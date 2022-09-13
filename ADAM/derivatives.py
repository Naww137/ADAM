#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 10:59:10 2022

@author: noahwalton
"""

import numpy as np
import pandas as pd

                    

def combine_nuclide_derivatives(nuclide_derivatives):
    """
    Function used to combine derivatives from individual nuclides into a derivative wrt the material.
    
    Because ADAM wants the derivative with respect to the number density of a given material, and that is a function 
    of individual isotopes' number density, the chain rule for derivatives must be used. In this case, it is a simple 
    sum over all nuclide derivatives because the total atom density for a material is just a sum of all constituent atom densities.

    Parameters
    ----------
    nuclide_derivatives : dictionary
        This is a dictionary with keys corresponding to nuclides and values corresponding to the absolute sensitivity/derivative 
        of k-effective with respect to the keyed nuclide.

    Returns
    -------
    combined_derivatives : float
        Combined derivative with respect to the material composed of the individual nuclides.

    """
    combined_derivatives = 0
    for isotope in nuclide_derivatives:
        combined_derivatives += nuclide_derivatives[isotope]
    return combined_derivatives
                    

def combine_region_derivatives(region_derivatives):
    parameter_derivative = sum(region_derivatives)
    return parameter_derivative
    