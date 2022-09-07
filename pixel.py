

import problem_definition
import pandas as pd




class pixel:
    
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
                
                
        
    def apply_optimization_parameters_to_material_definitions(self, parameters):
        """
        Generates updated isotopic concentration values for each region within a pixel given the optimization parameters.
        
        The updated_materials_definition attribute for the pixel object is created. This dataframe is created by applying the optimization 
        parameters to the base material definition, i.e. updated materials = base materials * parameters

        Parameters
        ----------
        parameters : DataFrame
            Parameters being optimized by ADAM.

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
                self.updated_region_materials[f'{region}'][f'{material}'] = self.updated_region_materials[f'{region}'][f'{material}'] * parameters[f'{material}']
            
        # combine like isotopes 
        for region in self.region_definition:
            self.updated_region_materials[f'{region}']['combined'] = self.updated_region_materials[f'{region}'].sum(axis=1)
    
    
    def write_material_string(self):
        """
        Creates the updated material string attribute for pixel object.
        
        This attribute is a string specific to the pixel object it belongs to and corresponds to a SCALE material composition input.
        The material id format is as follows, the first 4 digits represent the pixel, the last digit, or digit with magnitude 1e0, 
        represents the region within the pixel and will repeat within each pixel.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        material_string = ''
        
        if hasattr(self, 'updated_region_materials'):
            pass
        else:
            raise ValueError("Pixel does not have updated_region_materials attribute, please run 'apply_optimization_parameters_to_material_definitions' before writing material string")
            
        
        # loop through regions in the pixel
        region_id = 0
        for region_key, region_df in self.updated_region_materials.items():
            
            material_string += f"' {region_key}\n"
            material_id = (self.pixel_id*10)+region_id
            
            region_df_remove_zeros = region_df.loc[region_df.combined != 0]
            for isotope_key, isotope_value in region_df_remove_zeros.combined.iteritems():
                material_string += f"{isotope_key} {material_id} 0 {isotope_value} {self.temp} end\n"
        
        
            region_id += 1
            if region_id > 9:
                raise ValueError("Cannot have more than 10 material regions per pixel")

        self.material_string = material_string
                
    
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
                    temporary_dictionary[optimization_parameter].append(problem_definition.combine_nuclide_derivatives(absolute_sensitivity_by_parameter))
                else:
                    temporary_dictionary[optimization_parameter] = [problem_definition.combine_nuclide_derivatives(absolute_sensitivity_by_parameter)]
                
        self.derivatives_wrt_parameters_per_region = pd.DataFrame(temporary_dictionary, index=list(self.region_definition.keys()))
    
    
    
    def combine_region_derivatives(self):
        """
        Combines the derivatives across regions for the same parameters given the function for bomining derivatives in the problem_definition module.

        Returns
        -------
        None.

        """
        self.derivatives_wrt_parameters = self.derivatives_wrt_parameters_per_region.apply(problem_definition.combine_region_derivatives)
    
    