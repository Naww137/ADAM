
#%%
import numpy as np
import pandas as pd
import random
import os
from ADAM import scale_interface


#%%
### Create a new input file
def Create_New_Input(pixel_array, parameter_df, pdef, step):
    """
    Creates a new MC Transport run file.

    The purpose of this function is to take the parameters being optimized by ADAM and convert them into
    an input file for the user's MC transport/sensitivity analysis of choice. 
    This function follows the following steps:
        1. Use transformation function defined in problem definition to convert the optimization parameters to density factors.
        2. Apply density factors to the base material definitions for each pixel in the pixel array.
        3. Create a MC Transport/sensitivity input file and fill the material definition with that of each pixel.

    Parameters
    ----------
    pixel_array : object array
        Array of pixel objects describing the problem geometry.
    parameter_df : DataFrame
        Contains all ADAM parameters, theta, mt, vt
    pdef : object
        User defined problem definition object.
    step : int
        Step of the Gradient descent algorithm currently being executed.
    """

    # apply a transformation of variables to all theta in ADAM parameter dataframe
    density_factor_df = parameter_df.filter(like='theta').apply(pdef.transformation_function)
    
    # Use parameter data frame to update the base material dictionary for each pixel in pixel array
    for i in range(len(pixel_array)):
        pixel_array[i].apply_density_factors(density_factor_df.iloc[i])    
    
    ### Building scale input
    
    if pdef.build_input:

        # generate random number seed
        random_number = random.randint(1152921504606846976,18446744073709551615)
        hex_number = str(hex(random_number))
        hex_number = hex_number [2:]
        
        # create input file from template file - no material data
        scale_interface.create_tsunami_input(pdef.template_file, 'tsunami_job.inp', step, hex_number, pdef.generations)
        
        # write each pixel's material data to the target input file
        with open('tsunami_job.inp', 'r') as f:
            readlines = f.readlines()
            f.close()
        with open('tsunami_job.inp', 'w') as f:
            for line in readlines:
                f.write(line)
                if line.startswith('read composition'):
                    for each_pixel in pixel_array:
                        f.write(scale_interface.material_string(each_pixel))
        
    else:
        print("Skipping building scale input file.")




#%% initialize pixel array




#%%%

def update(step, pixel_array, pdef):
    """
    Performs the ADAM gradient descent update on the optimization parameters.

    This is the primary control function for the algorithm. 

    The parameter_df variable is a panda DataFrame that holds all of the ADAM variables, that is:
        theta   :   optimization parameters
          mt    :   first moment
          vt    :   second moment
    Each of the above ADAM variables is housed in a vector with respect to each pixel. 
    Often it is the case that a single pixel will have multiple optimization parameters applied to different materials within it.
    In such a case, the ADAM variables become indexed vectors where the index in the data frame indicates which material that parameter will be
    applied to and the location in the vector indicates the geometric location of that pixel.
    
    The parameter_df variable is defined from the previous step (or from the problem definition if on step 1). 
    Then that sensitivities are read from the MC transport/sensitivity calculation and converted to derivatives
    with respect to the optimization parameters. The ADAM update is performed and the new parameters are saved.
    Finally, a new set of MC transport/sensitivity input files is created.

    Parameters
    ----------
    step : int
        Step of the Gradient descent algorithm currently being executed.
    pixel_array : object array
        Array of pixel objects describing the problem geometry.
    pdef : object
        User defined problem definition object.
    """

    if step == 1:
        # If we are at step 1:
                # parameter_df = initial parameters given by user
                # create csv files to save data
                # do not read sensitivities from output files

        parameter_df = pdef.parameter_df

        if pdef.write_output:

            if os.path.isdir('parameter_data'):
                pass
            else:
                os.mkdir('parameter_data')

            with open('parameter_data/output.csv', 'w') as output_file:
                output_file.write("step, keff\n")

            parameter_df.to_csv(f'parameter_data/parameters_{step}.csv', index=False)

        ### Create a new input file
        Create_New_Input(pixel_array, parameter_df, pdef, step)


    else:



        ### Read parameters from previous step
        parameter_df = pd.read_csv(f'parameter_data/parameters_{step-1}.csv')
        


        ### Pull out keff and sensitivities from previous job
        output_file = 'tsunami_job.out'
        #!!! if file does not exist throw error

        # outputs keff and writes derivative dfs to each respective pixel
        # derivatives are absolute but wrt to each nuclide within each region
        keff = scale_interface.read_total_sensitivity_by_nuclide(output_file, pixel_array)


        # combine derivatives wrt nuclides in each region to get derivatives wrt multiplication factors (chain rule)
        derivatives_wrt_parameters = []
        for each_pixel in pixel_array:
            each_pixel.combine_derivatives_wrt_nuclides(pdef.material_dict_base)
            each_pixel.combine_region_derivatives()
            derivatives_wrt_parameters.append(each_pixel.derivatives_wrt_parameters)
        derivative_df = pd.DataFrame(derivatives_wrt_parameters)
        
        # chain rule for transformation function to get derivatives wrt optimization parameters
        obj_derivative_df = pdef.objective_derivative(derivative_df, parameter_df.filter(like='theta'))
        

        ### perform the ADAM algorithm update (remember, this is a minimization)
        theta = np.array(parameter_df.filter(like='theta'))
        dObj_dtheta = np.array(obj_derivative_df)
        mt = np.array(parameter_df.filter(like='mt'))
        vt = np.array(parameter_df.filter(like='vt'))

        mt_next = (pdef.beta_1 * mt + (1 - pdef.beta_1) * dObj_dtheta)
        vt_next = (pdef.beta_2 * vt + (1 - pdef.beta_2) * dObj_dtheta**2) 
        mt_next_hat = (mt_next / (1 - pdef.beta_1**step))
        vt_next_hat = (vt_next/ (1 - pdef.beta_2**step))
        
        new_theta = (theta - (pdef.alpha_value * mt_next_hat) / (np.sqrt(vt_next_hat) + pdef.epsilon))


        # check for any NaNs
        if np.isnan(new_theta).any():
            print(step)
            raise ValueError("NaN in new_theta, step {step}")


        # redefine parameter dataframe
        parameter_df = pd.DataFrame()
        for i in range(pdef.max_parameters):
            temporary_df = pd.DataFrame({f'theta{i}':   new_theta.T[i],
                                            f'mt{i}':   mt_next.T[i],
                                            f'vt{i}':   vt_next.T[i]})
            parameter_df = pd.concat([parameter_df,temporary_df], axis=1)


        ### Save new parameters
        if pdef.write_output:
            parameter_df.to_csv(f'parameter_data/parameters_{step}.csv', index=False)
            with open('parameter_data/output.csv', 'a') as output_file:
                    output_file.write(f"{step}, {keff}\n")

        ### Create a new input file
        Create_New_Input(pixel_array, parameter_df, pdef, step)

    

# %%
