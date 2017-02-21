'''
Created on Jan 18, 2017

@author: Greg Petrochenkov
'''
import numpy as np
import pandas as pd
from Web.nwis_request import get_ts_data, get_discrete_data
from Web.cartesian import create_output
from Web.graphs import GraphOutput

class FlowCalculator(object):
    
    def __init__(self):
        self.time = None
        self.tz = None
        self.stage = None
        self.alt_discharge = None
        self.discrete_df = None
        self.time_delta = None
        self.stage_increment = None
        self.datum = None
        self.manning_rough = None
        self.sub_divisions = None
        self.channel_bed_slope = None
        self.stage_hB = None
        self.stage_hp = None
        self.rise_peak_delta = None
        self.flow_QB = None
        self.flow_Qp = None
        self.flow_Q0 = None
        self.coord_file = None
        self.coord_df = None
        self.coord_min_max_y = None
        self.properties_file = None
        self.properties_df = None
        self.auto = False
        self.cross_section_graph = None
        self.slope_ratio = None
        self.g = 32.2 #ft/s^2
        self.computed_Q = []
        self.flow_df = None
        self.static_manning = None
        self.channel_properties_file = None
        self.channel_properties_df = None
        self.manning_df = None
        self.result_graph1 = None
        self.result_graph2 = None
        self.result_graph3 = None
        self.SSR = None
        self.graph_output = GraphOutput()
        
    def get_nwis_ts(self, site_id, start_date, end_date, tz, ds):
        '''
        Method for getting time series of stage, approximate Q, and discrete measurement Q
        
        Keyword arguments:
        site_id: id of the site to be queried
        start_date: date for which ts data will be greater than or equal to
        end_date: date for which ts data will be less than or equal to
        tz: timezone of start_date and end_date
        ds: whether timezone is in daylight savings (True or False)
        '''
        
        #get stage data and alternative discharge
        nwis_data = get_ts_data(site_id, start_date, end_date, tz, ds)
       
        #assign data to appropriate properties
        self.time = nwis_data['time']
        self.time_delta =  (self.time[1] - self.time[0]).seconds
        self.tz = (tz, ds)
        self.stage = nwis_data['stage']
        self.alt_discharge = nwis_data['alt_discharge']
        
        #get discrete sampled field measurement ts data
        self.discrete_df = get_discrete_data(site_id)
        self.discrete_df = self.discrete_df[self.discrete_df["Time"] >= np.datetime64(start_date.replace('/','-'))]
        self.discrete_df = self.discrete_df[self.discrete_df["Time"] <= np.datetime64(end_date.replace('/','-'))]
        
    def create_table(self):
        '''
        Method for reading in or creating Hydraulic Properties table
        '''
        
        #get cross-section geometry file and sort by X value
        self.coord_df = pd.read_csv(self.coord_file)
        self.coord_df.columns = [["X", "Y"]]
        self.coord_df = self.coord_df.sort(["X"])
        self.coord_min_max_y = np.min([self.coord_df['Y'].values[0],self.coord_df['Y'].values[-1]])
        
        #read in table if "false", otherwise create table
        #either way create graph of max stage
        if self.auto == "false":
            self.properties_df = pd.read_csv(self.properties_file)
            self.properties_df.columns = [["S","A","P","T","R"]]
            self.properties_df.index = self.properties_df["S"]
            self.properties_df.index.name = "Stage"
            self.properties_df = self.properties_df[["A","P","T","R"]]
            self.properties_df.rename(columns={
                                          "A": "Cross-sectional Area",
                                          "P": "Wetted Perimeter",
                                          "T": "Top Width",
                                          "R": "Hydraulic Radius"
                                          }, inplace=True)
            create_output(self)
            
        else:
            self.properties_df = create_output(self)
            
            
    def compute_slope_ratio(self, area_pair):
        '''
        Method for computing slope ratio
        
        Keyword arguments:
        area_pair: Area of cross-section for the stage at start of flood rise and flood peak
        '''
        
        #start of equation
        self.slope_ratio = (( 56200. * ( self.flow_Qp + self.flow_QB )) / (( self.stage_hp - self.stage_hB ) * ((area_pair[0] + area_pair[1]) / 2.))) * ( self.rise_peak_delta * self.channel_bed_slope )
        #end of equation
        
    def generate_first_approximation(self, j):
        '''
        Method for generating the first approximation for
        the Newton iterations
        
        Keyword arguments:
        j: index of time step
        
        Returns:
        Last computed Q if 1, otherwise equation suggested in 
        Fread paper (1975)
        
        '''
        if j == 1:
            val = self.Q(j-1)
            return val
        else:
            #start of equation
            val =  self.Q(j-1) + ( self.Q(j-1) - self.Q(j-2) )  / 2.
            #end of equation
            return val
        
    def h(self, index):
        '''
        Method for getting the stage of a particular time from 
        the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve h
        
        Returns: h at given timestep
        '''
        
        return self.time_series_df['h'].values[index]
    
    def A(self, index):
        '''
        Method for getting the cross-sectional area
         of a particular time from the time series data frame
         
        Keyword Arguments:
        index: timestep at which to retrieve A
        
        Returns: A at given timestep
        '''
        
        return self.time_series_df['A'].values[index]
    
    def P(self, index):
        '''
        Method for getting the wetted perimeter of a particular
        time from the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve P
        
        Returns: P at given timestep
        '''
        
        return self.time_series_df['P'].values[index]
    
    def T(self, index):
        '''
        Method for getting the top width of a particular
        time from the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve T
        
        Returns: T at given timestep
        '''
        
        return self.time_series_df['T'].values[index]
    
    def R(self, index):
        '''
        Method for getting the hydraulic radius of a particular
        time from the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve R
        
        Returns: R at given timestep
        '''
        
        return self.time_series_df['R'].values[index]
    
    def delta_h(self, index):
        '''
        Method for getting the rate of change in the stage(delta h) 
        of a particular time from the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve delta_h
        
        Returns: delta_h at given timestep
        '''
        
        return self.time_series_df['delta_h'].values[index]
    
    def K(self, index):
        '''
        Method for getting Fread's K (See Fread 1975 AWRA Paper)
        of a particular time from the time series data frame
        
        Keyword Arguments:
        index: timestep at which to retrieve K
        
        Returns: K at given timestep
        '''
        
        return self.time_series_df['K'].values[index]
    
    def Q(self, index):
        '''
        Method for getting flow
        of a particular time from the computed flow array
        
        Keyword Arguments:
        index: timestep at which to retrieve Q
        
        Returns: Q at given timestep
        '''
        
        return self.computed_Q[index]
    
    def manning(self, stage):
        '''
        Method for getting manning's roughness
        of a particular stage
        
        Keyword Arguments:
        stage: gauge height at which to retrieve n
        
        Returns: n at given stage
        '''
        
        if self.static_manning == "true":
            return self.manning_rough
        else:
            index = int(self.closest_to_zero(self.manning_df['Stage'].values, stage))
            return self.manning_df["n"].values[index]
    
    def L0(self, Qi, j):
        '''
        L0 differential equation per Fread (1975)
        
        Keyword Arguments:
        Qi: Initial flow approximation
        j: index of timestep
        
        Returns: L0 differential equation
        '''
        
        #start of equation
        val =  self.L3(j) + ( self.L4(j) / Qi ) + ( self.L5(j) * Qi ) + ( self.L6(j) * Qi**2. )              
        #end of equation
        return val
    
    def L1(self, Qi, j):
        '''
        L1 differential equation per Fread (1975)
        
        Keyword Arguments:
        Qi: Initial flow approximation
        j: index of timestep
        
        Returns: L1 differential equation
        '''
        
        #start of equation
        val =  -1. * ( self.L4(j) / Qi**2. ) + self.L5(j) + (2. * self.L6(j) * Qi )
        #end of equation
        return val
    
    def L2(self, j):
        '''
        L2 differential equation per Fread (1975)
        
        Keyword Arguments:
        j: index of timestep
        
        Returns: L2 differential equation
        '''
        
        #start of equation
        val =  1.486 * ( ( self.A(j) * self.R(j)**( 2./3. ) ) / self.manning(self.h(j)) )
        #end of equation
        return val
    
    def L3(self, j):
        '''
        L3 differential equation per Fread (1975)
        
        Keyword Arguments:
        j: index of timestep
        
        Returns: L3 differential equation
        '''
        
        #start of equation
        val = self.channel_bed_slope + ( (2. * self.channel_bed_slope) / ( 3. * self.slope_ratio**2.) ) + ( self.Q(j-1) / ( self.g * self.A(j-1) * self.time_delta))
        #end equation
        return val
    
    def L4(self, j):
        '''
        L4 differential equation per Fread (1975)
        
        Keyword Arguments:
        j: index of timestep
        
        Returns: L4 differential equation
        '''
        
        #start of equation
        val = np.nan_to_num(self.A(j) * self.delta_h(j) / self.K(j))
        #end of equation
        return val
    
    def L5(self, j):
        '''
        L5 differential equation per Fread (1975)
        
        Keyword Arguments:
        j: index of timestep
        
        Returns: L5 differential equation
        '''
        
        #start of equation
        val = ( 1. - np.nan_to_num(( 1. / self.K(j) ))) * ( self.T(j) * self.delta_h(j) /  ( self.g * self.A(j)**2. ) ) - ( 1. / ( self.g * self.A(j) * self.time_delta) )
        #end of equation
        return val
    
    def L6(self, j):
        '''
        L6 differential equation per Fread (1975)
        
        Keyword Arguments:
        j: index of timestep
        
        Returns: L6 differential equation
        '''
        
        #start of equation
        val = (-1.) * ( 2. * self.channel_bed_slope * self.T(j) ) / (3. * self.slope_ratio**2. * self.g * self.A(j)**3.)
        #end of equation
        return val
    
    def f_last_approximation(self, Q0, j, Qi):
        '''
        f(Qi) equation per Fread (1975)
        
        Keyword Arguments:
        Q0: initial approximation of flow
        j: index of timestep
        Qi: last approximation of flow
        
        Returns: f(Qi)
        '''
        
        #start of equation
        val = Qi - self.L2(j) * self.L0(Q0, j)**(1./2.)
        #end of equation
        return val
    
    def f_last_approximation_derivative(self, Q0, j):
        '''
        f'(Qi) equation per Fread (1975)
        
        Keyword Arguments:
        Q0: initial approximation of flow
        j: index of timestep
        
        Returns: f'(Qi)
        '''
        
        #start of equation
        val = 1. - (0.5 * self.L2(j) * self.L1(Q0, j))/ self.L0(Q0, j)**(1./2.)
        #end of equation
        return val
    
    def closest_to_zero(self, index_list, value):
        '''
        Finds the closest value in a list to that of a particular value
        and returns its index
        
        Keyword Arguments:
        index_list: list of values to compare against value
        value: parameter for use in the comparison
        
        Returns: index of closest match
        '''
        
        return np.array(np.abs(index_list - value)).argmin()
    
    def initialize_timeseries_data_for_newton_method(self):
        '''
        Method to gather all variables needed for the Newton iterations calculating flow
        '''
        
        #start with stage values for each time
        self.time_series_df = pd.DataFrame({"h": pd.Series(self.stage, index=self.time)})
        
        #get indices in the hydraulic properties table associated with each stage in time
        indices = [int(self.closest_to_zero(self.properties_df.index.values, x)) for x in self.stage]
        area_indices = [int(self.closest_to_zero(self.properties_df.index.values, x))  for x in \
                    [self.stage_hp, self.stage_hB]]
        
        #prefix for use depending on whether the cross-section was subdivided
        prefix = ''
        if self.properties_df.shape[1] > 4:
            prefix = 'Total '
            
        #Get the area
        self.time_series_df['A'] = [self.properties_df['%sCross-sectional Area' % prefix].values[x] for x in indices]
        
        #get area pair and compute slope ratio
        area_pair = [self.properties_df['%sCross-sectional Area' % prefix].values[x] for x in area_indices]
        self.compute_slope_ratio(area_pair)
        
        #wetted perimeter
        self.time_series_df['P'] = [self.properties_df['%sWetted Perimeter' % prefix].values[x] for x in indices]
        
        #top width
        self.time_series_df['T'] = [self.properties_df['%sTop Width' % prefix].values[x] for x in indices]
        
        #hydraulic radius
        self.time_series_df['R'] = [self.properties_df['%sHydraulic Radius' % prefix].values[x] for x in indices]
        
        #change in stage
        self.time_series_df["delta_h"] =  np.concatenate([[np.nan],
        [ 
        #start of equation                
        ( self.h(x) - self.h(y) ) / self.time_delta                                   
        #end of equation
        for x,y in zip(range(1,self.time_series_df.shape[0]), 
                                                range(0,self.time_series_df.shape[0]-1))]])
        
        #K per Fread (1975)
        self.time_series_df["K"] = np.concatenate([[np.nan], 
        [
        #start of equation
        (5./3.) - ( 2. * self.A(x) / ( 3. * self.P(x) * self.T(x) ) ) * (( self.P(x) - self.P(y) ) / ( self.h(x) - self.h(y) ) )                 \
        #end of equation
        for x,y in zip(range(1,self.time_series_df.shape[0]), 
                                                  range(0,self.time_series_df.shape[0]-1))]])
        
        #assign default value to special cases where K is negative or NaN
        self.time_series_df["K"][self.time_series_df["K"] <= 0] = 5./3.
        self.time_series_df["K"][np.isnan(self.time_series_df["K"])] = 5./3.
        
        
    def flow_newton_raphson_method(self, max_iteration=1000):
        '''
        Method to compute Q via the Newton Raphson numerical method
        
        Keyword arguments:
        max_iteration: maximum times the process is allowed to iterate over one timestep
        '''
        
        #initialize computed flow array and
        #add the first flow for use as approximation for next time step
        self.computed_Q = []
        self.computed_Q.append(self.flow_Q0)
        
        #for each time step
        for x in range(1, len(self.time)):
            
            #get first approximation
            init_approx = approx_Q = self.generate_first_approximation(x)
            iteration = 0
            
            #for each iteration until the criteria is met
            for y in range(0, max_iteration):
                
                new_approx_Q = approx_Q - ( self.f_last_approximation(init_approx, x, approx_Q) / self.f_last_approximation_derivative(init_approx, x) )
                
                #end case
                if np.abs(new_approx_Q - approx_Q) <= 1:
                    self.computed_Q.append(new_approx_Q)
                    break
                else:
                    approx_Q = new_approx_Q
                    iteration += 1
            
        #assign flow df 
        self.flow_df = pd.DataFrame({"Stage": self.time_series_df['h'],
                                    "Flow": pd.Series(self.computed_Q, index=self.time)})
        self.flow_df.index.name = "Time"
        
    def process_results(self):
        '''
        Method to graph output after the Newton Raphson process is complete
        '''
        
        self.graph_output.plot_results(self)
        
        #get the appropriate indices for comparison
        #then get the Sum of the Squared Residuals
        compute_discharge_idx = self.get_date_index()
        diff = [(x - self.computed_Q[y])**2 for x, y in zip(self.discrete_df["Q"], compute_discharge_idx)]
        self.SSR = np.sum(diff)
        
    def get_date_index(self):
        '''
        Method to get the indices at which the discrete time is closest to the continous time
        '''
        
        np_datetimes = np.array(self.time, dtype=np.datetime64)       
        return [np.array(np.abs(np_datetimes - x)).argmin() for x in self.discrete_df["Time"].values]
        
        
    
