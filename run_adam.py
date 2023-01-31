
from ADAM import ADAM_control_module
from ADAM import Problem_Definition
from ADAM import pixel
import pandas as pd
import numpy as np
import os

# %% Define geometry and materials

# number_of_pixels = 1936
# number_of_pixels = 400
number_of_pixels = 289
# number_of_pixels = 121
# number_of_pixels = 1

### Define geometric regions (repeating regions in this case) and the materials present within each
region_definition = {'rod':['fuel','moderator'], 'gap':['moderator'], 'clad':['zircalloy','moderator']}
# region_definition = {'left':['fuel'], 'right':['moderator']}
### region_definition = {'whole_pixel':['fuel','moderator']}
### region_definition = {'whole_pixel':['fuelmodmix']}

### Define the optimization parameters corresponding to the geometric region definition
parameter_definition = {'rod':['theta0','theta1'], 'gap':['theta1'], 'clad':['theta0','theta1']}
# parameter_definition = {'left':['theta0'], 'right':['theta1']}
# parameter_definition = {'whole_pixel':['theta0','theta1']}
# parameter_definition = {'whole_pixel':['theta0']}

material_dict_base = { 
                        'fuel':{
                                'u-235':8.59435E-04,
                                'u-238':2.23686E-02,
                                'o-16':4.64708E-02},
                
                        # 'zircalloy':{'o-16' : 2.71200E-04,
                        #                 'cr-52':6.98800E-05,
                        #                 'fe-56':1.42586E-04,
                        #                 'fe-58':4.38228E-07,
                        #                 'zr-94':7.37398E-03},
                        'zircalloy':{'o-16' : 2.71200E-04,
                                'cr-50':3.62373E-06,
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
max_parameters = len(np.unique(np.concatenate([np.array(v) for k,v in parameter_definition.items()]).ravel()))
# starting_thetas = pd.read_csv('./starting_thetas.csv')

initial_parameter_df = pd.DataFrame()
for i in range(max_parameters):
    if i == 0:
        initial_parameter_df[f'theta{i}'] = np.ones([number_of_pixels])*0  # np.random.default_rng().integers(-3,3,number_of_pixels)  #
        # initial_parameter_df[f'theta{i}'] = starting_thetas.theta0
    else:
        initial_parameter_df[f'theta{i}'] =  np.ones([number_of_pixels])*0 #np.random.default_rng().integers(-3,3,number_of_pixels)  #
        # initial_parameter_df[f'theta{i}'] = starting_thetas.theta1
    initial_parameter_df[f'mt{i}'] = np.zeros([number_of_pixels])
    initial_parameter_df[f'vt{i}'] = np.zeros([number_of_pixels])

# %% Define transformation and objective function derivative
def transformation_function(x):
    return 1/(1+np.exp(-x))

# Nbase_np and keff are passed in when this function is called, you don't have to use them
def obj_derivative(parameter_np, derivative_np, Nbase_np, keff, step):
    # r = 1/100
    # v = 1
    # limit = 61*(4**2)
    # M = np.sum(1/(1+np.exp(-parameter_np))); assert len(parameter_np[0])==1, "Mass Constraint objective function must be updated if you want to use two parameters"
    # dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    # obj_derivative_np = - derivative_np*Nbase_np*dM_dtheta + r*np.exp(v*(M-limit))*v*dM_dtheta

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
    
    # sigmoid with saddle function penalty (crit safety problem)
    dP_dxy = (4*parameter_np-2)*1e-5
    dP_dyx = dP_dxy
    dP_dyx[:,[1,0]] = dP_dxy[:,[0,1]] #reverse col for dp
    dxy_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2
    dP_dtheta = dP_dyx*dxy_dtheta

    dk_dtheta = -derivative_np * (np.exp(-parameter_np)/(1+np.exp(-parameter_np))**2) 
    obj_derivative_np = dk_dtheta + dP_dtheta

    np.save(f'./parameter_data/dP_dtheta_step{step}.npy',dP_dtheta)
    np.save(f'./parameter_data/dk_dtheta_step{step}.npy',dk_dtheta)
    
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

options = { 'Write Output'  :   False, 
            'Build Input'   :   True, 
            'Submit Job'    :   False,
            'Run Geometry Check' : False,
            'Use Starting Fission Source' : False,
            'Run Shift' : True ,

            'beta 1'    :   0.9, 
            'beta 2'    :   0.999,
            'epsilon'   :   1e-8,
            'alpha'     :   0.1    
                                        } 

generations = 10 
temperature = 300

pdef = Problem_Definition.Problem_Definition('spent_fuel_cask_single_cell_template.inp', material_dict_base,
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
while step < 3:

    keff = ADAM_control_module.run(step, pixel_array, pdef, output_filepath)

    step += 1



