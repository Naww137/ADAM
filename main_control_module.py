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
import file_handler
import math
from scipy.linalg import null_space
import numpy as np
import random
import operator


# In[2]:


### This function turns a set a of beta values into a runable scale input
def build_scale_input_from_beta(scale_handler,
                                parameter_vector,
                                material_1,
                                material_2,
                                template_file_string,
                                flag,
                                flag_replacement_string='replace',
                                temperature=300,
                                material_count_offset=1,
                                file_name_flag='default_',
                                replacement_dict_addition = ''):
    """
    Builds scale inputs from a set of parameter values.

    Parameters
    ----------
    scale_handler : TYPE
        DESCRIPTION.
    parameter_vector : TYPE
        DESCRIPTION.
    material_1 : TYPE
        DESCRIPTION.
    material_2 : TYPE
        DESCRIPTION.
    template_file_string : TYPE
        DESCRIPTION.
    flag : TYPE
        DESCRIPTION.
    flag_replacement_string : TYPE, optional
        DESCRIPTION. The default is 'replace'.
    temperature : TYPE, optional
        DESCRIPTION. The default is 300.
    material_count_offset : TYPE, optional
        DESCRIPTION. The default is 1.
    file_name_flag : TYPE, optional
        DESCRIPTION. The default is 'default_'.
    replacement_dict_addition : TYPE, optional
        DESCRIPTION. The default is ''.

    Returns
    -------
    None.

    """

    material_list = []
    #print(material_betas)
    print('here')
    for i in range(len(parameter_vector[0])):         # !!! each isotope is multiplied by its material beta 
        material_list.append(scale_handler.combine_material_dicts(material_1, material_2, parameter_vector[0][i], parameter_vector[1][i])) 
        #print(beta)
    print('here')
    # material_list.append(scale_handler.combine_material_dicts(material_1, "", material_betas[0]))
    # material_list.append(scale_handler.combine_material_dicts(material_2, "void", material_betas[1]))


    material_string_list = []
    for count, material in enumerate(material_list):
        material_string_list.append(
            scale_handler.build_scale_material_string(material, count + material_count_offset, temperature))

    ### Making list of keys
    flag_list = []
    for x in range(len(material_string_list)):
        flag_list.append(flag.replace(flag_replacement_string, str(x)))

    material_dict = scale_handler.make_data_dict(flag_list, material_string_list)
    
    for flag in replacement_dict_addition:
        material_dict[flag] = replacement_dict_addition[flag]

    scale_handler.create_scale_input_given_target_dict(template_file_string, file_name_flag, material_dict)

### This function takes a list of materials in each material type and sums
### the sensitivites for each. 
### Inputs:
### materials_list - list of dictionaries in with the form {"isotope":nuclear density,...}
### sensitivities - nested dictionaries
### material_betas passed in is the multiplication factors directly applied to the previous atom densities (forcing function has already been applied)
def combine_sensitivities_make_absolute(materials_list, keff, material_betas, sensitivities):
    #print(materials_list)
    #print(sensitivities)
    material_sens_lists = []

    ### Sum all sensitivities for each material dictionary in the list of materials
    for material_dict in materials_list:
        ### Sum all poison and fuel/mod sensitivities
        sensitivity_sum_list = []
        for material_loc in sensitivities:

            if material_loc == '0':
                #print("SKIPPING TOTAL SENSITIVITY")
                continue

            sum_ = 0.0

# current error where rel to abs factor is so large in magnitude
# =============================================================================            
            for isotope in material_dict:
                
                # !!! need to multiply by k/N to get absolute partial derivative from relative partial -> rel_to_abs_factor
                
                if len(material_dict) > 2:          # case for fuel material (len=5)
                
                ## material betas here are already exponentiated... can N be per barn-cm because it is here
                    rel_to_abs_factor = float(keff)/(float(material_dict[isotope])*material_betas[0][abs(int(material_loc))-1]) 
                                
                    if isotope == 'o-16':
                        sum_ += 2*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                    elif isotope == 'u-234':
                        sum_ += 1*0.0002807253944191792*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                    elif isotope == 'u-235':
                        sum_ += 1*0.030374487676155186*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                    elif isotope == 'u-236':
                        sum_ += 1*0.00011229015776767166*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                    elif isotope == 'u-238':
                        sum_ += 1*0.969232496771658*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                        
                else:                               # case for moderator material
                
                    rel_to_abs_factor = float(keff)/(float(material_dict[isotope])*material_betas[1][abs(int(material_loc))-1])
                    
                    if isotope == 'h-1':
                        sum_ += 2*float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                    else:
                        sum_ += float(sensitivities[material_loc][isotope]['sensitivity'])*rel_to_abs_factor
                        
            sensitivity_sum_list.append(sum_)
