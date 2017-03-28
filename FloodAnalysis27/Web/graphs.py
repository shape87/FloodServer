'''
Created on Jan 18, 2017

@author: Greg Petrochenkov
'''

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.image as image
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
import unit_conversion as uc
from shapely.geometry import Polygon
from datetime import datetime

# UPLOAD_FOLDER = '/opt/django/webapps/pubs_ui/FloodAnalysis/FloodAnalysis27/Web/uploads'
# USGS_IMAGE = '/opt/django/webapps/pubs_ui/FloodAnalysis/FloodAnalysis27/Web/static/images/usgs.png'
UPLOAD_FOLDER = 'C:\\Users\\chogg\\Documents\\GitHub\\FloodAnalysis_v2\\FloodAnalysis27\\Web\\uploads'
USGS_IMAGE = 'C:\\Users\\chogg\\Documents\\GitHub\\FloodAnalysis_v2\\FloodAnalysis27\\Web\\static\\images\\usgs.png'

class GraphOutput:
    
    def __init__(self):
        self.grid_spec = None
        self.time_nums = None
        self.figure = None
        self.discrete_discharge = False
        self.alt_discharge = False
    
    def format_date(self, x, arb=None):
        '''
        Format dates so that they are padded away from the x-axis
        
        Keyword Arguments:
        x: pandas datenum value
        arb: unused but necessary keyword arg for matplotlib
        
        Returns: formatted date string
        
        '''
        date_str = mdates.num2date(x).strftime('%b-%d-%Y \n %H:%M')
        return ''.join([' ','\n',date_str])
    
    def null_date(self, x, arb=None):
        '''
        Format dates so that it is invisible
        
        Keyword Arguments:
        x: pandas datenum value
        arb: unused but necessary keyword arg for matplotlib
        
        Returns: blank string
        
        '''
        return ''
    
    def pad_left(self, z, arb=None):
        '''
        Format dates so that they are padded away from the z-axis
        
        Keyword Arguments:
        z: date string
        arb: unused but necessary keyword arg for matplotlib
        
        Returns: formatted date string
        
        '''
        return ''.join(['         ', '%d' % z])
    
    def create_header(self, flood_model, graph_type="normal"):
        '''
        Create the header and set up grid for USGS compliant graphs
        
        Keyword Arguments:
        flood_model: FlowCalculator object with data
        graph_type: Changes grid based on the type of graph
        
        '''   
        
        #matplotlib options for graph
        font = {'family' : 'Bitstream Vera Sans',
                'size'   : 14}
        matplotlib.rc('font', **font)
        plt.rcParams['figure.figsize'] = (16,10)
        plt.rcParams['figure.facecolor'] = 'white'
          
        #make the figure 
        self.figure = plt.figure(figsize=(16,10))
        
        #adjust dates to the appropriate timezone
        new_dates = uc.adjust_from_gmt([flood_model.time[0],flood_model.time[-1]], \
                                         flood_model.tz[0],flood_model.tz[1])
        
        # changes dates to matplotlib datenums
        first_date = mdates.date2num(new_dates[0])
        last_date = mdates.date2num(new_dates[1])
       
        #creates a linear space between first and last date for performance
        self.time_nums = np.linspace(first_date, last_date, len(flood_model.time))
        
        #Read images
        logo = image.imread(USGS_IMAGE, None)
    
        #change grid based on graph type
        if graph_type == "stack":
            self.grid_spec = gridspec.GridSpec(3, 2,
                               width_ratios=[1,2],
                               height_ratios=[1,4,4]
                               )
        else:
            self.grid_spec = gridspec.GridSpec(2, 2,
                               width_ratios=[1,2],
                               height_ratios=[1,7]
                               )
        #---------------------------------------Logo Section
        ax2 = self.figure.add_subplot(self.grid_spec[0,0])
        ax2.set_axis_off()
       
        ax2.axes.get_yaxis().set_visible(False)
        ax2.axes.get_xaxis().set_visible(False)
        
        ax2.imshow(logo)
    
    def plot_results(self, flood_model):
        '''
        Plots all result graphs
        
        Keyword Arguments:
        flood_model: FlowCalculator object containing all data
        '''
        
        self.create_header(flood_model, "stack")
        self.shared_axis_discharge(flood_model)
        
        self.create_header(flood_model)
        self.twin_axis_discharge(flood_model)
        
        
    def pad_space(self, ax, min_max):
        '''
        Changes limits of x and y axis so that the data is more aesthetically pleasing
        
        Keyword Arguments:
        ax: axis of matplotlib figure
        min_max: minimum and maximum of data to be plotted
        '''
        
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        new_x, new_y = [], []
        
        #if axis limit equals minimum x
        if x_lims[0] == min_max["min_x"]:
            new_x.append(x_lims[0] - 50)
        else:
            new_x.append(x_lims[0])
           
        #if axis limit equals maximum x
        if x_lims[1] == min_max["max_x"]:
            new_x.append(x_lims[1] + 50)
        else:
            new_x.append(x_lims[1])
            
        #if axis limit equals minimum y
        if y_lims[0] == min_max["min_y"]:
            new_y.append(y_lims[0] - 10)
        else:
            new_y.append(y_lims[0])
           
        #if axis limit equals maximum y
        if y_lims[1] == min_max["max_y"]:
            new_y.append(y_lims[1] + 10)
        else:
            new_y.append(y_lims[1])
            
        #set new or unchanged limits
        ax.set_xlim(new_x)
        ax.set_ylim(new_y)
            
        
    def stage_graph(self, flood_model, min_max, pgon):
        '''
        Plots the maximum stage for a given cross section geometry
        
        Keyword Arguments:
        flood_model: FlowCalculator object containing the data
        min_max: minimum and maximum bounds of polygon
        pgon: polygon of max stage boundaries
        '''
        
        
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot('111')
        ax.set_title("Cross Sectional Geometry at Max Possible Stage")
        plt.xlabel("Feet to the right of reference point")
        plt.ylabel("Feet above datum")
        
        #intersect with polygon in order to get a flat top width
        inter = Polygon([
                         (min_max["min_x"],min_max["min_y"]),
                         (min_max["max_x"],min_max["min_y"]),
                         (min_max["max_x"],flood_model.coord_min_max_y),
                         (min_max["min_x"],flood_model.coord_min_max_y)
                         ])
        intersection = pgon.intersection(inter)
        
        #get path and add the patch of the appropriate color
        path = Path(intersection.exterior.coords)
        patch = patches.PathPatch(path, facecolor="orange", lw=2, alpha=.3)
        ax.add_patch(patch)
        
        #plot the individual coordinates
        plt.plot([x[0] for x in pgon.exterior.coords], 
                 [x[1] for x in pgon.exterior.coords], '-o')
        
        self.pad_space(ax, min_max)
        
        #save the filename to flood_model and then save the figure
        flood_model.cross_section_graph = os.path.join(UPLOAD_FOLDER, "cross.png")
        plt.savefig(flood_model.cross_section_graph)

    def sub_divided_stage_graph(self, flood_model, min_max, pgon, sub_pgons):
        '''
        Plots the maximum stage for a given subdivided cross section geometry
        
        Keyword Arguments:
        flood_model: FlowCalculator object containing the data
        min_max: minimum and maximum bounds of polygon
        pgon: polygon of max stage boundaries,
        sub_pgons: list of individual sub divided polygons
        '''
        
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot('111')
        ax.set_title("Cross Sectional Geometry at Max Stage")
        plt.xlabel("Feet to the right of reference point")
        plt.ylabel("Feet above datum")
        
        #intersect with polygon in order to get a flat top width
        inter = Polygon([
                         (min_max["min_x"],min_max["min_y"]),
                         (min_max["max_x"],min_max["min_y"]),
                         (min_max["max_x"],flood_model.coord_min_max_y),
                         (min_max["min_x"],flood_model.coord_min_max_y)
                         ])
        
        
        colors = ['red','green','orange','blue','purple']
        
        #for each subdivision add a patch of the appropriate color
        for x in range(0,len(sub_pgons)):
            intersection = sub_pgons[x].intersection(inter)
            
            path = Path(intersection.exterior.coords)
            patch = patches.PathPatch(path, facecolor=colors[x % 5], 
                                      lw=2, alpha=.3)
            ax.add_patch(patch)
            
        #plot the individual coordiantes of the entire geometry
        plt.plot([x[0] for x in pgon.exterior.coords], 
                 [x[1] for x in pgon.exterior.coords], '-o')
        
        self.pad_space(ax, min_max)
        
        #save the filename to the flood_model object and save the figure
        flood_model.cross_section_graph = os.path.join(UPLOAD_FOLDER, "cross.png")
        plt.savefig(flood_model.cross_section_graph)
     
    def shared_axis_discharge(self, flood_model):
        '''
        Plots the stagecomputed newton raphson discharge along with optional
        discrete field measurement discharge and approximated discharge on
        separate axes
        
        Keyword Arguments:
        flood_model: FlowCalculator object containing the data
        '''
        
        #arrays for the legend
        plots, names = [], []
        
        ax = self.figure.add_subplot(self.grid_spec[1,0:])
        ax2 = self.figure.add_subplot(self.grid_spec[2,0:], sharex=ax)
        
        #plot the stage on the first axis
        stage, = ax.plot(flood_model.time, flood_model.stage, color="green", alpha=.75)
        plots.append(stage)
        names.append("Stage")
        ax.set_ylabel("Stage in Feet")
        
        #plot the computed Q on the second axis
        computed_q, = ax2.plot(flood_model.time, flood_model.computed_Q, color="blue", alpha=.75)
        plots.append(computed_q)
        names.append("Computed Discharge")
        
        if self.alt_discharge == True:
            #plot the approximated Q on the second axis
            alt_q, = ax2.plot(flood_model.time, flood_model.alt_discharge, color="red", alpha=.75)
            plots.append(alt_q)
            names.append("Alternative Discharge")
            
        if self.discrete_discharge == True:
            #plot the discrete field measurement Q on the second axis
            disc_q, = ax2.plot(flood_model.discrete_df["Time"].values, 
                              flood_model.discrete_df["Q"].values, 'o', color="black", alpha=.75)
            plots.append(disc_q)
            names.append("Discrete Sampled Discharge")
        
        ax2.set_ylabel("Discharge in ft^3/s")
        ax2.set_xlabel("Timezone in UTC")
        
        #x axis formatter for dates (function format_date() below)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_date))
      
        ax.grid(b=True, which='major', color='grey', linestyle="-")
        ax2.grid(b=True, which='major', color='grey', linestyle="-")
        
        #options for legend and legend placement
        legend = ax.legend(plots,
                           names, 
                  bbox_to_anchor=(.95, 1.485), loc=1, borderaxespad=0.0, prop={'size':10.3},frameon=False,numpoints=1, \
                  title="EXPLANATION")
        legend.get_title().set_position((-56, 0))
        ax.set_title("Stage, Discrete Sampled and Computed Discharge over Time")
        title_pos = ax.title.get_position()
        new_pos = (title_pos[0], title_pos[1] + .03) 
        ax.title.set_position(new_pos)
        
        #hide x axis tick labels for first axis
        plt.setp( ax.get_xticklabels(), visible=False)
        
        #save filename to flood_model object and save the figure
        flood_model.result_graph1 = os.path.join(UPLOAD_FOLDER, "result1.png")
        plt.savefig(flood_model.result_graph1)
        
    def twin_axis_discharge(self, flood_model):
        '''
        Plots the stage, computed newton raphson discharge along with optional
        discrete field measurement discharge and approximated discharge
        on the same axis
        
        Keyword Arguments:
        flood_model: FlowCalculator object containing the data
        '''
        
        #arrays for legend
        plots, names = [], []
        
        ax = self.figure.add_subplot(self.grid_spec[1,0:])
        ax3 = ax.twinx()
        
        #plot the stage on the twin axis
        stage, = ax3.plot(flood_model.time, flood_model.stage, color="green", alpha=.75)
        plots.append(stage)
        names.append("Stage")
        ax.set_ylabel("Discharge in ft^3/s")
        
        #plot the computed Q
        computed_q, = ax.plot(flood_model.time, flood_model.computed_Q, color="blue", alpha=.75)
        plots.append(computed_q)
        names.append("Computed Discharge")
        
        if self.alt_discharge == True:
            #plot the approximate Q
            alt_q, = ax.plot(flood_model.time, flood_model.alt_discharge, color="red", alpha=.75)
            plots.append(alt_q)
            names.append("Alternative Discharge")
            
        if self.discrete_discharge == True:
            #plot the discrete field measurement Q
            alt_q, = ax.plot(flood_model.discrete_df["Time"].values, 
                              flood_model.discrete_df["Q"].values, 'o', color="black", alpha=.75)
            plots.append(alt_q)
            names.append("Discrete Sampled Discharge")
        
        ax3.set_ylabel("Stage in Feet")
        ax.set_xlabel("Timezone in UTC")
        
        ax.grid(b=True, which='major', color='grey', linestyle="-")
        
        #x axis formatter for dates (function format_date() below)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_date))
        
        #options for legend and legend placement
        legend = ax.legend(plots,
                           names, 
                  bbox_to_anchor=(.95, 1.265), loc=1, borderaxespad=0.0, prop={'size':10.3},frameon=False,numpoints=1, \
                  title="EXPLANATION")
        legend.get_title().set_position((-56, 0))
        
        ax.set_title("Stage, Discrete Sampled and Computed Discharge over Time")
        title_pos = ax.title.get_position()
        new_pos = (title_pos[0], title_pos[1] + .03) 
        ax.title.set_position(new_pos)
        
        #save filename to flood_model object and save the figure
        flood_model.result_graph2 = os.path.join(UPLOAD_FOLDER, "result2.png")
        plt.savefig(flood_model.result_graph2)
        
