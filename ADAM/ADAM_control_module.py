
#%%
import numpy as np
import pandas as pd
import random
import os
from ADAM import scale_interface
from ADAM import cluster_interface
import shutil


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
        scale_interface.create_tsunami_input(pdef.template_file, 'tsunami_job.inp', step, hex_number, pdef.generations, pdef.starting_fission_source_bool, pdef.run_shift)
        
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


#%%

def ADAM_update_parameter_df(pdef, parameter_df, obj_derivative_df, step):
    """
    Performs the ADAM update on the optimization parameters.

    The parameter_df variable is a panda DataFrame that holds all of the ADAM variables, that is:
    theta   :   optimization parameters
    mt    :   first moment
    vt    :   second moment
    Each of the above ADAM variables is housed in a vector with respect to each pixel. 
    Often it is the case that a single pixel will have multiple optimization parameters applied to different materials within it.
    In such a case, the ADAM variables become indexed vectors where the index in the data frame indicates which material that parameter will be
    applied to and the location in the vector indicates the geometric location of that pixel.

    Parameters
    ----------
    pdef : _type_
        _description_
    obj_derivative_df : _type_
        _description_
    step : _type_
        _description_

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """

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

    ### Redefine and write parameter dataframe
    parameter_df = pd.DataFrame()
    for i in range(pdef.max_parameters):
        temporary_df = pd.DataFrame({f'theta{i}':   new_theta.T[i],
                                        f'mt{i}':   mt_next.T[i],
                                        f'vt{i}':   vt_next.T[i]})
        parameter_df = pd.concat([parameter_df,temporary_df], axis=1)

    return parameter_df




#%%%

def run(step, pixel_array, pdef, output_filepath):
    """
    This is the primary control function for the ADAM algorithm.
    
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
        ### If we are at step 1: parameter_df = initial parameters given by user
        parameter_df = pdef.parameter_df
        ### Write output for starting step
        if pdef.write_output:
            if os.path.isdir('parameter_data'):
                shutil.rmtree('parameter_data')
                os.mkdir('parameter_data')
            else:
                os.mkdir('parameter_data')
            with open('parameter_data/output.csv', 'w') as output_file:
                output_file.write("step, keff\n")
            parameter_df.to_csv(f'parameter_data/parameters_{step}.csv', index=False)

        keff=0

    else:
        # If at step > 1:
        # Check for parameter data directory
        if os.path.isdir('parameter_data'):
            pass
        else:
            raise ValueError("Step>1 but no parameter_data is present. Cannot find directory parameter_data/")
        # Read parameters from previous step
        parameter_df = pd.read_csv(f'parameter_data/parameters_{step-1}.csv')


        ### Create a new MC input file
        Create_New_Input(pixel_array, parameter_df, pdef, step-1)


        ### Run the MC simulation
        if pdef.submit_job:
            cluster_interface.submit_jobs_to_necluster('tsunami_job')
            cluster_interface.wait_on_submitted_job('tsunami_job', output_filepath)
            cluster_interface.remove_unwanted_files()
            cluster_interface.check_outfiles_or_rerun('tsunami_job', output_filepath)

        ### Read output of MC simulation
        # outputs keff and writes derivative dfs to each respective pixel
        # derivatives are absolute but wrt to each nuclide within each region
        if pdef.run_shift:
            keff = scale_interface.read_total_sensitivity_by_nuclide("tsunami_job_ifp", pixel_array)
        else:
            keff = scale_interface.read_total_sensitivity_by_nuclide("tsunami_job", pixel_array)
        with open(output_filepath, 'a') as f:
            f.write(f"{step-1}, {keff}\n")


        ### Combine derivatives to get them wrt optimization parameters
        # wrt nuclides and region combined to derivatives wrt multiplication factors applied to compound for the entire region (chain rule)
        derivatives_wrt_parameters = []
        for each_pixel in pixel_array:
            each_pixel.combine_derivatives_wrt_nuclides(pdef.material_dict_base)
            each_pixel.combine_region_derivatives()
            derivatives_wrt_parameters.append(each_pixel.derivatives_wrt_parameters)
        derivative_df = pd.DataFrame(derivatives_wrt_parameters)
        # TODO: handle 0 given for derivatives
        # chain rule for transformation function to get derivatives wrt optimization parameters (this is where the objective function enters)
        obj_derivative_df = pdef.objective_derivative(derivative_df, parameter_df.filter(like='theta'), keff, step)
    

        ### Perform the ADAM update to get new parameters (remember, this is a minimization)
        parameter_df = ADAM_update_parameter_df(pdef, parameter_df, obj_derivative_df, step-1)

         ### Remove previous out files
        if pdef.submit_job:
            cluster_interface.remove_out_files()
            
        # write new parameters
        if pdef.write_output:
            parameter_df.to_csv(f'parameter_data/parameters_{step}.csv', index=False)
            with open('parameter_data/output.csv', 'a') as output_file:
                    output_file.write(f"{step-1}, {keff}\n")

    return keff

    

#%%