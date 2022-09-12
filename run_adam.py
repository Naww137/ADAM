

#%%

import numpy as np
import pandas as pd
import ADAM

#%%  User input for problem setup


### Build initial parameter dataframe

# Define the number of pixels to be considered and the initial optimization parameters to use if starting from step 1.
# If not starting from step 1, assign starting_step as the step to be ran next (i.e if steps 1-20 have been ran starting_step=21)

number_of_pixels = 289
starting_step = 1

if starting_step == 1:
    
    parameter_df = pd.DataFrame()
    parameter_df['optimization_parameter_1'] = np.ones([number_of_pixels])
    parameter_df['optimization_parameter_2'] = np.ones([number_of_pixels])

else:
     _ = 0



### Define base materials to be used in the problem 

material_dict_base = {'fuel':{
                             'u-235':8.59435E-04,
                             'u-238':2.23686E-02,
                             'o-16':4.64708E-02},
    
                    'zircalloy':{'cr-50':3.62373E-06,
                            'cr-52':6.98800E-05,
                            'cr-53':7.92383E-06,
                            'cr-54':1.97241E-06,
                            'fe-54':9.08312E-06,
                            'fe-56':1.42586E-04,
                            'fe-57':3.29292E-06,
                            'fe-58':4.38228E-07,
                            'zr-90':2.18292E-02,
                            'zr-91':4.76042E-03,
                            'zr-92':7.27640E-03,
                            'zr-94':7.37398E-03,
                            'zr-96':1.18798E-03,
                            'sn-112':4.64145E-06,
                            'sn-114':3.15810E-06,
                            'sn-115':1.62690E-06,
                            'sn-116':6.95739E-05,
                            'sn-117':3.67488E-05,
                            'sn-118':1.15893E-04,
                            'sn-119':4.11031E-05,
                            'sn-120':1.55895E-04,
                            'sn-122':2.21545E-05,
                            'sn-124':2.77051E-05},
                 
                    'moderator':{
                                'o-16':3.3368E-02,
                                'h-1':6.6733E-02}  
                                                  }

material_df_base = pd.DataFrame(material_dict_base)




### Define geometric regions (repeating regions in this case) and the materials present within each

region_definition = {'rod':['fuel','moderator'], 'gap':['moderator'], 'clad':['zircalloy','moderator']}
# region_definition = {'whole_pixel':['fuel','moderator']}



### Define the optimization parameters corresponding to the geometric region definition

parameter_definition = {'rod':['optimization_parameter_1','optimization_parameter_2'], 'gap':['optimization_parameter_2'], 'clad':['optimization_parameter_1','optimization_parameter_2']}
# parameter_definition = {'whole_pixel':['optimization_parameter_1','optimization_parameter_2']}







#%% Check material/region/parameter input


for region in region_definition:
    if region not in parameter_definition:
        raise ValueError("A region is defined in region_definition but not parameter_definition, please fix this before running ADAM")
for region in parameter_definition:
    if region not in region_definition:
        raise ValueError("A region is defined in parameter_definition but not region_definition, please fix this before running ADAM")
for region in region_definition:
    if len(region_definition[region]) != len(parameter_definition[region]):
        raise ValueError(f"The number of materials defined in region '{region}' do not match the number of parameters defined in that region")


print("\nYou entered the following region, material, and parameter definitions:\n")
for region in region_definition.keys():
    for material, parameter in zip(region_definition[f'{region}'], parameter_definition[f'{region}']):
        print(f'For region "{region}" the material "{material}" will be controlled by {parameter}')
print()


input("Press enter to continue and run ADAM...")



#%% Initialize pixel array and run ADAM if user confirms their geometry

pixel_array = ADAM.pixel_array_functions.initialize_pixel_array(number_of_pixels, region_definition, parameter_definition, material_df_base, 300)

ADAM.ADAM_control_module.ADAM(parameter_df,
                        pixel_array, 
                        material_dict_base,
                        'spent_fuel_cask_template.inp',
                        generations = 10,
                        submit_job=False,
                        alpha_value = 0.1,
                        beta_1=0.9,
                        number_of_steps = 1,
                        write_output = True,
                        epsilon = 1e-8,
                        
                        starting_step = starting_step,
                        
                        starting_first_moment = [],
                        starting_second_moment = [])