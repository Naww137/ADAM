#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 20:21:22 2022

@author: noahwalton
"""

import pandas as pd
import numpy as np
import math

# =============================================================================
# def adam_gradient_descent_scale(initial_betas,
#                            debug_print_all = False,
#                            submit_tsunami_job = True,
#                            stopping_value = 0.001,
#                            number_of_steps = 10,
#                            alpha_value = 0.1, 
#                            beta_1 = 0.9,
#                            beta_2 = 0.999,
#                            epsilon = 1,
#                            write_output = False,
#                            write_output_string = "output.csv",
#                            fix_mass_adjustment = True,
#                            fix_mass_target = 'initial',
#                            fix_mass_round_value = 5,
#                            fix_mass_type='all',
#                            starting_step = 1,
#                            initialize_first_and_second_vectors_from_sdf = False,
#                            initialize_first_and_second_vector_target_sdf_file = "default",
#                            initialize_first_and_second_vector_target_sdf_betas = [],
#                            starting_first_moment_vector=[[],[]],
#                            starting_second_moment_vector=[[],[]],
#                            materials = ["void", "fuel/moderator:25/75"]):
# =============================================================================

parameter_df = pd.DataFrame()
parameter_df['fuel'] = [1,1,1,1,1]
parameter_df['mod'] = [2,2,2,2,2]

debug_print_all = False
submit_tsunami_job = True
stopping_value = 0.001
number_of_steps = 10
alpha_value = 0.1
beta_1 = 0.9
beta_2 = 0.999
epsilon = 1
write_output = False
write_output_string = "output.csv"
fix_mass_adjustment = True
fix_mass_target = 'initial'
fix_mass_round_value = 5
fix_mass_type='all'
starting_step = 1
initialize_first_and_second_vectors_from_sdf = False
initialize_first_and_second_vector_target_sdf_file = "default"
initialize_first_and_second_vector_target_sdf_betas = []

starting_first_moment = pd.DataFrame(np.ones([len(parameter_df.index),len(parameter_df.columns)]),columns=parameter_df.columns)
starting_second_moment = pd.DataFrame(np.ones([len(parameter_df.index),len(parameter_df.columns)]),columns=parameter_df.columns)

materials = ["void", "fuel/moderator:25/75"]




#%%

def transformation_function(x):
    
    y = np.exp(x)
    
    return y


#%%
"""
Executes ADAM gradient descent algorithm at the highest level.

Parameters
----------
sensitivities : TYPE
    DESCRIPTION.
betas : TYPE
    DESCRIPTION.

Returns
-------
new_sensitivities : TYPE
    DESCRIPTION.