# =============================================================================

        material_sens_lists.append(sensitivity_sum_list)

    return material_sens_lists   # returns 2 arrays of 100 location sensitivities [fuel, mod]



### This function takes the d%keff/d%material_change and turns them into d%keff/dbeta
### Inputs:
### tsunami_betas: List of beta values from 0-1
### material_1 and 2_sensitivities: the total tsunami sensitivities from calculation
### beta_diff is the amount added and subtracted to beta values
def calculate_sensitivities_2_materials_general(tsunami_betas,                                          # !!!!! not used anywhere !!!!!
                                                material_1_sensitivities,
                                                material_2_sensitivities,
                                                beta_diff = 0.01):
    sensitivities = []
    for mat_count, material_1_sensitivity in enumerate(material_1_sensitivities):
        material_2_sensitivity = material_2_sensitivities[mat_count]
        beta_ = tsunami_betas[mat_count]

        ### Calculating percent change in poison
        ###     Calculating % change in each material
        x_1_material_1_beta_change_percent = (beta_ + beta_diff) / beta_ - 1
        
        x_1_material_2_beta_change_percent = (1 - beta_ - beta_diff) / (1 - beta_) - 1

        x_2_material_1_beta_change_percent = (beta_ - beta_diff ) / beta_ - 1
        x_2_material_2_beta_change_percent = (1 - beta_ + beta_diff) / (1 - beta_) - 1
        

        ###     Multiplying the percent change in beta by the sensitivity 
        ###     per % change in beta.
        y_1 = x_1_material_1_beta_change_percent * material_1_sensitivity +               x_1_material_2_beta_change_percent * material_2_sensitivity

        y_2 = x_2_material_1_beta_change_percent * material_1_sensitivity +               x_2_material_2_beta_change_percent * material_2_sensitivity

        ###    
        x_1 = beta_ + beta_diff
        x_2 = beta_ - beta_diff
        
        ### Adding calculating d% sensitivity/dbeta 
        sensitivities.append((y_2 - y_1) / (x_2 - x_1))
    return sensitivities




### This function takes the material betas that describe the geometry, builds the tsunami job and runs it.
### Then it pulls out the keff and senstivities and converts them into usable form
### Inputs:
### material_betas - variables_func is passed in here, it is a list of the multiplying factors directly applied (forcing function already used)
### materials - list of material dictionaries for each material
### tsunami_job_flag - string to start tsunami jobs with
### debug_fake_tsunami_run - skips running tsunami 
def evaluate_with_Tsunami(parameter_df,
                          tsunami_job_flag = "tsunami_job",
                          build_input = True,
                          submit_tsunami_job = True,
                          pull_keff = True,
                          pull_sensitivities = True):
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
    
    # convert dataframe to legacy dictionary structure
    parameter_vector = list(list(parameter_df.to_numpy().T))
    materials = list(parameter_df.columns)
    
    
    sfh = file_handler.scale_file_handler()
    default_material_list = sfh.build_material_dictionaries(materials, multiplier = 1.0)
    
    ### Building scale input
    if build_input:
        random_number = random.randint(1152921504606846976,18446744073709551615)
        hex_number = str(hex(random_number))
        hex_number = hex_number [2:]
        rep_dict_addition = {'%%%random_number%%%':hex_number}

        build_scale_input_from_beta(sfh,
                                     parameter_vector=parameter_vector,
                                     material_1=default_material_list[0],
                                     material_2=default_material_list[1],
                                     flag="%material_replace%",
                                     flag_replacement_string='replace',
                                     template_file_string="tsunami_template_file_10x10.inp",
                                     file_name_flag=tsunami_job_flag,
                                     replacement_dict_addition = rep_dict_addition)
        sfh.build_scale_submission_script(tsunami_job_flag, solve_type = 'tsunami')
        
    else:
        print("Skipping building scale input file.")
    

    if submit_tsunami_job:
        assert build_input == True, "You didn't build a new input, but you're submitting to the cluster. Quite irregular."
        sfh.submit_jobs_to_necluster(tsunami_job_flag)
        sfh.wait_on_submitted_job(tsunami_job_flag)
    else:
        print("Not submitting the tsunami job.")
    
    ### Pulling out keff from Tsunami job
    if pull_keff:
        print("    Pulling keff")
        ### Checking if tsunami_jog_flag has ".out" at the end, if not, add it.
        if tsunami_job_flag.endswith('.out') == False:
            keff_filename = tsunami_job_flag + ".out"
        else:
            keff_filename = tsunami_job_flag
            
        keff, uncert = sfh.get_keff_and_uncertainty(keff_filename)
    else:
        print("Faking keff")
        keff = 0.0
    
    ### Pulling out sensitivities and turning them into dk/k/dB 
    if pull_sensitivities:
        print("    Pulling sensitivities")
        
        ### Checking if tsunami_jog_flag has ".sdf" at the end, if not, add it.
        if tsunami_job_flag.endswith('.sdf') == False:
            sdf_filename = tsunami_job_flag + ".sdf"
        else:
            sdf_filename = tsunami_job_flag
        
        material_derivatives = combine_sensitivities_make_absolute(default_material_list, keff, parameter_vector,      # returns 2 lists of 100 locational sensitivities [fuel,mod]
                                                              sfh.parse_sdf_file_into_dict(sdf_filename))
        
        # convert material sensitivities to pd dataframe for output
        derivative_df = pd.DataFrame(np.array(material_derivatives).T, columns=materials)
        
       
    return keff, derivative_df

