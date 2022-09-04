
class pixel:
    
    def __init__(self, region_definition, parameter_definition, material_df_base, pixel_id):
        
        self.region_definition = region_definition
        self.parameter_definition = parameter_definition
        self.material_df_base = material_df_base
        self.pixel_id = pixel_id
        
        # to replace material key with parameter key
        self.par_def = {}
        for region in region_definition:
            for i in range(len(region_definition[f'{region}'])):
                self.par_def[f'{region_definition[region][i]}'] = parameter_definition[f'{region}'][i]
                
                
        
    def get_updated_material_definition(self, parameters):
        """
        Generates updated isotopic concentration values for each region within a pixel.

        Parameters
        ----------
        parameters : DataFrame
            DESCRIPTION.

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
    
    
    def write_material_string_for_single_pixel(self, temp):
        
        material_string = ''
        
        if hasattr(self, 'updated_region_materials'):
            _=0
        else:
            raise ValueError("pixel does not have updated_region_materials attribute, please run 'get_updated_material_definition' before writing material string")
            
        
        # loop through regions in the pixel
        region_id = 0
        for region_key, region_df in self.updated_region_materials.items():
            
            material_string += f"' {region_key}\n"
            material_id = (self.pixel_id*10)+region_id
            
            region_df_remove_zeros = region_df.loc[region_df.combined != 0]
            for isotope_key, isotope_value in region_df_remove_zeros.combined.iteritems():
                material_string += f"{isotope_key} {material_id} 0 {isotope_value} {temp} end\n"
        
        
            region_id += 1
            if region_id > 9:
                raise ValueError("Cannot have more than 10 material regions per pixel")

        self.material_string = material_string
                
    
    
    
    
    
    
    