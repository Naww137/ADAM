#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 19:33:07 2022

@author: noahwalton
"""

#!/usr/bin/env python
# coding: utf-8

# # Implementation of the stochastic gradiant descent algorithm
# # https://en.wikipedia.org/wiki/Stochastic_gradient_descent
# # And ADAM Gradient Descent
# # https://arxiv.org/pdf/1412.6980.pdf
# # Coupled to Scale Tsunami 

# In[1]:


import pandas as pd
import os
import math
import numpy as np
import random
import pixel
import pixel_array_functions
import cluster_interface
import scale_interface
import objective_function_definition


# In[2]:


def evaluate(parameter_df,
            pixel_array,
            steps,
            generations,
            template_file = 'template.inp',
            job_flag = "tsunami_job",
            build_input = True,
            submit_job = True,
            pull_keff = True,
            pull_sensitivities = True,
            delete_excess_run_files = False):
    """
    Evaluates the current step.
    
    This function takes the parameter vector and builds a corresponding TSUNAMI input. 
    It then runs that input on the UTK cluster. The result is then evaluated. 
    Sensitivities and other inofrmation are extracted and evaluated s.t. they can be
    fed to the next step. This includes converting the relative sensitivities to absolute derivatives.

    Parameters
    ----------
    parameter_df : TYPE
        DESCRIPTION.
    pixel_array : object array
        Array of pixel objects containing material/region/parameter information.
    materials : TYPE
        DESCRIPTION.
    tsunami_job_flag : TYPE, optional
        DESCRIPTION. The default is "tsunami_job".
    build_input : TYPE, optional
        DESCRIPTION. The default is True.
    submit_tsunami_job : TYPE, optional
        DESCRIPTION. The default is True.
    pull_keff : TYPE, optional
        DESCRIPTION. The default is True.
    pull_sensitivities : TYPE, optional
        DESCRIPTION. The default is True.

    Returns
    -------
    keff : TYPE
        DESCRIPTION.
    beta_sensitivities : TYPE
        DESCRIPTION.
    TYPE
        DESCRIPTION.
    TYPE
        DESCRIPTION.

    """
    
    
    
    ### Use parameter data frame to update the base material dictionary for each pixel in pixel array
    pixel_array_functions.get_updated_materials_in_pixel_array(pixel_array, parameter_df)
    
    
    
    
    ### Building scale input
    
    if build_input:

        # generate random number seed
        random_number = random.randint(1152921504606846976,18446744073709551615)
        hex_number = str(hex(random_number))
        hex_number = hex_number [2:]
        
        # create input file from template file
        scale_interface.create_tsunami_input(template_file, job_flag+'.inp', steps, hex_number, generations)
        
        # write each pixel's material string to target input file
        pixel_array_functions.write_material_strings_to_template(pixel_array, job_flag+'.inp')
    
        # create an .sh file for TORQUE job submission on the UTK NE cluster
        cluster_interface.build_scale_submission_script(job_flag, solve_type = 'tsunami')
        
    else:
        print("Skipping building scale input file.")
    



    ### Submit tsunami job and wait on it to complete
    
    if submit_job:
        assert build_input == True, "You didn't build a new input, but you're submitting to the cluster. Quite irregular."
        cluster_interface.submit_jobs_to_necluster(job_flag)
        cluster_interface.wait_on_submitted_job(job_flag)
    else:
        print("Not submitting the tsunami job.")
        
        
    
    
    ### Pull out keff and sensitivities from job
    
    output_file = job_flag+'.out'
    sensitivity_dictionary, keff = scale_interface.read_total_sensitivity_by_nuclide(output_file)
    
    # convert scale IDed sensitivities to sensitivities specific to each pixel/pixel region in the pixel_array
    pixel_array_functions.get_nuclide_sensitivites_for_each_pixel(pixel_array, sensitivity_dictionary)
 
    
    
    
    ### Delete un-necessary_files from the previous job
    
    if delete_excess_run_files:
        cluster_interface.remove_unwanted_files()

    
       
    return keff






# In[3]:



def ADAM(parameter_df,
        pixel_array, 
        material_dict_base,
        template_file,
        generations = 10,
        submit_job = True,
        stopping_value = 0.001,
        number_of_steps = 10,
        alpha_value = 0.1, 
        beta_1 = 0.9,
        beta_2 = 0.999,
        epsilon = 1,
        write_output = False,
        starting_step = 1,
        starting_first_moment=[],
        starting_second_moment=[]):
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
    # stopping_criteria = False
    # parameters = parameter_df
       
    # only write new output csv files if we are starting at step 1
    if starting_step == 1:
        if write_output:
            
            print("\nWARNING: Need to update print-to-csv functions to be dynamic WRT parameter definitions\n")
            
            with open('output.csv', 'w') as output_file:
                output_file.write("step, keff\n")
            with open('parameters.csv', 'w') as output_file:
                # string = 'step, keff,'
                # string += f' {parameter_df.keys()[0]} [1x{len(parameter_df)}, {parameter_df.keys()[1]} [1x{len(parameter_df)}\n'
                output_file.write("step, keff, fuel_betas_this_step [1x1936], mod_betas_this_step [1x1936]\n")
            with open('first_moments.csv', 'w') as output_file:
                output_file.write("step, keff, fuel_1st_moment_vectors_this_step [1x1936], mod_1st_moment_vectors_this_step [1x1936], fuel_2nd_moment_vectors_this_step [1x1936], mod_2nd_moment_vectors_this_step [1x1936]\n")
            with open('second_moments.csv', 'w') as output_file:
                output_file.write("step, keff, fuel_2nd_moment_vectors_this_step [1x1936], mod_2nd_moment_vectors_this_step [1x1936]\n")

       


    ### Main loop
    while steps < number_of_steps + 1:
        
        print("Step #:", steps)
        job_flag = 'tsunami_job_' + str(steps)
        
        
        # apply a transformation of variables to the domain
        transformed_parameters = parameter_df.apply(objective_function_definition.transformation_function)
         
        
        
        ### Evaluate with TSUNAMI, sensitivities/derivatives stored in pixel_array objects
        keff = evaluate(transformed_parameters,
                        pixel_array,
                        steps,
                        generations,
                        template_file = template_file, # 'spent_fuel_cask_template.inp', #'tsunami_template_file_10x10.inp'
                        job_flag = job_flag,                    
                        submit_job = submit_job)
        
        
        
        # combine derivatives wrt nuclides in each region to get derivatives wrt multiplication factors
        print("Need to update documentation to maintain consistent verbiage for multiplication factors or optimization parameters")
        derivative_df = pixel_array_functions.get_combined_derivatives(pixel_array, material_dict_base)
       
        
       
        # chain rule for transofrmation function to get derivatives wrt optimization parameters
        obj_derivative_df = objective_function_definition.objective_derivative(derivative_df, parameter_df)
       
        
       
        ### perform the ADAM algorithm update (remember, this is a minimization)
        first_moment_df = (beta_1 * first_moment_vector  + (1 - beta_1) * obj_derivative_df)
        second_moment_df = (beta_2 * second_moment_vector + (1 - beta_2) * obj_derivative_df**2) 
        first_moment_hat_df = (first_moment_df / (1 - beta_1**steps))
        second_moment_hat_df = (second_moment_df/ (1 - beta_2**steps))
       
        new_parameter_df = (parameter_df - (alpha_value * first_moment_hat_df) / (np.sqrt(second_moment_hat_df) + epsilon))
                             
            
            
        ### Writing out the output file                                      
        if write_output:
            with open('output.csv', 'a') as output_file:
                write_string = str(steps) + "," + str(keff)
                output_file.write(write_string + "\n")
            with open('parameters.csv', 'a') as par_file:
                np.savetxt(par_file, [np.array(parameter_df).flatten()], delimiter=',')
            with open('first_moments.csv', 'a') as fm_file:
                np.savetxt(fm_file, [np.array(first_moment_df).flatten()], delimiter=',')
            with open('second_moments.csv', 'a') as sm_file:
                np.savetxt(sm_file, [np.array(second_moment_df).flatten()], delimiter=',')
                
                
                
        # redefine parameters as new updated parameters, increase step number, repeat in while loop
        parameter_df = new_parameter_df
        steps += 1
        

    

    
