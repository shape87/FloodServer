'''
Created on Dec 21, 2016

@author: chogg
'''
#from shapely import speedups
from shapely.geometry import Polygon, LineString
import numpy as np
import pandas as pd

def create_output(flood_model):
    '''
    Creates a graph and also creates a hydraulic properties table if auto is selected
    
    Keyword arguments:
    flood_model: the FlowCalculator object necessary to compute hydraulic properties table
    
    '''
    
    #shapely optimization
 #   speedups.enable()
    
    points = [(x,y) for x, y in zip(flood_model.coord_df['X'],
                                    flood_model.coord_df['Y'])]
    
    total_pgon = Polygon(points)
    
    #get min and max of axes and name such for readability
    min_x, max_x = total_pgon.bounds[0], \
                    total_pgon.bounds[2]
    min_y, max_y = total_pgon.bounds[1], \
                    total_pgon.bounds[3]
    min_max = {"min_x": min_x, "min_y": min_y,
               "max_x": max_x, "max_y": max_y}
      
    #create range of stage for hydraulic properties table if auto is true
    if flood_model.auto == "true":         
        stage = np.concatenate(
                               [np.arange(min_y, flood_model.coord_min_max_y, 
                                          float(flood_model.stage_increment))[1:],
                                [flood_model.coord_min_max_y]])
              
    #If there are sub divisions, break area in to sub divisions      
    if len(flood_model.sub_divisions) > 0:
        sub_pgons = []
        start_index = min_x
        for x in np.concatenate([sorted(flood_model.sub_divisions),[max_x]]):
            end_index = x
            inter = Polygon([(start_index,min_y),(end_index,min_y),
                             (end_index,max_y),(start_index,max_y)])
            sub_pgons.append(total_pgon.intersection(inter))
            start_index = x
          
        #create the subdivided stage graph
        flood_model.graph_output.sub_divided_stage_graph(flood_model, min_max, total_pgon, sub_pgons)
        
        #if auto is true create hydraulic properties table
        if flood_model.auto == "true":
            data = stage_intermediate(sub_pgons, stage, min_max)
            data.index = data.index.values - flood_model.datum
            data.index.name = "Stage" 
            return data
        
    else:
        #create stage graph
        flood_model.graph_output.stage_graph(flood_model, min_max, total_pgon)
        
        #if auto is true create hydraulic properties table
        if flood_model.auto == "true":
            data = stage_intermediate(total_pgon, stage, min_max)
            data.index = data.index.values - flood_model.datum
            data.index.name = "Stage"
            return data

def stage_intermediate(pgon, stage, bounds):
    '''
    Mediates creation of hyrdaulic property dataframes
    
    Keyword arguments:
    pgon: either a single polygon or group of polygons if subdivided
    stage: the list of incremental stage
    bounds: the x-y bounds of the total polygon (whether subdivided or not)
    
    Returns: Pandas Dataframe of Hydraulic Properties
    '''
    
    #if the polygon was subdivided, process a data frame for each subdivision
    if type(pgon) is not Polygon:
        master_data = None
        for x in range(1,len(pgon)+1):
            
            if x == 1:
                df = stage_table(pgon[x-1], stage, bounds, "%d" % x, (False,True))
            elif x == len(pgon):    
                df = stage_table(pgon[x-1], stage, bounds, "%d" % x, (True,False))
            else:
                df = stage_table(pgon[x-1], stage, bounds, "%d" % x, (True,True))
                
                
            if master_data is None:
                master_data = df
            else:
                master_data = pd.concat([master_data, df], axis=1)
                
        get_total(master_data, len(pgon))
        return master_data
    else:
        return stage_table(pgon, stage, bounds, "")         

