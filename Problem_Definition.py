

#%%

import numpy as np
import pandas as pd

#%%  User input for problem setup


### Build initial parameter dataframe

# Define the number of pixels to be considered and the initial optimization parameters to use if starting from step 1.
# If not starting from step 1, assign starting_step as the step to be ran next (i.e if steps 1-20 have been ran starting_step=21)

class Problem_Definition:

    def __init__(self, initialize_attributes, run_geometry_check):
    
        if initialize_attributes:
            self.ADAM_Runtime_Parameters()
            self.Geometry()
            self.Material_Definition()
            self.Starting_Step()
        if run_geometry_check:
            self.Check_Geometry()


    def ADAM_Runtime_Parameters(self):
        self.write_output = True
        self.build_input = True
        self.submit_job = False
        # self.template_file = 'spent_fuel_cask_template.inp'
        # self.template_file = 'tsunami_template_file_10x10.inp'
        # self.template_file = 'tsunami_template_file_44x44.inp'
        self.template_file = 'tsunami_template_11x11.inp'
        self.generations = 10
        self.temperature = 300

        # hyper parameters
        self.beta_1 = 0.9
        self.beta_2 = 0.999
        self.epsilon = 1e-8
        self.alpha_value = 1e-3

    def Starting_Step(self):
        self.starting_step = 1
        self.max_parameters = max(len(v) for k,v in self.parameter_definition.items())

        if self.starting_step == 1:

            parameter_df = pd.DataFrame()
            for i in range(self.max_parameters):
                if i == 0:
                    parameter_df[f'theta{i}'] = np.ones([self.number_of_pixels])*-1.0
                else:
                    parameter_df[f'theta{i}'] = np.ones([self.number_of_pixels])*-6
                parameter_df[f'mt{i}'] = np.zeros([self.number_of_pixels])
                parameter_df[f'vt{i}'] = np.zeros([self.number_of_pixels])
        else:
            pass
            
        self.parameter_df = parameter_df

    def Geometry(self):
            
        # self.number_of_pixels = 1936
        # self.number_of_pixels = 289
        self.number_of_pixels = 121

        ### Define geometric regions (repeating regions in this case) and the materials present within each
        # self.region_definition = {'rod':['fuel','moderator'], 'gap':['moderator'], 'clad':['zircalloy','moderator']}
        # self.region_definition = {'whole_pixel':['fuel','moderator']}
        self.region_definition = {'whole_pixel':['fuelmodmix']}

        ### Define the optimization parameters corresponding to the geometric region definition
        # self.parameter_definition = {'rod':['theta0','theta1'], 'gap':['theta1'], 'clad':['theta0','theta1']}
        # self.parameter_definition = {'whole_pixel':['theta0','theta1']}
        self.parameter_definition = {'whole_pixel':['theta0']}


    def Material_Definition(self):
        self.material_dict_base = {'fuel':{
                                        'u-235':8.59435E-04,
                                        'u-238':2.23686E-02,
                                        'o-16':4.64708E-02},
                        
                                'zircalloy':{'cr-52':6.98800E-05,
                                            'fe-56':1.42586E-04,
                                            'fe-58':4.38228E-07,
                                            'zr-94':7.37398E-03},
                                # 'zircalloy':{'cr-50':3.62373E-06,
                                #         'cr-52':6.98800E-05,
                                #         'cr-53':7.92383E-06,
                                #         'cr-54':1.97241E-06,
                                #         'fe-54':9.08312E-06,
                                #         'fe-56':1.42586E-04,
                                #         'fe-57':3.29292E-06,
                                #         'fe-58':4.38228E-07,
                                #         'zr-90':2.18292E-02,
                                #         'zr-91':4.76042E-03,
                                #         'zr-92':7.27640E-03,
                                #         'zr-94':7.37398E-03,
                                #         'zr-96':1.18798E-03,
                                #         'sn-112':4.64145E-06,
                                #         'sn-114':3.15810E-06,
                                #         'sn-115':1.62690E-06,
                                #         'sn-116':6.95739E-05,
                                #         'sn-117':3.67488E-05,
                                #         'sn-118':1.15893E-04,
                                #         'sn-119':4.11031E-05,
                                #         'sn-120':1.55895E-04,
                                #         'sn-122':2.21545E-05,
                                #         'sn-124':2.77051E-05},
                            
                                'moderator':{
                                            'o-16':3.3368E-02,
                                            'h-1':6.6733E-02} ,

                                # fuelmodmix replicates concentrations from p2
                                'fuelmodmix':{
                                            'u-234':5.0E-06*(1/4.4),
                                            'u-235':5.41E-04*(1/4.4),
                                            'u-236':2.0E-06*(1/4.4),
                                            'u-238':1.7263E-02*(1/4.4),
                                            'o-16':3.3368E-02*((1-1/4.4)+(1/4.4)),
                                            'h-1':6.6733E-02*(1-1/4.4),},

                                                            }

        self.material_df_base = pd.DataFrame(self.material_dict_base)
    
    def Check_Geometry(self):
        for region in self.region_definition:
            if region not in self.parameter_definition:
                raise ValueError("A region is defined in region_definition but not parameter_definition, please fix this before running ADAM")
        for region in self.parameter_definition:
            if region not in self.region_definition:
                raise ValueError("A region is defined in parameter_definition but not region_definition, please fix this before running ADAM")
        for region in self.region_definition:
            if len(self.region_definition[region]) != len(self.parameter_definition[region]):
                raise ValueError(f"The number of materials defined in region '{region}' do not match the number of parameters defined in that region")


        print("\nYou entered the following region, material, and parameter definitions:\n")
        for region in self.region_definition.keys():
            for material, parameter in zip(self.region_definition[f'{region}'], self.parameter_definition[f'{region}']):
                print(f'For region "{region}" the material "{material}" will be controlled by {parameter}')
        print()

        input("Press enter to confirm...\n")
        print(f"You are runnning the template {self.template_file} with {self.number_of_pixels} pixels\n")
        input("Press enter to confirm and run ADAM...")


    def transformation_function(self, x):
        """
        Transformation function applied to ADAM parameters to get multiplication factor applied to densities. 
        
        This function allows the ADAM parameters to be unconstrained but can change 
        the behavior of the parameter domain being input to TSUNAMI. This function is applied to the optimized parameter 
        DataFrame (rather than called) then the transformed parameters are multiplied by the base material density definition.

        Parameters
        ----------
        x : float or array-like
            Parameter being optimized by ADAM.

        Returns
        -------
        y : float or array-like
            Transformed parameter applied to material densities.

        """
        
        # exponential
        # y = np.exp(x)

        # sigmoid
        y = 1/(1+np.exp(-x))
        
        return y



    def objective_derivative(self, derivative_df, parameter_df):
        """
        Gets the derivative of the objective function given derivatives of k-effective with respect to the density factors (summed number density).

        Parameters
        ----------
        derivative_df : DataFrame
            DataFrame containing a column with derivatives $\frac{\deltak}{\deltaN_f}$ for each optimization parameter. 
            These are derivatives of k-effective with respect to the density factors applied to the base number densities, they are passed through this function to get derivatives of the objective
            function with respect to the theta optimization parameters. The column keys will correspond the the optimization parameter controlling that column and the index within a column 
            corresponds to pixel location.
        parameter_df : DataFrame
            DataFrame containing the theta parameters for the given step. This DataFrame has the same format as the derivative_df with columns 
            keyed by the optimization parameter they apply to.

        Returns
        -------
        obj_derivative_df : DataFrame
            DataFrame of the same format (column keys = optimization parameters for that column of pixels) containing derivatives of the objective function
            with respect to the optimization parameters "theta".

        """

        ### Get Nbase vector - Nbase summed over all regions/isotopes for each optimization parameter
        Nbase_region = {}
        for region in self.region_definition:
            for material, optimization_parameter in zip(self.region_definition[f'{region}'], self.parameter_definition[f'{region}']):
                
                Nbase_material = 0
                for isotope in self.material_dict_base[f'{material}'].keys():
                    Nbase_material += self.material_dict_base[f'{material}'][f'{isotope}']

                if optimization_parameter in Nbase_region:
                    Nbase_region[optimization_parameter].append(Nbase_material)
                else:
                    Nbase_region[optimization_parameter] = [Nbase_material]

        Nbase = []
        for optimization_parameter in Nbase_region:
            Nbase.append(sum(Nbase_region[optimization_parameter]))
        Nbase_np = np.array([Nbase]*len(parameter_df))


        ### cast into numpy arrays
        derivative_np = np.array(derivative_df)
        parameter_np = np.array(parameter_df)
        


        ### put through derivative of objective function

        # p3 original, exp transform with penalty
        # r = 100
        # v = 2
        # beta_limit = 20
        # obj_derivative_np = derivative_np - (-r*v*np.exp(-v*(beta_limit+parameter_np)) + r*v*np.exp(v*(parameter_np-beta_limit)))

        # p3 with sigmoid and no penalty - currently ignoring contant Nbase that should be multiplied by the second derivative
        # obj_derivative_np = -derivative_np * Nbase_np * (np.exp(-parameter_np)/(1+np.exp(-parameter_np)**2))
        
        # p2 with sigmoid and penalty for total mass
        r = 100
        v = 2
        limit = 61
        M = np.sum(1/(1+np.exp(-parameter_np))); assert len(parameter_np[0])==1, "Mass Constraint objective function must be updated if you want to use two parameters"
        dM_dtheta = np.exp(-parameter_np)/(1+np.exp(-parameter_np)**2)
        obj_derivative_np = - derivative_np*Nbase_np*dM_dtheta + r*np.exp(v*(M-limit))*v*dM_dtheta





        ### put objective function derivatives into dataframe 
        obj_derivative_df = pd.DataFrame(obj_derivative_np, columns=np.array(parameter_df.columns))

        return obj_derivative_df


#