#     def contour_stage_discharge(self, flood_model):
#     
#         # the label
#         ax = self.figure.add_subplot(self.grid_spec[1,0:], projection='3d')
#         
#         computed, = ax.plot(self.time_nums, flood_model.stage, flood_model.computed_Q, color='blue')
#         ax.set_title("Discrete Sampled Discharge vs. Computed")
#         ax.set_xlabel("Timezone UTC", labelpad=48)
#         ax.set_ylabel("Stage in Feet", labelpad=20)
#         ax.set_zlabel("Discharge in Feet^3/Second", labelpad=28)
#        
#         
#         ax.xaxis.set_major_formatter(ticker.FuncFormatter(self.format_date))
#         ax.zaxis.set_major_formatter(ticker.FuncFormatter(self.pad_left))
#        
#         sampled, = ax.plot(self.time_nums, flood_model.stage, flood_model.discrete_discharge, color='red', alpha=.5)
#         
#         legend = ax.legend([sampled, computed],
#                            ["Discrete Sampled Discharge","Computed Discharge"], \
#                   bbox_to_anchor=(.95, 1.255), loc=1, borderaxespad=0.0, prop={'size':10.3},frameon=False,numpoints=1, \
#                   title="EXPLANATION")
#         legend.get_title().set_position((-56, 0))
#         
#         ax.set_title("Stage, Discrete Sampled and Computed Discharge over Time")
#         title_pos = ax.title.get_position()
#         new_pos = (title_pos[0], title_pos[1] + .135) 
#         ax.title.set_position(new_pos)
#         
#         ax.set_xticks(np.linspace(self.time_nums[0], self.time_nums[-1], 5))
#         
# #         print(ax.zticks.get_position())
#         
#         flood_model.result_graph3 = "uploads/result3.png"
#         
#         plt.savefig(flood_model.result_graph3)
    
if __name__ == "__main__":
    import pandas as pd
    from Web.flow_calc import FlowCalculator
    g = GraphOutput()
    g.discrete_discharge = True
    g.alt_discharge = True
    
    f = FlowCalculator()
    
    df = pd.read_csv("./data/flow_table.csv")
    f.time = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in df["Time"].values]
    f.computed_Q = df["Flow"].values
    f.stage = df["Stage"].values
    f.alt_discharge = np.array(f.computed_Q) - 10000
    f.discrete_df = pd.DataFrame({"Time": pd.Series(f.time[::30]), "Q": pd.Series(f.alt_discharge[::30])})
    f.tz = ("UTC", False)
    
    g.plot_results(f)
    
    
