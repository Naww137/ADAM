#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 10:59:10 2022

@author: noahwalton
"""

import numpy as np
import pandas as pd
import pixel




def transformation_function(x):
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
    
    y = np.exp(x)
    
    return y



def objective_derivative(derivative_df,parameter_df):
    """
    Gets the derivative of the objective function given the derivatives of the optimized parameters.

    Parameters
    ----------
    derivative_df : TYPE
        DESCRIPTION.
    parameter_df : TYPE
        DESCRIPTION.

    Returns
    -------
    new_sensitivities : TYPE
        DESCRIPTION.

    """
    derivative_np = np.array(derivative_df)
    parameter_np = np.array(parameter_df)
    
    r = 100
    v = 2
    beta_limit = 20

    obj_derivative_np = derivative_np - (-r*v*np.exp(-v*(beta_limit+parameter_np)) + r*v*np.exp(v*(parameter_np-beta_limit)))
    obj_derivative_df = pd.DataFrame(obj_derivative_np, columns=np.array(parameter_df.columns))
    
    return obj_derivative_df
                    
                    

def combine_nuclide_derivatives(nuclide_derivatives):
    """
    Function used to combine derivatives from individual nuclides into a derivative wrt the material.
    
    Because ADAM wants the derivative with respect to the number density of a given material, and that is a function 
    of individual isotopes' number density, the chain rule forderivatives must be used. In this case, it is a simple 
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
    