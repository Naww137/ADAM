#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 21:29:33 2022

@author: noahwalton
"""

#%%
import pandas as pd
import numpy as np
import pixel

pixels = 6


# take in parameters that are being optimized by ADAM!
parameter_df = pd.DataFrame()
parameter_df['par1'] = np.ones([pixels])
parameter_df['par2'] = np.ones([pixels])



#%%

# now, how do I want to apply these parameters to a physical thing
#pard = {'par1':np.ones([pixels]), 'par2':np.ones([pixels])}
par1 = np.array([1,1,1])
par2 = np.array([2,2,2])

#pard = {'rod':[par_fuel,par_mod], 'clad':[par_fuel, par_mod]}

#material_df['mat1'] = 

# define base material values that you want to use in the geometry
material_dict_base = {'fuel':{
                         'u-235':8.59435E-04,
                         'u-238':2.23686E-02,
                         'o-16':4.64708E-02},
                'zircalloy':{'cr-50':3.62373E-06,
                        'cr-52':6.98800E-05,
                        'cr-53':7.92383E-06},
# =============================================================================
#                  'zircalloy':{'cr-50':3.62373E-06,
#                          'cr-52':6.98800E-05,
#                          'cr-53':7.92383E-06,
#                          'cr-54':1.97241E-06,
#                          'fe-54':9.08312E-06,
#                          'fe-56':1.42586E-04,
#                          'fe-57':3.29292E-06,
#                          'fe-58':4.38228E-07,
#                          'zr-90':2.18292E-02,
#                          'zr-91':4.76042E-03,
#                          'zr-92':7.27640E-03,
#                          'zr-94':7.37398E-03,
#                          'zr-96':1.18798E-03,
#                          'sn-112':4.64145E-06,
#                          'sn-114':3.15810E-06,
#                          'sn-115':1.62690E-06,
#                          'sn-116':6.95739E-05,
#                          'sn-117':3.67488E-05,
#                          'sn-118':1.15893E-04,
#                          'sn-119':4.11031E-05,
#                          'sn-120':1.55895E-04,
#                          'sn-122':2.21545E-05,
#                          'sn-124':2.77051E-05},
# =============================================================================
                 
                  'moderator':{'o-16':3.3368E-02,
                         'h-1':6.6733E-02}  }

# define geometric regions (repeating regions in this case) and the materials present within each
region_definition = {'rod':['fuel','moderator'], 'clad':['zircalloy','moderator']}

parameter_definition = {'rod':['par1','par2'], 'clad':['par1','par2']}

    
parameters = parameter_df.iloc[0]

    
    
#%%



# make material base a dataframe 
material_df_base = pd.DataFrame(material_dict_base)


    


# create scale input string
temp = 300
    
# initialize pixel array
pixel_array = []
for i in range(pixels):
    pixel_array.append(pixel.pixel(region_definition, parameter_definition, material_df_base, i+1))

# update materials based on optimization parameter
for i in range(pixels):
    pixel_array[i].get_updated_material_definition(parameter_df.iloc[i])
    pixel_array[i].write_material_string_for_single_pixel(temp)



def write_pixel_material_strings_to_template(template_file, input_file):
    
    with open(template_file, 'r') as f:
        readlines = f.readlines()
        f.close()
        
    with open(input_file, 'w') as f:
        for line in readlines:
            f.write(line)
            
            if line.startswith('read composition'):
                for each_pixel in pixel_array:
                    f.write(each_pixel.material_string)
                    
tempfile = '/Users/noahwalton/Documents/GitHub/ADAM/mini_template.inp'
inpfile = '/Users/noahwalton/Documents/GitHub/ADAM/test.inp'
        
        
write_pixel_material_strings_to_template(tempfile, inpfile)

# %%
