'''
Created on Jan 18, 2017

@author: Greg Petrochenkov
'''


import requests
import defusedxml.ElementTree as ET
from datetime import datetime
import unit_conversion
import re
from StringIO import StringIO
import pandas as pd
import unit_conversion as uc

def appendHTMLPrefix(string, prefix_type=''):
    '''
    Formats prefix in order to crawl through WaterML 2.0
    
    Keyword Arguments:
    string: property to lookup
    prefix_type: appropriate prefix to join with
    
    Returns: joined string prefix and property
    '''
    
    if prefix_type == 'gml':
        return ''.join(['{http://www.opengis.net/gml/3.2}', string])
    elif prefix_type == 'om':
        return ''.join(['{http://www.opengis.net/om/2.0}',string])
    else:
        return ''.join(['{http://www.opengis.net/waterml/2.0}',string])
    
def format_time(dates):
    '''
    Formats datestrings in to Python Datetimes
    
    Keyword Arguments:
    dates: list of datestrings
    
    Returns: List of Datetimes
    '''
    
    dash_index = dates[0].rfind('+')

    if dash_index == -1:
        dash_index = dates[0].rfind('-')
    
    dates = [datetime.strptime(x[0:dash_index], '%Y-%m-%dT%H:%M:%S') \
             for x in dates]

    return dates

def get_data_type(attrib, sites):
    '''
    Gets the parameter code associated with the data type
    
    Keyword Arguments:
    attrib: string encompassing the parameter code
    sites: site id of site
    
    Returns: sliced string with parameter code
    '''
    
    site_len = len(sites)
    index = attrib.find(sites)
    first = int(index + site_len+1)
    last = int(index + site_len+6)
    return attrib[first:last]
          
def get_ts_data(sites,start_date = None, end_date = None, tz=None, ds=None):
    '''
    Gets the time series of gauge height and alternative approximated discharge measurements
    and other ancillary data
    
    Keyword Arguments:
    sites: site id to be queried
    start_date: all data queried will be greater than or equal to this date
    end_date: all data queried will be less than or equal to this date
    tz: timezone of start_date and end_date
    ds: whether or not timezone is in daylight savings (True or False)
    
    Returns: dictionary of time, guage height, approx discharge, lat, lon, and name
    '''
    
    #convert start date to Python Datetime and adjust based on the timezone
    dt1 = datetime.strptime(start_date,'%Y/%m/%d %H:%M')
    dt1 = unit_conversion.make_timezone_aware(dt1, tz, ds)
    dt1 = unit_conversion.adjust_from_gmt([dt1], tz, ds)[0]
    
    #convert end date to Python Datetime and adjust based on the timezone
    dt2 = datetime.strptime(end_date,'%Y/%m/%d %H:%M')
    dt2 = unit_conversion.make_timezone_aware(dt2,tz,ds)
    dt2 = unit_conversion.adjust_from_gmt([dt2], tz, ds)[0]
        
    params = { 'sites': sites,
     'format': 'waterml,2.0',
    'startDT': dt1.isoformat('T'),
    'endDT': dt2.isoformat('T'),
     'parameterCd': '00060,00065'
    }

    #Query NWIS
    r = requests.get('http://waterservices.usgs.gov/nwis/iv/', params=params)
   
    time, gauge_height, alt_discharge =[], [], []
    lat, lon, name, data_type = None, None, None, None
    
    #if the query was successful
    if r.status_code not in [503, 504]:
        root = ET.fromstring(r.text)
        
        #get the name property
        name_search = ''.join(['.//',appendHTMLPrefix('name', prefix_type='gml')])
        for child in root.findall(name_search):
            name = child.text
    
        search = ''.join(['.//',appendHTMLPrefix('observationMember')])
        for child in root.findall(search):
            
            #get the appropriate parameter code
            search2 = ''.join(['.//',appendHTMLPrefix('OM_Observation', prefix_type='om')])
            for y in child.findall(search2):
                data_type = get_data_type(y.attrib[appendHTMLPrefix('id', prefix_type='gml')], sites)
            
            #get the latitude
            if lat is None:
                c = ''.join(['.//',appendHTMLPrefix('pos', prefix_type='gml')])
                for x in child.findall(c):
                    lat_lon = x.text.split(' ')
                    lat = lat_lon[0]
                    lon = lat_lon[1]
            
            #get the datetime
            if len(time) == 0:
                a = ''.join(['.//',appendHTMLPrefix('time')])
                for x in child.findall(a):
                    time.append(x.text)
               
            #get the value associated with parameter code 
            b = ''.join(['.//',appendHTMLPrefix('value')])
            for x in child.findall(b):
                
                #gauge height
                if data_type == '00060':
                    alt_discharge.append(float(x.text))
                    
                #approximate discharge
                if data_type == '00065':
                    gauge_height.append(float(x.text))
        
        time = format_time(time)
        
        return {"time": time, "stage": gauge_height, 
                "alt_discharge": alt_discharge,
                "lat": lat, "lon": lon, "name": name}
        
        
def get_discrete_data(sites):
    '''
    Gets the time series of discrete discharge field measurements
    
    Keyword Arguments:
    sites: site id to be queried
    
    Returns: Panda Dataframe of Time, Timezone, and Discharge
    '''
    
    params = { 'site_no': sites,
     'agency_cd': 'USGS',
     'format': 'rdb_expanded'
     }

    #query NWIS
    r = requests.get('https://waterdata.usgs.gov/nwis/measurements/', params=params)
   
    #Get first entry of data
    match = re.search('\nUSGS\t', r.text)
    match.span()[0]
    
    #save string to string buffer
    string_io = StringIO(r.text[match.span()[0]:])
    string_io.seek(0)
    string_io.next()
        
    #read in table and adjust timezone to UTC
    discrete_df = pd.read_table(string_io, header=None, engine='c', sep='\t')
    discrete_df[3] = pd.to_datetime(discrete_df[3])
    discrete_df[3] =  [discrete_df[3].values[x] - uc.translate_tz(y) 
                       for x,y in zip(range(0,len(discrete_df[3].values)),discrete_df[4].values)]
    
    discrete_df = discrete_df[[3,4,9]]
    discrete_df.columns = [["Time", "Tz", "Q"]]
    
    return discrete_df
    
        
if __name__ == "__main__":
    site = '07010000'
    start_date = '2016-11-29 00:00'
    end_date = '2016-12-07 00:00'
    timezone = "US/Central"
    ds = False
    
    data = get_ts_data(site, start_date, end_date, timezone, ds)