# In[5]:


### inputs:
### x_dim, y_dim - X and Y size of beta matrix
### build_type - "fixed" for applying "fixed_value" to each location, "random" for uniformly distributed random values 
def build_initial_betas(x_dim, y_dim, build_type, rand_min = 0.0, rand_max = 1.0, fixed_value = 0.5):
    material_betas = []
    for x in range(x_dim):
        for y in range(y_dim):
            if build_type == 'random':
                material_betas.append(random.uniform(rand_min, rand_max))
            if build_type == 'fixed':
                material_betas.append(fixed_value)
    return material_betas

def debug_write_out_10x10_list(list_, string_):
    print("Writing out: ", string_, len(list_))
    write_string = ""
    count = 0
    for value in list_:
        write_string += str(value) + ","
        if count == 10:
            print("")
            count = 0
        count += 1
    print(string_, len(list_), write_string)

# In[6]:


### This function takes the gradient descent step. checks if the values stay between 0.99 and 0.01
### inputs:
### variables
### negative sensitivities
### step_size
def calculate_new_variables(variables, negative_sensitivities, step_size):
    new_variables = [float(variable_ + step_size * deriv_) for variable_, deriv_ in zip(variables, negative_sensitivities)]
    
    ### Checking if variables meet variable requirement
    new_new_variables = []
    for variable in new_variables:
        if variable > 1.0:
            variable = 0.99
        if variable < 0.0:
            variable = 0.01
        new_new_variables.append(variable)
        
    return new_new_variables

# In[7]:


#gradient_descent_scale(material_betas,
#                       debug_fake_tsunami_run = True,
#                       debug_print_betas = True,
#                       step_size_type = 'sqrt_n_mult#1',
#                       number_of_steps = 10,
#                       write_output = True,
#                       null_space_adj = True,
#                      materials = ["void", "fuel/moderator:25/75"])


# In[8]:


### Implementation of ADAM gradient descent
### https://arxiv.org/pdf/1412.6980.pdf

### Function which takes the list of beta values, checks to see if the values are above or below limits and sets them to
### those limits
def check_beta_values(betas, min_val = 0.01, max_val = 0.99):
    new_betas = []
    for val in betas:
        if val > max_val:
            val = max_val
        if val < min_val:
            val = min_val
        new_betas.append(val)
    return new_betas