"""

steps = starting_step
 

if starting_step > 1:
    first_moment = starting_first_moment
    second_moment = starting_second_moment
else:   
    # initializae first/second moment vectors as all 0 for very first step - could be better informed
    first_moment_vector = pd.DataFrame(np.zeros([len(parameter_df.index),len(parameter_df.columns)]),columns=parameter_df.columns)
    second_moment_vector = pd.DataFrame(np.zeros([len(parameter_df.index),len(parameter_df.columns)]),columns=parameter_df.columns)


### Stopping_criteria not implemented currently, only # of steps
stopping_criteria = False
parameters = parameter_df

# only write new output csv files if we are starting at step 1
if starting_step == 1:
    if write_output:
        with open('output.csv', 'w') as output_file:
            output_file.write("step, keff\n")
        with open('parameters.csv', 'w') as output_file:
            output_file.write("step, keff, fuel_betas_this_step [1x1936], mod_betas_this_step [1x1936]\n")
        with open('moments.csv', 'w') as output_file:
            output_file.write("step, keff, fuel_1st_moment_vectors_this_step [1x1936], mod_1st_moment_vectors_this_step [1x1936], fuel_2nd_moment_vectors_this_step [1x1936], mod_2nd_moment_vectors_this_step [1x1936]\n")


### Main loop
while steps == 1: # < number_of_steps + 1:
    
    print("Step #:", steps)
    ### 
    tsunami_job_flag = 'tsunami_job_' + str(steps)
    
    transformed_parameters = transformation_function(parameters)
    
    
    
    steps += 1
    
    
    
    
    #%%
    
    ### Evaluate with TSUNAMI
    keff, beta_sensitivities, material_1_sense, material_2_sense = evaluate_with_Tsunami(variables_func,
                                                         tsunami_job_flag = tsunami_job_flag,                    
                                                         submit_tsunami_job = submit_tsunami_job,
                                                         materials = materials)

     
    ### Mulitplying %keff derives by keff

    #beta_sensitivities = [float(deriv * float(keff)) for deriv in beta_sensitivities]
    print(sum(variables_func[0]))
    print(sum(variables_func[1]))
   
   # put through sensitivity of obj function - now we have a penalty on extremely small betas
    beta_sensitivities = sensitivity_function(beta_sensitivities, variables)
   
    
    first_moment_vector_hat=[[],[]]
    second_moment_vector_hat=[[],[]]
    new_variables=[[],[]]  
    ### Implementation of ADAM gradient descent
    for i in range(2):
        first_moment_vector[i] = [(beta_1 * first_mv  + (1 - beta_1) * deriv) for first_mv, deriv in zip(first_moment_vector[i], beta_sensitivities[i])]
        second_moment_vector[i] = [(beta_2 * second_mv + (1 - beta_2) * deriv**2) for second_mv, deriv in zip(second_moment_vector[i], beta_sensitivities[i])]
        first_moment_vector_hat[i] = [(first_mv / (1 - beta_1**steps)) for first_mv in first_moment_vector[i]]
        second_moment_vector_hat[i] = [(second_mv/ (1 - beta_2**steps)) for second_mv in second_moment_vector[i]]
        new_variables[i] = [(beta + (alpha_value * first_mv) / (math.sqrt(second_mv) + epsilon)) for
                         beta, first_mv, second_mv in zip(variables[i], first_moment_vector_hat[i], second_moment_vector_hat[i])]
    
    
    
    if fix_mass_adjustment:    
        new_variables = fixed_mass_adjustment(new_variables,
                                              target_mass, 
                                              beta_sensitivities,
                                              fix_mass_type,
                                              debug=debug_print_all,
                                              mass_round_dig = fix_mass_round_value)
    new_variables = np.array(new_variables)

    if debug_print_all:
        debug_write_out_10x10_list(beta_sensitivities, "beta_sensitivities")
        debug_write_out_10x10_list(first_moment_vector, "first_moment_vector")
        debug_write_out_10x10_list(second_moment_vector, "second_moment_vector")
        debug_write_out_10x10_list(first_moment_vector_hat, "first_moment_vector_hat")
        debug_write_out_10x10_list(second_moment_vector_hat, "second_moment_vector_hat")
        debug_write_out_10x10_list(variables, "variables")
        debug_write_out_10x10_list(new_variables, "new_variables_final")
        
        
    ### Writing out the output file   
    #! redo this to write steps and keff, betas, and moment vectors separately                                       
    if write_output:                                        # !!! these variable must be printed this way in order to start at step>1
        with open(write_output_string, 'a') as output_file:
            write_string = str(steps) + "," + str(keff)
            
            for _ in variables[0]:                      
                write_string += "," + str(_)
            
            for _ in variables[1]:                      
                write_string += "," + str(_)
                
            for _ in first_moment_vector[0]:
                write_string += "," + str(_)
                
            for _ in first_moment_vector[1]:
                write_string += "," + str(_)
                
            for _ in second_moment_vector[0]:
                write_string += "," + str(_)
                
            for _ in second_moment_vector[1]:
                write_string += "," + str(_)
            
            output_file.write(write_string + "\n")
    steps += 1 
    print('Keff')  
    print(keff_old)
    print(keff)
    if (float(keff_old)<float(keff)):
        variables = new_variables           # new variables are not run yet
        alpha_value=alpha_value*1.0
        keff_old=keff
    else:
        variables = new_variables
        alpha_value=alpha_value*1.0
        keff_old=keff

    print(alpha_value)


# In[9]:


### Building initial beta values
#material_betas = build_initial_betas(1, 2, 'random', rand_min = 0.2, rand_max = 0.8)
number_used=61


# =============================================================================
# starting criteria !!!
# assign starting_step as the step to be ran next (i.e if steps 1-20 have been ran starting_step=21)
# =============================================================================
starting_step = 1
Non_Uniform_Start = True

# p1 solution
fb = -2.4001086204461104
mb = -1.8978802738322902
zb = -15

# p1 sanity check
# =============================================================================
# fb = -2.2603464290159994
# mb = -1.8683184827943493
# zb = -50
# =============================================================================

# optimal circle search results
fb = -1.745323
mb = -1.147416
zbf = -6
zbm = -6

if starting_step == 1:
    
    material_betas_start=[[],[]]
    
    # default function inputs if not initializing
    initialize_boolean=False; initialize_file= "default"; initialize_betas=[]
    initialize_first_moment_vectors = [[],[]]; initialize_second_moment_vectors=[[],[]]
    
    if Non_Uniform_Start:               ## forcing function is exponential e^beta = atom dens scaling factor
        # fuel betas
        material_betas_start[0] = [zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf,
                                   zbf, zbf, zbf,  fb,  fb,  fb,  fb, zbf, zbf, zbf,
                                   zbf, zbf,  fb,  fb,  fb,  fb,  fb,  fb, zbf, zbf,
                                   zbf,  fb,  fb,  fb,  fb,  fb,  fb,  fb,  fb, zbf,
                                   zbf,  fb,  fb,  fb,  fb,  fb,  fb,  fb,  fb, zbf,
                                   zbf,  fb,  fb,  fb,  fb,  fb,  fb,  fb,  fb, zbf,
                                   zbf,  fb,  fb,  fb,  fb,  fb,  fb,  fb,  fb, zbf,
                                   zbf, zbf,  fb,  fb,  fb,  fb,  fb,  fb, zbf, zbf,
                                   zbf, zbf, zbf,  fb,  fb,  fb,  fb, zbf, zbf, zbf,
                                   zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf, zbf,]
        # mod betas
        material_betas_start[1] = [mb,  mb,  mb,  mb,  mb,  mb,  mb,  mb,  mb, mb,
                                   mb,  mb,  mb, zbm, zbm, zbm, zbm,  mb,  mb, mb,
                                   mb,  mb, zbm, zbm, zbm, zbm, zbm, zbm,  mb, mb,
                                   mb, zbm, zbm, zbm, zbm, zbm, zbm, zbm, zbm, mb,
                                   mb, zbm, zbm, zbm, zbm, zbm, zbm, zbm, zbm, mb,
                                   mb, zbm, zbm, zbm, zbm, zbm, zbm, zbm, zbm, mb,
                                   mb, zbm, zbm, zbm, zbm, zbm, zbm, zbm, zbm, mb,
                                   mb,  mb, zbm, zbm, zbm, zbm, zbm, zbm,  mb, mb,
                                   mb,  mb,  mb, zbm, zbm, zbm, zbm,  mb,  mb, mb,
                                   mb,  mb,  mb,  mb,  mb,  mb,  mb,  mb,  mb, mb,]
    else:
        material_betas_start[0] = build_initial_betas(10, 10, 'fixed', fixed_value = -2)
        material_betas_start[1] = build_initial_betas(10, 10, 'fixed', fixed_value = -2)
        
        
    
else:
    
    data = np.genfromtxt('output.csv', delimiter=',', skip_header=1, usecols=range(2,602))
    material_betas_start=[[],[]]
    material_betas_start[0] = data[-1, 0:100]
    material_betas_start[1] = data[-1, 100:200]  
    
# =============================================================================
#     for mat in range(2):
#         material_betas_start[mat] = [-20 if beta < -20 else beta for beta in material_betas_start[mat]]
#         material_betas_start[mat] = [20 if beta > 20 else beta for beta in material_betas_start[mat]]
# =============================================================================
            
    initialize_first_moment_vectors = [[],[]]; initialize_second_moment_vectors=[[],[]]
    initialize_first_moment_vectors[0] = data[-1,200:300]; initialize_first_moment_vectors[1] = data[-1,300:400]
    initialize_second_moment_vectors[0] = data[-1,400:500]; initialize_second_moment_vectors[1] = data[-1,500:600]
    
    # function inputs if initializing
    initialize_boolean=True
    initialize_file= 'tsunami_job_' + str(starting_step-1) +'.sdf'
    initialize_betas=material_betas_start
    



# =============================================================================
# ### running adam gradient descent algorithm
# =============================================================================
adam_gradient_descent_scale(material_betas_start,
                       submit_tsunami_job=False,
                       debug_print_all = False,
                       alpha_value = 0.1,
                       beta_1=0.9,
                       number_of_steps = 4,
                       write_output = True,
                       epsilon = 1e-8,
                       fix_mass_adjustment = False,
                       fix_mass_target = 'initial',
                       fix_mass_round_value = 5,
                       
                       starting_step = starting_step,
                       initialize_first_and_second_vectors_from_sdf = initialize_boolean,
                       initialize_first_and_second_vector_target_sdf_file = initialize_file,
                       initialize_first_and_second_vector_target_sdf_betas = initialize_betas,
                       starting_first_moment_vector=initialize_first_moment_vectors,
                       starting_second_moment_vector=initialize_second_moment_vectors,
                       
                       materials = ["fuel","moderator"])
