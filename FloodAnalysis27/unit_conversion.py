'''
Created on Jan 18, 2017

@author: Greg Petrochenkov
'''
"""Contains conversion factors between different units.

Example:
pressure_in_atm = 1.023 pressure_in_dbar = ATM_TO_DBAR * pressure_in_atm

Also contains functions to convert dates to UTC seconds and milliseconds.
"""

import pytz
from datetime import timedelta
#from pandas import Timedelta

from numpy import timedelta64

METER_TO_FEET = 3.28084
METERS_PER_SECOND_TO_MILES_PER_HOUR = 2.236936292054

FILL_VALUE = -1e10

GRAVITY = 9.8  # (m / s**2)
GRAVITY_FEET = 32.1740 #(f / s**2)
SALT_WATER_DENSITY = 1027  # density of seawater (kg / m**3)
FRESH_WATER_DENSITY = 1000
BRACKISH_WATER_DENSITY = 1015

    
def adjust_to_gmt(datetime, tzinfo, dst):
    '''
    Method to adjust Python Datetimes from timezone to UTC
    
    Keyword arguments:
    datetimes: array of datetimes
    tzinfo: timezone to adjust from
    dst: whether or not the timezone is in daylight savings
    
    Returns:  adjusted datetimes
    '''
    
    if tzinfo == 'US/Eastern':
        delta = timedelta(seconds = 18000)
        datetime = datetime + delta
    elif tzinfo == "US/Central":
        delta = timedelta(seconds = 21600)
        datetime = datetime + delta
    elif tzinfo == "US/Mountain":
        delta = timedelta(seconds = 25200)
        datetime = datetime + delta
    elif tzinfo == "US/Pacific":
        delta = timedelta(seconds = 28800)
        datetime = datetime + delta
    elif tzinfo == "US/Aleutian" or tzinfo == "US/Hawaii":
        delta = timedelta(seconds = 36000)
        datetime = datetime + delta
        
    if dst:
        delta = timedelta(seconds=3600)
        datetime = datetime - delta
        
    return datetime
    
def adjust_from_gmt(datetimes, tzinfo, dst):
    '''
    Method to adjust Python Datetimes from UTC to the appropriate timezone
    
    Keyword arguments:
    datetimes: array of datetimes
    tzinfo: timezone to adjust to
    dst: whether or not the timezone is in daylight savings
    
    Returns:  adjusted datetimes
    '''
    
    if tzinfo == 'US/Eastern':
        delta = timedelta(seconds = 18000)
        datetimes = [x - delta for x in datetimes]
    elif tzinfo == "US/Central":
        delta = timedelta(seconds = 21600)
        datetimes = [x - delta for x in datetimes]
    elif tzinfo == "US/Mountain":
        delta = timedelta(seconds = 25200)
        datetimes = [x - delta for x in datetimes]
    elif tzinfo == "US/Pacific":
        delta = timedelta(seconds = 28800)
        datetimes = [x - delta for x in datetimes]
    elif tzinfo == "US/Aleutian" or tzinfo == "US/Hawaii":
        delta = timedelta(seconds = 36000)
        datetimes = [x - delta for x in datetimes]
        
    if dst == True:
        delta = timedelta(seconds=3600)
        datetimes = [x + delta for x in datetimes]
        
    return datetimes

def translate_tz(tz):
    '''
    Adjusting a Pandas Timestamp by the numberof hours in a timezone
    
    Keyword arguments:
    tz: string representing the timezone
    
    Returns:  Pandas Timedelta
    '''
    
    if tz == "EST":
     #   return Timedelta('5 hours')
        return timedelta64(5, 'h')
    if tz == "EDT":
 #       return Timedelta('4 hours')
        return timedelta64(4, 'h')  	  
    if tz == "CST":
#        return Timedelta('6 hours')
        return timedelta64(6, 'h')
    if tz == "CDT":
#        return Timedelta('5 hours')
        return timedelta64(5, 'h')
    if tz == "PST":
#       return Timedelta('8 hours')
        return timedelta64(8, 'h')
    if tz == "PDT":
#       return Timedelta('7 hours')
        return timedelta64(7, 'h')
#   return Timedelta('0 hours')
    return timedelta64(0, 'h')

def adjust_by_hours(datetimes, hours):
    '''
    Adjusts a datetime byt the specified number of hours
    
    Keyword arguments:
    datetimes: array of datetimes
    hours: hours to adjust

    Returns: array of adjusted datetimes
    '''
    
    delta = timedelta(hours=hours)
    datetimes = [x - delta for x in datetimes]
    time_zone = pytz.timezone("GMT") 
    datetimes = [time_zone.localize(x) for x in datetimes]
    return datetimes

def make_timezone_aware(datetime, tz, daylight_savings):
    '''
    Makes a datetime that is not timezone aware timezone aware
    
    Keyword arguments:
    datetime: Non-aware Datetime
    tz: timezone
    daylight_savings: whether the timezone is in daylight savings
    
    Returns: Timezone aware datetime
    '''
    
    time_zone = pytz.timezone(tz)
    datetime = time_zone.localize(datetime, is_dst=daylight_savings)
    
    if daylight_savings == True:
        delta = timedelta(hours=1)
        datetime = datetime - delta
   
    return datetime
    
