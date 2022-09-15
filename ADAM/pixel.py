

from ADAM import derivatives
import pandas as pd



class pixel:
    """
    Summary of pixel class.

    More on pixel class.


    Methods
    -------
    apply_optimization_parameters_to_material_definitions: 
        Applies the optimization parameters to the base material values.
    write_material_string:
        Creates the updated material string attribute.
    combine_derivatives_wrt_nuclides:
        Combine derivatives for each nuclide in a material.
    combine_region_derivatives:
        Combines derivatives for each region with a given optimization parameter.
    """
    
    def __init__(self, region_definition, parameter_definition, material_df_base, pixel_id, temperature):
        
        self.region_definition = region_definition
        self.parameter_definition = parameter_definition
        self.material_df_base = material_df_base
        self.pixel_id = pixel_id
        self.temp = temperature
        
        # to replace material key with parameter key
        self.par_def = {}
        for region in region_definition:
            for i in range(len(region_definition[f'{region}'])):
                self.par_def[f'{region_definition[region][i]}'] = parameter_definition[f'{region}'][i]
                
                
        
    def apply_density_factors(self, density_factors):
        """
        Generates updated isotopic concentration values for each region within a pixel.
        
        The updated_materials_definition attribute for the pixel object is created. This dataframe is created by multiplying the density 
        factors (transformed optimization parameters) to the base isotopic concentrations (material_df_base).
        
        .. math:: 
            N_{updated} = N_{base}*T(\\theta)

        Where T is the user defined transformation function.

        Parameters
        ----------
        density_factors : DataFrame
            Transformed optimization parameters, aka density factors.

        Returns
        -------
        None.

        """
        
        # create the updated region materials dataframe and replace column material keys with the parameter key to be applied
        self.updated_region_materials = dict.fromkeys(self.region_definition.keys())
        for region in self.region_definition:
            self.updated_region_materials[f'{region}'] = self.material_df_base[self.region_definition[f'{region}']].rename(columns=self.par_def)

        # apply multiplier
        for region in self.region_definition:
            for material in self.updated_region_materials[f'{region}']:
                self.updated_region_materials[f'{region}'][f'{material}'] = self.updated_region_materials[f'{region}'][f'{material}'] * density_factors[f'{material}']
            
        # combine like isotopes 
        for region in self.region_definition:
            self.updated_region_materials[f'{region}']['combined'] = self.updated_region_materials[f'{region}'].sum(axis=1)
    

                
    
    def combine_derivatives_wrt_nuclides(self, material_dict_base):
        """
        Combines absolute sensitivities/derivatives with respect to each nuclide within each region of the pixel object.
        
        This function goes into the 

        Parameters
        ----------
        material_dict_base : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        if hasattr(self, 'sensitivity_data_by_nuclide'):
            pass
        else:
            raise ValueError("Pixel does not have sensitivity_data_by_nuclide attribute, please run 'pixel_array_functions.get_nuclide_sensitivites_for_each_pixel' before attempting to combine derivatives")
        
        
        for region in self.region_definition:
            temporary_dictionary = {}
            for material, optimization_parameter in zip(self.region_definition[f'{region}'], self.parameter_definition[f'{region}']):
                
                absolute_sensitivity_by_parameter = {}
                for isotope in material_dict_base[f'{material}'].keys():
                    absolute_sensitivity_by_parameter[isotope] = self.sensitivity_data_by_nuclide[region][isotope][3]
                
                if optimization_parameter in temporary_dictionary:
                    temporary_dictionary[optimization_parameter].append(derivatives.combine_nuclide_derivatives(absolute_sensitivity_by_parameter))
                else:
                    temporary_dictionary[optimization_parameter] = [derivatives.combine_nuclide_derivatives(absolute_sensitivity_by_parameter)]
                
        self.derivatives_wrt_parameters_per_region = pd.DataFrame(temporary_dictionary, index=list(self.region_definition.keys()))
    
    
    
    def combine_region_derivatives(self):
        """
        Combines the derivatives across regions for the same parameters given the function for bomining derivatives in the objective_function_definition module.

        Returns
        -------
        None.

        """
        self.derivatives_wrt_parameters = self.derivatives_wrt_parameters_per_region.apply(derivatives.combine_region_derivatives)
    
    