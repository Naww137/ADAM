#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 08:55:17 2022

@author: noahwalton
"""

import os
import pandas as pd






def read_keff(tsunami_file_string):
    """
    Reads a SCALE.out file to pull the k-eff and statistical uncertainty.

    Parameters
    ----------
    tsunami_file_string : string
        Filename of the SCALE.out file to be read.

    Returns
    -------
    keff : float
        k-eigenvalue of the system.
    unc : float
        Statistical uncertainty in the k-eigenvalue.

    """
    with open(tsunami_file_string, 'r') as f:
        for line in f:
            if "best estimate system k-eff" in line:
                splitline = line.split()
                keff = float(splitline[5])
                unc = float(splitline[9])
    return keff, unc




def read_total_sensitivity_by_nuclide(tsunami_file_string, pixel_array):
    """
    Reads out energy integrated total sensitivities for each nuclide for each material id.

    This function reads sensitivity data from the SDF, but needs to read the output file as well in order to get atom densities.
    A more simple implementation is to also read sensitivities from the output file, but a weird bug in TSUNAMI causes these not to always be written 
    correctly. See the old function "read_total_sensitivity_by_nuclide_OUTPUTFILEONLY" in this scale_interface module for the more simple implemntation.
    Perhaps the TSUNAMI bug will be fixed in the future.

    Parameters
    ----------
    tsunami_file_string : string
        Basename of the of the SCALE outfiles file to read.
    pixel_array : object array
        Array of pixel objects describing the problem geometry.

    Returns
    -------
    data : nested dict
        Nested dictionary where first set of keys are scale material id numbers, then second set of keys are nuclides.
        For a given material/isotope key-set, 4 values are given as a tuple: (sensitivity, uncertainty, atom_density, absolute_sensitivity)

    """
    data = {}
    with open(f'{tsunami_file_string}.sdf', 'r') as f:
        in_data = False
        line_count = 0
        for line in f:
            
            if line_count == 3:
                if "k-eff" not in line:
                    raise ValueError("k-eff not found in SDF")
                splitline = line.split()
                keff = float(splitline[0])
                k_unc = float(splitline[2])
            
            if "total" in line:
                in_data = True
                isotope = line.split()[0]
                in_data_line_count = 0
                continue

            if in_data:
        
                if in_data_line_count == 0:
                    splitline = line.split()
                    mixture_id = abs(float(splitline[0]))
                if in_data_line_count == 2:
                    splitline = line.split()
                    sensitivity = float(splitline[0])
                    uncertainty = float(splitline[1])

                if in_data_line_count == 3:
                    in_data = False
                    if mixture_id == 0:     # mixture id==0 is for system interated sensitivity, we don't need this yet
                        pass
                    else:
                        if mixture_id not in data:
                            data[mixture_id] = {}
                        data[mixture_id][isotope] = [sensitivity, uncertainty] #, atom_density, absolute_sensitivity)

                in_data_line_count += 1

            line_count += 1


    ### Now put dictionary data from scale into pixels in pixel array
    for each_pixel in pixel_array:
        each_pixel.sensitivity_data_by_nuclide = {}
        for i, region in enumerate(each_pixel.region_definition):
            scale_material_id = each_pixel.pixel_id*10 + i

            # scale relative sensitivities by atom_dens/keff
            for isotope, atom_dens in each_pixel.updated_region_materials[region]['combined'].loc[each_pixel.updated_region_materials[region]['combined'] != 0].items():
                absolute_sensitivity = data[scale_material_id][isotope][0]*atom_dens/keff
                data[scale_material_id][isotope].extend([atom_dens, absolute_sensitivity])

            each_pixel.sensitivity_data_by_nuclide[region] = data[scale_material_id]


    return keff
    


# =======================================================================================

def get_combined_derivatives(pixel_array, material_dict_base):
    """
    Combines nuclide derivatives for each region and then for each parameter within each pixel in the pixel array.
    
    See Also
    --------
    pixel.combine_derivatives_wrt_nuclides


    Parameters
    ----------
    pixel_array : TYPE
        DESCRIPTION.
    material_dict_base : TYPE
        DESCRIPTION.

    Returns
    -------
    DataFrame
        DataFrame of sensitivities wrt optimization parameters.

    """
    derivatives_wrt_parameters = []
    for each_pixel in pixel_array:
        each_pixel.combine_derivatives_wrt_nuclides(material_dict_base)
        each_pixel.combine_region_derivatives()
        derivatives_wrt_parameters.append(each_pixel.derivatives_wrt_parameters)
        
    return pd.DataFrame(derivatives_wrt_parameters)
    



def create_tsunami_input(template_file, input_file, step, hex_number, generations, starting_fission_source_bool, run_shift):
    """
    Creates a tsunami input file from the template file with a random number seed, adds number of generations and removes read source input if on the first step.

    Parameters
    ----------
    template_file : string
        Filename of template file.
    input_file : string
        Filename of input file to create.
    steps : int
        Step number in the gradient descent algorithm.
    hex_number : float
        Python generated random number seed.
    generations : int
        Monte Carlo generations to be run in each step.
    starting_fission_source_bool : bool
        Boolean logic to utilize the previous steps fission distribution as the starting distribution for the next.

    Returns
    -------
    None.

    """
    
    with open(template_file, 'r') as f:
        readlines = f.readlines()
        f.close()
    
    if starting_fission_source_bool: 
        if run_shift:
            raise ValueError('Cannot run shift with a starting fission source - must update template for this feature to be compatible with shift')
            
        with open(input_file, 'w') as f:
            if step == 1:
                for line in readlines[3:]:
                    if line.startswith('read start'):
                        pass
                    elif line.startswith('nst=9'):
                        pass
                    elif line.startswith('mss=fissionSource.msl'):
                        pass
                    elif line.startswith('end start'):
                        pass

                    elif line.startswith('nsk=1'):
                        f.write('nsk=10\n')                   
                    elif line.startswith('gen='):
                        f.write(f'gen={generations+10}\n')                    
                    elif line.startswith('rnd='):
                        f.write(f'rnd={hex_number}\n')                    
                    else:
                        f.write(line)
            else:
                for line in readlines:
                    if line.startswith('rnd='):
                        f.write(f'rnd={hex_number}\n')                  
                    elif line.startswith('gen='):
                        f.write(f'gen={generations}\n')
                    else:
                        f.write(line)
            
    elif not starting_fission_source_bool: 

        with open(input_file, 'w') as f:
            for line in readlines[3:-12]:
                if line.startswith('read start'):
                    pass
                elif line.startswith('nst=9'):
                    pass
                elif line.startswith('mss=fissionSource.msl'):
                    pass
                elif line.startswith('end start'):
                    pass
                elif line.startswith('cds='):
                    pass
                elif line.startswith('scd='):
                    pass

                elif line.startswith('=tsunami-3d-k5'):
                    if run_shift:
                        f.write(f'{line}-shift\n')
                    else:
                        f.write(line)

                elif line.startswith('nsk=1'):
                    f.write('nsk=10\n')                   
                elif line.startswith('gen='):
                    f.write(f'gen={generations+10}\n')                    
                elif line.startswith('rnd='):
                    f.write(f'rnd={hex_number}\n')                    
                else:
                    f.write(line)
    

def material_string(pixel):
        """
        Creates the updated material string attribute for pixel object.
        
        This attribute is a string specific to the pixel object it belongs to corresponding to a SCALE material composition input.
        The material id format is as follows, the first 4 digits represent the pixel, the last digit, or digit with magnitude 1e0, 
        represents the region within the pixel and will repeat within each pixel.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        SCALE composition material string for the given pixel.

        """
        
        material_string = ''
        
        if hasattr(pixel, 'updated_region_materials'):
            pass
        else:
            raise ValueError("Pixel does not have updated_region_materials attribute, please run 'apply_optimization_parameters_to_material_definitions' before writing material string")
            
        
        # loop through regions in the pixel
        region_id = 0
        for region_key, region_df in pixel.updated_region_materials.items():
            
            material_string += f"' {region_key}\n"
            material_id = (pixel.pixel_id*10)+region_id
            
            region_df_remove_zeros = region_df.loc[region_df.combined != 0]
            for isotope_key, isotope_value in region_df_remove_zeros.combined.iteritems():
                material_string += f"{isotope_key} {material_id} 0 {isotope_value} {pixel.temp} end\n"
        
        
            region_id += 1
            if region_id > 9:
                raise ValueError("Cannot have more than 10 material regions per pixel")

        return material_string

















#%% Unused functions

def read_total_sensitivity_by_nuclide_OUTPUTFILEONLY(tsunami_file_string, pixel_array):
    """
    Reads out energy integrated total sensitivities for each nuclide in each material id region.

    This function is no longer used because of a weird bug in TSUNAMI where every now and then a random material sensitivity won't write to the
    Total Sensitivity Coefficients by Nuclide  table in the output file. \n
    The updated function in this module that is actually used in ADAM reads sensitivites from the SDF file then atom densities from the output file. 
    This, however, is a more complicated procedure. The weird bug in TSUNAMI, was noticed to only occur when a material id's 
    sensitivites are all zero! This is evident of a deeper bug, hoever, if this more simple function for reading sensitivities from the output file is desired,
    include some logic that sets sensitivities to zero for all isotopes in a given material ID if that ID id not found in the output file.
    

    Parameters
    ----------
    tsunami_file_string : string
        Filenmae of the SCALE.out file to read.

    Returns
    -------
    data : nested dict
        Nested dictionary where first set of keys are scale material id numbers, then second set of keys are nuclides.
        For a given material/isotope key-set, 4 values are given as a tuple: (sensitivity, uncertainty, atom_density, absolute_sensitivity)

    """
    data = {}
    did_not_find_keff = True
    did_not_find_sensitivities = True
    with open(tsunami_file_string, 'r') as f:
        in_data = False
        skiplines = 0
        for line in f:
            
            # read out k-effective, occurs before sensitivities
            if "best estimate system k-eff" in line:
                splitline = line.split()
                keff = float(splitline[5])
                unc = float(splitline[9])
                did_not_find_keff = False
                
            # read out sensitivities
            if "Total Sensitivity Coefficients by Nuclide" in line:
                in_data = True
                did_not_find_sensitivities = False
                
                # throw error if keff not found before trying to use the keff variable
                if did_not_find_keff:
                    raise ValueError(f"No k-eff found, it seems that KENO did not complete for {tsunami_file_string}.") 

                continue
            
            if in_data:
                skiplines += 1
                
                if skiplines > 4:
                    
                    if len(line.strip()) == 0 :
                        in_data = False
                        continue
                    
                    splitline = line.split()
                    
                    mixture_id = float(splitline[0])
                    isotope = splitline[1]
                    atom_density = float(splitline[2])
                    sensitivity = float(splitline[3])
                    uncertainty = float(splitline[5])
                    absolute_sensitivity = sensitivity*atom_density/keff
                    
                    if mixture_id not in data:
                        data[mixture_id] = {}
                    data[mixture_id][isotope] = (sensitivity, uncertainty, atom_density, absolute_sensitivity)
        
        # throw error if keff or sensitivities were not found
        if did_not_find_keff:
                    raise ValueError(f"No k-eff found, it seems that KENO did not complete for {tsunami_file_string}.")   
        if did_not_find_sensitivities:
            raise ValueError(f"No sensitivities found, it seems that SAMS did not complete for {tsunami_file_string}.")


    ### Now parse dictionary data from scale into pixels in pixel array
    for each_pixel in pixel_array:
        each_pixel.sensitivity_data_by_nuclide = {}
        for i, region in enumerate(each_pixel.region_definition):
            scale_material_id = each_pixel.pixel_id*10 + i
            each_pixel.sensitivity_data_by_nuclide[region] = data[scale_material_id]

    return keff

def read_total_sensitivity_by_mixture(tsunami_file_string):
    """
    Reads a SCALE.out file and parses out the sensitivities by mixture.
    
    Because these sensitivities are coming directly from the SCALE.out file, they are relative, S = sig/k * dk/dsig
    See the theory in the SCALE manual or research papers associated with this work.

    Parameters
    ----------
    tsunami_file_string : string
        Filename of the SCALE.out file to be read.

    Returns
    -------
    DataFrame
        DataFrame with columns mixture_id, sensitivity, and uncertainty. The sensitivity is relative, see theory. The uncertainty is 
        absolute with respect to the sensitivity and due to the statistical nature of the Monte Carlo problem.

    """
    data = []
    with open(tsunami_file_string, 'r') as f:
        in_data = False
        skiplines = 0
        for line in f:
            if "Total Sensitivity Coefficients by Mixture" in line:
                in_data = True
                continue
            
            if in_data:
                skiplines += 1
                
                if skiplines > 4:
                    
                    if len(line.strip()) == 0 :
                        in_data = False
                        continue
                    
                    splitline = line.split()
                    mixture_id = float(splitline[0])
                    sensitivity = float(splitline[1])
                    uncertainty = float(splitline[3])
                    data.append((mixture_id, sensitivity, uncertainty))
                    
    return pd.DataFrame(data, columns=['mixture_id', 'sensitivity', 'uncertainty'])
    


### Tsunami File function section
def parse_sdf_file_into_dict(tsunami_file_string):
    """
    Parses the SDF file to get energy integrated sensitivities.
    
    This is a legacy function and will not work with the current ADAM implementation. The current implementation reads
    energy integrated sensitivities from the .out file. The .sdf file contains energy binned sensitivity data as well as energy integrated.
    This function was kept in case the user wishes to update the algorithm to read sensitivities from .sdf files rather than the output. 

    Parameters
    ----------
    tsunami_file_string : TYPE
        DESCRIPTION.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    data_dict : TYPE
        DESCRIPTION.

    """
    
    raise ValueError("SDF file parsing is a legacy function, needs to be updated for the current ADAM algorithm. See documentation.")
    
    tsunami_file = open(tsunami_file_string, 'r')
    in_data = False
    data_dict = collections.OrderedDict()
    for line in tsunami_file:
        line = line.strip()
        if line == "0.000000E+00  0.000000E+00      0      0":
            continue
        if 'total' in line:
            in_data = True
            line = line.strip()

            line_split = line.split('total')
            isotope = line_split[0].strip()

            in_data_count = 0
            continue

        if in_data:
            # print(line.strip())
            if in_data_count == 0:
                line_split = line.split(' ')
                material = line_split[0]

            if in_data_count == 1:
                line_split = line.split('  ')
                sensitivity = line_split[0]
                uncert = line_split[1]

            in_data_count += 1
            if in_data_count == 2:
                in_data = False
                # print(material, isotope, sensitivity, uncert)
                if material not in data_dict:
                    data_dict[material] = collections.OrderedDict()
                data_dict[material][isotope] = collections.OrderedDict()
                data_dict[material][isotope]['sensitivity'] = sensitivity
                data_dict[material][isotope]['uncertainty'] = uncert
    return data_dict