def adjust_max_betas(betas,sensitivities,mass_adjust,typ='all'):
    #print(sum(betas))
    
    if typ=='all':
        beta_pair=np.zeros([len(betas),3])
        for i in range(len(betas)):
            beta_pair[i,0]=betas[i]
            beta_pair[i,1]=sensitivities[i]
            beta_pair[i,2]=i+1
            
        #print(beta_pair)
        beta_pair=sorted(beta_pair,key=operator.itemgetter(1))
        #print(beta_pair)
        adjust_slope=(mass_adjust/121)
        
        for i in range(len(betas)):
            #print(beta_pair[i][0])
            beta_pair[i][0]=beta_pair[i][0]-adjust_slope+adjust_slope*((i)/121)
            #print(beta_pair[i][0])
        #print(beta_pair)
        beta_pair=sorted(beta_pair,key=operator.itemgetter(2))
        beta_pairs=np.zeros([len(betas),3])
        for i in range(len(betas)):
            beta_pairs[i,0]=beta_pair[i][0]
            beta_pairs[i,1]=beta_pair[i][1]
            beta_pairs[i,2]=beta_pair[i][2]
        #print(sum(beta_pairs[:,0]))
        #print(beta_pairs[:,0])
        new_betas=beta_pairs[:,0]
        
    
    elif typ=='bottom':
        beta_pair=np.zeros([len(betas),3])
        for i in range(len(betas)):
            beta_pair[i,0]=betas[i]
            beta_pair[i,1]=sensitivities[i]
            beta_pair[i,2]=i+1
            
        #print(beta_pair)
        beta_pair=sorted(beta_pair,key=operator.itemgetter(1))
        #print(beta_pair)
        adjust_slope=(mass_adjust/(121-15))
        
        for i in range(len(betas)):
            #print(beta_pair[i][0])
            if i<(121-15):
                beta_pair[i][0]=beta_pair[i][0]-adjust_slope+adjust_slope*((i)/(121-15))
            else:
                beta_pair[i][0]=beta_pair[i][0]
            #print(beta_pair[i][0])
        #print(beta_pair)
        beta_pair=sorted(beta_pair,key=operator.itemgetter(2))
        beta_pairs=np.zeros([len(betas),3])
        for i in range(len(betas)):
            beta_pairs[i,0]=beta_pair[i][0]
            beta_pairs[i,1]=beta_pair[i][1]
            beta_pairs[i,2]=beta_pair[i][2]
        #print(sum(beta_pairs[:,0]))
        #print(beta_pairs[:,0])
        new_betas=beta_pairs[:,0]
        
    
    return new_betas 

def fix_mass(betas, target_mass, sensitivities, min_val = 0.01, max_val = 0.99, sticky_mass = True, typ = 'all'):
    current_mass = sum(betas)    
    adjustment_factor = target_mass / current_mass 
    
    new_betas = []
    if adjustment_factor>1:
        for _ in betas:
            if sticky_mass:
                if (_ == min_val):
                    new_betas.append(_)
                    continue
                elif (_ == max_val):
                    new_betas.append(_)
                    continue
    else:
        mass_adjust=current_mass-target_mass
        new_betas=adjust_max_betas(betas,sensitivities,mass_adjust,typ)
        
        
    return new_betas

    

### Function which takes betas, target_mass, whether to use "sticky values" (make highest and lowest values unchanged)
def fixed_mass_adjustment(betas, target_mass, sensitivities, typ, sticky_mass = True, debug=False, mass_round_dig = 5):
    if debug:
        print("Curent mass: {}, target: {}".format(sum(betas), target_mass))
    
    material_betas = check_beta_values(betas)
    while round(sum(material_betas), 5) != 61.0:
        material_betas = fix_mass(betas = material_betas,sensitivities=sensitivities, target_mass = 61.0, sticky_mass = sticky_mass,typ=typ)
        material_betas = check_beta_values(material_betas)
        #print(sum(material_betas))
        if debug:
            print(sum(material_betas))
    return material_betas 
  
def calculate_first_moment_vector(beta_1, first_moment_vector, beta_sensitivities):
    return [(beta_1 * first_mv  + (1 - beta_1) * deriv) 
                               for first_mv, deriv in zip(first_moment_vector, beta_sensitivities)]
    
def calculate_second_moment_vector(beta_2, second_moment_vector, beta_sensitivities):
    return [(beta_2 * second_mv + (1 - beta_2) * deriv**2) 
                                for second_mv, deriv in zip(second_moment_vector, beta_sensitivities)]




