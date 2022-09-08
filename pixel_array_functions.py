#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 10:59:10 2022

@author: noahwalton
"""

import numpy as np
import pandas as pd
import pixel




def initialize_pixel_array(number_of_pixels, region_definition, parameter_definition, material_df_base, temp):
    """
    Initializes the pixel object array.

    Parameters
    ----------
    number_of_pixels : float or int
        Number of repeating pixel units in geometry.
    region_definition : TYPE
        DESCRIPTION.
    parameter_definition : TYPE
        DESCRIPTION.
    material_df_base : TYPE
        DESCRIPTION.
    temp : TYPE
        DESCRIPTION.

    Returns
    -------
    pixel_array : object array
        Array of pixel objects.

    """
    pixel_array = []
    for i in range(number_of_pixels):
        pixel_array.append(pixel.pixel(region_definition, parameter_definition, material_df_base, i+1, temp))
    return pixel_array


def get_updated_materials_in_pixel_array(pixel_array, parameter_df):
    """
    Updates the material definitions for each pixel in pixel array and defines updated material string attribute.
    
    This function runs apply_optimization_parameters_to_material_definitions() and write_material_string() for each 
    pixel in the given pixel array.
    
    See Also
    --------
    pixel.apply_optimization_parameters_to_material_definitions
    pixel.write_material_string
    

    Parameters
    ----------
    pixel_array : object array
        Array of pixel objects.
    parameter_df : DataFrame
        DataFrame containing the parameters being optimized by ADAM.

    Returns
    -------
    None.

    """
    # update materials based on optimization parameter
    for i in range(len(pixel_array)):
        pixel_array[i].apply_optimization_parameters_to_material_definitions(parameter_df.iloc[i])
        pixel_array[i].write_material_string()
        
        
def write_material_strings_to_template(pixel_array, input_file):
    """
    Write updated material strings for each pixel in pixel_array to an input file.

    Parameters
    ----------
    pixel_array : object array
        Array of pixel objects.
    input_file : string
        Filename of the input file to be created.

    Returns
    -------
    None.

    """
    
    with open(input_file, 'r') as f:
        readlines = f.readlines()
        f.close()
        
    with open(input_file, 'w') as f:
        for line in readlines:
            f.write(line)
            
            if line.startswith('read composition'):
                for each_pixel in pixel_array:
                    f.write(each_pixel.material_string)
                    
                
def get_nuclide_sensitivites_for_each_pixel(pixel_array, sensitivity_dictionary):
    """
    Converts sensitivity/derivative data from scale material numbering/id scheme to object oriented.
    
    This function takes the sensitivity_dictionary produced by scale_interface.read_total_sensitivity_by_nuclide() and assigns 
    the data to each pixel object and the respective regions within. The result is a new attribute in each pixel object that houses the derivative information for that step, this attirbute 
    is a dictionary titled "sensitivity_data_by_nuclide" and has the form {region:{isotope:(sensitivity, uncertainty, atom_density, absolute_sensitivity)}}.

    Parameters
    ----------
    pixel_array : object array
        Array of pixel objects.
    sensitivity_dictionary : dict
        Dictionary containing sensitivity data read from a scale.out file.

    Returns
    -------
    None.

    """
    
    for each_pixel in pixel_array:
        
        each_pixel.sensitivity_data_by_nuclide = {}
        
        for i, region in enumerate(each_pixel.region_definition):
            scale_material_id = each_pixel.pixel_id*10 + i
            each_pixel.sensitivity_data_by_nuclide[region] = sensitivity_dictionary[scale_material_id]
                
                
                
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
                    
                    