#DEFERRED IMPLEMENTATION  - 1-24-2017

# import pandas as pd
# from Web.flow_calc import FlowCalculator 
# import numpy as np
# 
# prop_df = pd.read_csv('./uploads/props.csv')
# 
# fc = FlowCalculator()
# fc.datum = 23.95
# fc.auto = "true"
# fc.stage_increment = 0.01
# fc.sub_divisions = ''
# 
# fc.coord_file = './uploads/manning_coord4.csv'
# fc.create_table()
# result1 = fc.properties_df.copy()
# 
# 
# fc.coord_file = './uploads/manning_coord2.csv'
# # fc.datum = 23.65
# fc.create_table()
# result2 = fc.properties_df.copy()
#  
# fc.coord_file = './uploads/manning_coord3.csv'
# # fc.datum = 23.22
# fc.create_table()
# result3 = fc.properties_df.copy()
# 
# def closest_to_zero(index_list, value):
#     return np.array(np.abs(index_list - value)).argmin()
# 
# idx1 = closest_to_zero(result1.index, prop_df['Stage'].values[0])
# idx2 = closest_to_zero(result2.index, prop_df['Stage'].values[1])
# idx3 = closest_to_zero(result3.index, prop_df['Stage'].values[2])
# 
# Z1 = result1['Cross-sectional Area'].values[idx1] \
# * result1['Hydraulic Radius'].values[idx1]**(2./3.)
# Z2 = result2['Cross-sectional Area'].values[idx2] \
# * result2['Hydraulic Radius'].values[idx2]**(2./3.)
# Z3 = result3['Cross-sectional Area'].values[idx3] \
# * result3['Hydraulic Radius'].values[idx3]**(2./3.)
# 
# L12 = prop_df['Ref Distance'].values[1] - prop_df['Ref Distance'].values[0]
# L23 = prop_df['Ref Distance'].values[2] - prop_df['Ref Distance'].values[1]
# 
# Q = prop_df["Q"].values[0]
# h1 = prop_df["Water Surface Elevation"].values[0]
# h2 = prop_df["Water Surface Elevation"].values[1]
# h3 = prop_df["Water Surface Elevation"].values[2]
# 
# hv1 = (Q / result1['Cross-sectional Area'].values[idx1])**2 / (2. * 32.2)
# hv2 = (Q / result2['Cross-sectional Area'].values[idx2])**2 / (2. * 32.2)
# hv3 = (Q / result3['Cross-sectional Area'].values[idx3])**2 / (2. * 32.2)
# 
# h_hv3 = (h3 + hv3)
# h_hv2 = h_hv3 + ((h2-h3)+(hv3-hv2))
# h_hv1 = h_hv2 + ((h1-h2)+(hv2-hv1))
# 
# print np.sqrt((h_hv1 - h_hv3) / ((L12/(Z1*Z2)) + (L23/(Z2*Z3))))
# n = (1.486/Q) * np.sqrt(((h_hv1-h_hv3)) / ((L12/(Z1*Z2)) + (L23/(Z2*Z3))))
# print n
#     
# 
# 
# 
# 
# 
# 
# 