def transformation_function(x):
    """
    Transformation function applied to ADAM parameters. 
    
    This function allows the ADAM parameters to be unconstrained but can change 
    the behavior of the parameter domain going into tsunami.

    Parameters
    ----------
    x : TYPE
        DESCRIPTION.

    Returns
    -------
    y : TYPE
        DESCRIPTION.

    """
    
    y = np.exp(x)
    
    return y



# previously no sensitivity function,just returned same sensitivities as given from eval_w_tsunami
# =============================================================================
# def sensitivity_function(sensitivities,betas,current_mass,total_mass):
#     new_sensitivities=[]
# 
#     for i in range(len(betas)):
#         new_sensitivities.append(sensitivities[i])
#     return new_sensitivities
# =============================================================================

# now we have a penalty term for extremely small/large values of beta

def obj_derivative(derivative_df,parameter_df):
    """
    

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
    derivative_np = np.array(derivative_df)
    parameter_np = np.array(parameter_df)
    
    r = 100
    v = 2
    beta_limit = 20
    
# =============================================================================
#     new_sensitivities=[[],[]]
#     for mat in range(len(betas)):
#         for i in range(len(betas[mat])):
#             new_sensitivities[mat].append(sensitivities[mat][i] - (-r*v*np.exp(-v*(beta_limit+betas[mat][i])) + r*v*np.exp(v*(betas[mat][i]-beta_limit))))
# =============================================================================

    obj_derivative_np = derivative_np - (-r*v*np.exp(-v*(beta_limit+parameter_np)) + r*v*np.exp(v*(parameter_np-beta_limit)))
    obj_derivative_df = pd.DataFrame(obj_derivative_np, columns=np.array(parameter_df.columns))
    
    return obj_derivative_df




### Implementation of ADAM gradient descent
### inputs:
### initial material betas - list of values from 0-1.0 describing material
### debug_fake_tsunami_run - Boolean, if True running Tsunami is skipped
### debug_print_betas- Boolean, if true beta values are printed each step
### number_of_steps - Int, total number of steps to take with algo
### alpha_value - Float, Step size, set to default value
### beta_1 - Float, Decay rate for first moment, set to default value
### beta_2 - Float, Decay rate for second moment, set to default value
### epsilon - Float, Small value used to avoid division by zero, set to default value
### write_output - Boolean, True to write out output
### null_space_adj - Boolean, if True multiply penultimate values by null vector so that their changes sum to 0
### materials - List of materials void, (TCR) fuel and moderator. If you want a mixed material the form is:
###    "material 1 string/material 2 string:fraction material 1/fraction material 2"
def adam_gradient_descent_scale(parameter_df,
                           debug_print_all = False,
                           submit_tsunami_job = True,
                           stopping_value = 0.001,
                           number_of_steps = 10,
                           alpha_value = 0.1, 
                           beta_1 = 0.9,
                           beta_2 = 0.999,
                           epsilon = 1,
                           write_output = False,
                           write_output_string = "output.csv",
                           fix_mass_adjustment = True,
                           fix_mass_target = 'initial',
                           fix_mass_round_value = 5,
                           fix_mass_type='all',
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
    stopping_criteria = False
    parameters = parameter_df
       
    # only write new output csv files if we are starting at step 1
    if starting_step == 1:
        if write_output:
            with open('output.csv', 'w') as output_file:
                output_file.write("step, keff\n")
            with open('parameters.csv', 'w') as output_file:
                output_file.write("step, keff, fuel_betas_this_step [1x1936], mod_betas_this_step [1x1936]\n")
            with open('first_moments.csv', 'w') as output_file:
                output_file.write("step, keff, fuel_1st_moment_vectors_this_step [1x1936], mod_1st_moment_vectors_this_step [1x1936], fuel_2nd_moment_vectors_this_step [1x1936], mod_2nd_moment_vectors_this_step [1x1936]\n")
            with open('second_moments.csv', 'w') as output_file:
                output_file.write("step, keff, fuel_2nd_moment_vectors_this_step [1x1936], mod_2nd_moment_vectors_this_step [1x1936]\n")

       
    ### Main loop
    while steps < number_of_steps + 1:
        
        print("Step #:", steps)
        ### 
        tsunami_job_flag = 'tsunami_job_' + str(steps)
        
        # apply a transformation of variables to the domain
        transformed_parameters = parameter_df.apply(transformation_function)
         
        
        ### Evaluate with TSUNAMI
        keff, derivative_df = evaluate_with_Tsunami(transformed_parameters,
                                                             tsunami_job_flag = tsunami_job_flag,                    
                                                             submit_tsunami_job = submit_tsunami_job)
       
        # put through sensitivity of obj function - now we have a penalty on extremely small betas
        obj_derivative_df = obj_derivative(derivative_df, parameter_df)
       
        
        # edit the following to take a the obj_derivative_df and parameter dataframes
        first_moment_df = (beta_1 * first_moment_vector  + (1 - beta_1) * obj_derivative_df)
        second_moment_df = (beta_2 * second_moment_vector + (1 - beta_2) * obj_derivative_df**2) 
        first_moment_hat_df = (first_moment_df / (1 - beta_1**steps))
        second_moment_hat_df = (second_moment_df/ (1 - beta_2**steps))
       
        new_parameter_df = (parameter_df + (alpha_value * first_moment_hat_df) / (np.sqrt(second_moment_hat_df) + epsilon))
                             
            
        ### Writing out the output file   
        #! redo this to write steps and keff, betas, and moment vectors separately                                       
        if write_output:                                        # !!! these variable must be printed this way in order to start at step>1
            with open(write_output_string, 'a') as output_file:
                write_string = str(steps) + "," + str(keff)
                output_file.write(write_string + "\n")
            with open('parameters.csv', 'a') as par_file:
                np.savetxt(par_file, [np.array(parameter_df).flatten()], delimiter=',')
            with open('first_moments.csv', 'a') as fm_file:
                np.savetxt(fm_file, [np.array(first_moment_df).flatten()], delimiter=',')
            with open('second_moments.csv', 'a') as sm_file:
                np.savetxt(sm_file, [np.array(second_moment_df).flatten()], delimiter=',')
                
        # redefine parameters as new updated parameters before while loop
        parameter_df = new_parameter_df


# In[9]:


### Building initial parameter dataframe
#material_betas = build_initial_betas(1, 2, 'random', rand_min = 0.2, rand_max = 0.8)
pixels = 100


# =============================================================================
# starting criteria !!!
# assign starting_step as the step to be ran next (i.e if steps 1-20 have been ran starting_step=21)
# =============================================================================
starting_step = 1
Non_Uniform_Start = True


if starting_step == 1:
    
    parameter_vector = pd.DataFrame()
    parameter_vector['fuel'] = np.ones([pixels])
    parameter_vector['moderator'] = np.ones([pixels])

    
else:
     _ = 0
# =============================================================================
#     data = np.genfromtxt('parameters.csv', delimiter=',', skip_header=1, usecols=range(2,602))
#     material_betas_start=[[],[]]
#     material_betas_start[0] = data[-1, 0:pixels]
#     material_betas_start[1] = data[-1, pixels:pixels*2]  
#     
# # =============================================================================
# #     for mat in range(2):
# #         material_betas_start[mat] = [-20 if beta < -20 else beta for beta in material_betas_start[mat]]
# #         material_betas_start[mat] = [20 if beta > 20 else beta for beta in material_betas_start[mat]]
# # =============================================================================
#             
#     initialize_first_moment_vectors = [[],[]]; initialize_second_moment_vectors=[[],[]]
#     initialize_first_moment_vectors[0] = data[-1,200:300]; initialize_first_moment_vectors[1] = data[-1,300:400]
#     initialize_second_moment_vectors[0] = data[-1,400:500]; initialize_second_moment_vectors[1] = data[-1,500:600]
#     
#     # function inputs if initializing
#     initialize_boolean=True
#     initialize_file= 'tsunami_job_' + str(starting_step-1) +'.sdf'
#     initialize_betas=material_betas_start
# =============================================================================
    

#%%

# =============================================================================
# ### running adam gradient descent algorithm
# =============================================================================
adam_gradient_descent_scale(parameter_vector,
                       submit_tsunami_job=False,
                       debug_print_all = False,
                       alpha_value = 0.1,
                       beta_1=0.9,
                       number_of_steps = 3,
                       write_output = True,
                       epsilon = 1e-8,
                       fix_mass_adjustment = False,
                       fix_mass_target = 'initial',
                       fix_mass_round_value = 5,
                       
                       starting_step = starting_step,
                       
                       starting_first_moment = [],
                       starting_second_moment = [])


#%%
    
    
    
    
    
    
    
    
    
