

#%%

import numpy as np
import pandas as pd

#%%  User input for problem setup


### Build initial parameter dataframe

# Define the number of pixels to be considered and the initial optimization parameters to use if starting from step 1.
# If not starting from step 1, assign starting_step as the step to be ran next (i.e if steps 1-20 have been ran starting_step=21)

class Problem_Definition:

    def __init__(self,  template_filename, material_dict_base,
                                        number_of_pixels, 
                                        region_definition,
                                        parameter_definition,
                                        generations, temperature,
                                        initial_parameter_df,
                                        max_parameters,

                                        transformation,
                                        obj_derivative,

                                        ADAM_Runtime_Parameters = {}
                                                                    ):
    
        ### init geometry
        self.number_of_pixels = number_of_pixels
        self.region_definition = region_definition
        self.parameter_definition = parameter_definition
        self.max_parameters = max_parameters

        ### init material df
        self.material_df_base = pd.DataFrame(material_dict_base)
        self.material_dict_base = material_dict_base

        ### init other parameters
        self.template_file = template_filename
        self.generations = generations
        self.temperature = temperature
        self.parameter_df = initial_parameter_df
        self.transformation = transformation
        self.obj_derivative = obj_derivative
        

            # self.Starting_Step()

        ADAM_Runtime_Parameters_default = { 'Write Output'  :   True, 
                                            'Build Input'   :   True, 
                                            'Submit Job'    :   True,
                                            'Run Geometry Check' : False,

                                            'beta 1'    :   0.9, 
                                            'beta 2'    :   0.999,
                                            'epsilon'   :   1e-8,
                                            'alpha'     :   1e-3    
                                                                        } 

        ### redefine options dictionary if any input options are given
        for parameter in ADAM_Runtime_Parameters:
            if parameter not in ADAM_Runtime_Parameters_default:
                raise ValueError('An unrecognized key was passed to the Problem Definition as an ADAM Runtime Parameter')
        ADAM_rtp = ADAM_Runtime_Parameters_default
        for old_parameter in ADAM_Runtime_Parameters_default:
            if old_parameter in ADAM_Runtime_Parameters:
                ADAM_rtp.update({old_parameter:ADAM_Runtime_Parameters[old_parameter]})
        self.ADAM_rtp = ADAM_rtp

        ### do options
        if self.ADAM_rtp['Run Geometry Check']:
            self.Check_Geometry()

        ### setup ADAM runtime parameters as attributes
        self.write_output = ADAM_rtp['Write Output']
        self.build_input = ADAM_rtp['Build Input']
        self.submit_job = ADAM_rtp['Submit Job']
        self.beta_1 = ADAM_rtp['beta 1']
        self.beta_2 = ADAM_rtp['beta 2']
        self.epsilon = ADAM_rtp['epsilon']
        self.alpha_value = ADAM_rtp['alpha']



    
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


    def transformation_function(self, x, ):
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
        # y = 1/(1+np.exp(-x))

        # user passed transformation function
        y = self.transformation(x)
        
        return y



    def objective_derivative(self, derivative_df, parameter_df, keff):
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
        

        ### calculate object derivative using user passed function
        obj_derivative_np = self.obj_derivative(parameter_np, derivative_np, Nbase_np, keff)

        ### put objective function derivatives into dataframe 
        obj_derivative_df = pd.DataFrame(obj_derivative_np, columns=np.array(parameter_df.columns))

        return obj_derivative_df


#