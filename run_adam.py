
from ADAM import ADAM_control_module
from ADAM import Problem_Definition
from ADAM import pixel
import pandas as pd
import numpy as np
import os

# %% Define geometry and materials

# number_of_pixels = 1936
# number_of_pixels = 400
# number_of_pixels = 289
number_of_pixels = 121

### Define geometric regions (repeating regions in this case) and the materials present within each
# region_definition = {'rod':['fuel','moderator'], 'gap':['moderator'], 'clad':['zircalloy','moderator']}
region_definition = {'whole_pixel':['fuel','moderator']}
# region_definition = {'whole_pixel':['fuelmodmix']}

### Define the optimization parameters corresponding to the geometric region definition
# parameter_definition = {'rod':['theta0','theta1'], 'gap':['theta1'], 'clad':['theta0','theta1']}
parameter_definition = {'whole_pixel':['theta0','theta1']}
# parameter_definition = {'whole_pixel':['theta0']}

material_dict_base = { 
                        'fuel':{
                                'u-235':8.59435E-04,
                                'u-238':2.23686E-02,
                                'o-16':4.64708E-02},
                
                        'zircalloy':{'o-16' : 2.71200E-04,
                                        'cr-52':6.98800E-05,
                                        'fe-56':1.42586E-04,
                                        'fe-58':4.38228E-07,
                                        'zr-94':7.37398E-03},
                        
                        'moderator':{
                                        'o-16':3.3368E-02,
                                        'h-1':6.6733E-02} ,


                        # 'fuel':{'u-234':5.0E-06,
                        #         'u-235':5.41E-04,
                        #         'u-236':2.0E-06,
                        #         'u-238':1.7263E-02,
                        #         'o-16':3.5622E-02},
                        
                        # fuelmodmix replicates concentrations from p2
                        'fuelmodmix':{
                                        'u-234':5.0E-06*(1/4.4),
                                        'u-235':5.41E-04*(1/4.4),
                                        'u-236':2.0E-06*(1/4.4),
                                        'u-238':1.7263E-02*(1/4.4),
                                        'o-16':3.3368E-02*((1-1/4.4)+(1/4.4)),
                                        'h-1':6.6733E-02*(1-1/4.4),},

                                                                                }

# %% Initial parameters
max_parameters = max(len(v) for k,v in parameter_definition.items())
initial_parameter_df = pd.DataFrame()
for i in range(max_parameters):
    if i == 0:
        initial_parameter_df[f'theta{i}'] = np.ones([number_of_pixels])*-0.2
    else:
        initial_parameter_df[f'theta{i}'] = np.ones([number_of_pixels])*2
    initial_parameter_df[f'mt{i}'] = np.zeros([number_of_pixels])
    initial_parameter_df[f'vt{i}'] = np.zeros([number_of_pixels])

# %% Define transformation and objective function derivative
def transformation_function(x):
    return 1/(1+np.exp(-x))

# Nbase_np and keff are passed in when this function is called, you don't have to use them
def obj_derivative(parameter_np, derivative_np, Nbase_np, keff):
    r = 1/100
    v = 1
    limit = 61*(4**2)
    M = np.sum(1/(1+np.exp(-parameter_np))); assert len(parameter_np[0])==1, "Mass Constraint objective function must be updated if you want to use two parameters"
    dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    obj_derivative_np = - derivative_np*Nbase_np*dM_dtheta + r*np.exp(v*(M-limit))*v*dM_dtheta

    # r=7
    # v=60
    # dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    # obj_derivative_np = dM_dtheta - v*r*np.exp((v*(1-keff)))*derivative_np*dM_dtheta

    ### put through derivative of objective function

    # p3 original, exp transform with penalty - Need to add Nbase
    # r = 100
    # v = 2
    # beta_limit = 20
    # obj_derivative_np = derivative_np - (-r*v*np.exp(-v*(beta_limit+parameter_np)) + r*v*np.exp(v*(parameter_np-beta_limit)))

    # p3 with sigmoid and no penalty
    # obj_derivative_np = -derivative_np * Nbase_np * (np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2)
    
    # p2 with sigmoid and penalty for total mass
    # r = 1/100
    # v = 1
    # limit = 61*(4**2)
    # M = np.sum(1/(1+np.exp(-parameter_np))); assert len(parameter_np[0])==1, "Mass Constraint objective function must be updated if you want to use two parameters"
    # dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    # obj_derivative_np = - derivative_np*Nbase_np*dM_dtheta + r*np.exp(v*(M-limit))*v*dM_dtheta

    # p2 inverse with sigmoid and penalty for k>=1
    # r = 100
    # v = 2
    # limit = 61
    # M = np.sum(1/(1+np.exp(-parameter_np))); assert len(parameter_np[0])==1, "Mass Constraint objective function must be updated if you want to use two parameters"
    # dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    # obj_derivative_np = - derivative_np*Nbase_np*dM_dtheta + r*np.exp(v*(M-limit))*v*dM_dtheta
    
    return obj_derivative_np

#%% Define optional ADAM runtime parameters and initialize a problem definition object

options = { 'Write Output'  :   True, 
            'Build Input'   :   True, 
            'Submit Job'    :   False,
            'Run Geometry Check' : False,

            'beta 1'    :   0.9, 
            'beta 2'    :   0.999,
            'epsilon'   :   1e-8,
            'alpha'     :   0.1    
                                        } 

generations = 10 
temperature = 300

pdef = Problem_Definition.Problem_Definition('tsunami_template_11x11.inp', material_dict_base,
                                                                            number_of_pixels, 
                                                                            region_definition,
                                                                            parameter_definition,
                                                                            generations, temperature,
                                                                            initial_parameter_df,
                                                                            max_parameters,

                                                                            transformation_function,
                                                                            obj_derivative,
                                                                            
                                                                            ADAM_Runtime_Parameters = options)


# %% Now run ADAM for a number of steps

### define path to runtime output file
output_filepath = os.path.join(os.getcwd(), "run_adam.outfile")

### Initialize pixel array
pixel_array = []
for i in range(pdef.number_of_pixels):
    pixel_array.append(pixel.pixel(pdef.region_definition, pdef.parameter_definition, pdef.material_df_base, i+1, pdef.temperature))

### Input starting step
step = 1
if step == 1:
    with open(output_filepath, 'w') as f:
        f.write("Welcome to ADAM!\nYou have just started running, this file will print updates for each step\n")
else:
    with open(output_filepath, 'a') as f:
        f.write(f"ADAM was interrupted, retarting from step {step}\n")


### Run ADAM 
while step < 600:

    keff = ADAM_control_module.run(step, pixel_array, pdef, output_filepath)

    step += 1



