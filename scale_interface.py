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




def read_total_sensitivity_by_nuclide(tsunami_file_string):
    """
    Reads out energy integrated total sensitivities for each nuclide in each material id region.

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
    with open(tsunami_file_string, 'r') as f:
        in_data = False
        skiplines = 0
        for line in f:
            
            # read out k-effective, occurs before sensitivities
            if "best estimate system k-eff" in line:
                splitline = line.split()
                keff = float(splitline[5])
                unc = float(splitline[9])
                
            # read out sensitivities
            if "Total Sensitivity Coefficients by Nuclide" in line:
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
                    isotope = splitline[1]
                    atom_density = float(splitline[2])
                    sensitivity = float(splitline[3])
                    uncertainty = float(splitline[5])
                    absolute_sensitivity = sensitivity*atom_density/keff
                    
                    if mixture_id not in data:
                        data[mixture_id] = {}
                    data[mixture_id][isotope] = (sensitivity, uncertainty, atom_density, absolute_sensitivity)
            
    return data, keff
    


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
    
    

def create_tsunami_input(template_file, input_file, steps, hex_number, generations):
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

    Returns
    -------
    None.

    """
    
    with open(template_file, 'r') as f:
        readlines = f.readlines()
        f.close()
        
    with open(input_file, 'w') as f:
        
        if steps == 1:
            for line in readlines[3:]:
                if line.startswith('read start'):
                    continue
                if line.startswith('nst=9'):
                    continue
                if line.startswith('mss=fissionSource.msl'):
                    continue
                if line.startswith('end start'):
                    continue
                if line.startswith('nsk=1'):
                    f.write('nsk=10\n')
                    continue
                if line.startswith(' gen='):
                    f.write('gen={generations+10}\n')
                    continue
                else:
                    f.write(line)
        else:
            for line in readlines:
                if line.startswith('rnd='):
                    f.write(f'rnd={hex_number}')
                if line.startswith('gen='):
                    f.write(f'rnd={generations}')
                else:
                    f.write(line)
    


    


#%% Old legacy function !!!




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