def stage_table(pgon, stage, bounds, name, left_right=(False,False)):
    '''
    Computes the hydraulic properties of the table
    
    Keyword arguments:
    pgon: polygon representing max stage to be intersected with incremental stage
    stage: the list of incremental stage
    bounds: the x-y bounds of the polygon (passed in for more terse code)
    name: name to give the column of the returned Pandas DataFrame
    left_right: rules to allow wetted perimeter calculations to return correct value
    
    Returns: Pandas Dataframe of hydraulic properties
    '''
    
    area, wetted_perims, top_width, hydraulic_rad = [], [], [], []
    
    index = 0
   
        
    for x in stage:
    
        #create intersection polygon
        inter = Polygon([(bounds["min_x"],bounds["min_y"]),
                         (bounds["max_x"],bounds["min_y"]),
                         (bounds["max_x"],x),
                         (bounds["min_x"],x)])
        
        intersection = pgon.intersection(inter)
        area.append(float(intersection.area))
        
        #the intersection may be a single polygon or a collection of multiple geometries
        #if single polygon
        if type(intersection) is Polygon:
            
            wetted_perims.append(
                get_wetted_perimeter(
                    intersection.exterior.coords, 
                    left_right, 
                    intersection.bounds,
                )
            )
            top_width.append(intersection.bounds[2]-intersection.bounds[0])
            
        else:
            
            temp_wetted_perims = []
            temp_top_widths = []
            
            #for each geometry in the collection
            for z in intersection.geoms:
                if type(z) is Polygon:
                    
                    temp_wetted_perims.append(
                        get_wetted_perimeter(
                            z.exterior.coords, 
                            left_right, 
                            z.bounds,
                        )
                    )
            
                    temp_top_widths.append(z.bounds[2]-z.bounds[0])
                    
                if type(z) is LineString:
                    
                    temp_wetted_perims.append(
                        get_wetted_perimeter(
                            z.coords, 
                            left_right, 
                            z.bounds,
                        )
                    )
            
                    temp_top_widths.append(z.bounds[2]-z.bounds[0])
                    
            top_width.append(np.sum(temp_top_widths))
            wetted_perims.append(np.sum(temp_wetted_perims))
              
        # if the wetted perimeter is zero avoid divide by zero
        if wetted_perims[-1] > 0:  
            hydraulic_rad.append(area[-1]/wetted_perims[-1])
        else:
            hydraulic_rad.append(0)
        
        index += 1
            
    return pd.DataFrame({
                        "".join(["Cross-sectional Area", name]) :
                                pd.Series(area, index = stage),
                        "".join(["Wetted Perimeter", name]) :
                                pd.Series(np.array(wetted_perims), index = stage),
                        "".join(["Top Width", name]) :
                                pd.Series(top_width, index = stage),
                        "".join(["Hydraulic Radius", name]) :
                                pd.Series(hydraulic_rad, index = stage),
                        })

def get_wetted_perimeter(coords, left_right, bounds):
    '''
    Computes the wetted perimeter for a LineString of coordinates
    
    Keyword arguments: 
    coords: list of coordinates representing a boundary to create LineString
    left_right: rules for deciding where to cut off line string
    bounds: the x-y bounds of the geometry (passed in for more terse code)
    
    Returns: Wetted perimeter (length of adjusted LineString
    '''
    
    coords = list(coords)
    
    #removes duplicate tuples of points
    duplicates = np.where(np.array([coords.count(x) for x in coords]) > 1)
    coords = np.delete(coords, duplicates[0][0], axis=0)
    
    #gets the highest points in order to sort the coordinates by its x values
    sort_query = np.where([x[1] == bounds[3] for x in coords])
    coords = np.concatenate([coords[sort_query[0][1]:],coords[:sort_query[0][1]]])
    
    #if no subdivisions
    if left_right == (False, False):
        
        try:
            return LineString(coords).length
        except:
            return 0
    
    #if subdivided and the right boundary borders another subdivision
    if left_right == (False,True):
        
        try:
            return LineString(coords[1:]).length
        except:
            return 0
    
    #if subdivided and both the right and the left boundary borders another subdivision
    if left_right == (True,True):
         
        try:
            return LineString(coords[1:-1]).length
        except:
            return 0
      
    #if subdivided and the left boundary borders another subdivision
    if left_right == (True,False):
        
        try:
            return LineString(coords[:-1]).length
        except:
            return 0
    
def get_total(master_data, pgon_len):
    '''
    Appends total columns to a hydraulic properties Dataframe if the polygon was subdivided 
    
    Keyword arguments: 
    master_data: the Dataframe with the subdivided hydraulic properties
    pgon_len: the number of polygons as a result of the subdivision
    
    '''
    
    #creates np arrays the size of the number of rows in the hydraulic properties dataframe
    total_area = np.repeat(0., master_data.shape[0])
    total_wetted_perimeter = np.repeat(0., master_data.shape[0])
    total_top_width = np.repeat(0., master_data.shape[0])
    
    #sum up the columns for each subdivision
    for x in range(1,pgon_len+1):
        total_area += master_data["Cross-sectional Area%d" % x]
        total_wetted_perimeter += master_data["Wetted Perimeter%d" % x]
        total_top_width += master_data["Top Width%d" % x]
        
    #get the hydraulic radius for the total column
    total_hydraulic_radius = total_area / total_wetted_perimeter
    total_hydraulic_radius[np.where(np.isinf(total_hydraulic_radius))] = 0
    
    #append total columns
    master_data["Total Cross-sectional Area"] = total_area
    master_data["Total Wetted Perimeter"] = total_wetted_perimeter
    master_data["Total Top Width"] = total_top_width
    master_data["Total Hydraulic Radius"] = total_hydraulic_radius
                
