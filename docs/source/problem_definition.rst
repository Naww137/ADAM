Problem Definition
==================

.. _problem_definition:

The Problem Defintion is an object class in ADAM that houses all information about the optimization problem being solved.
The user must instantiate this object and pass it to the :ref:`ADAM_control_module.run() <ADAM_control_module>`.  function in order to execute ADAM. 
An example of this is given in the run_adam.py example.

Required Arguements
-------------------

When instantiating the Problem Definition, the following arguements are required. 
The format for the material dictionary, region definition, and parameter definition are described further below in the Geometry & Material Definition section.

.. py:function:: Problem_Definition.Problem_Definition()

        Instantiates ADAM Problem Definition.

        :param template_filename: Whether or not to write the variables to a csv with each step.
        :type template_filename: str
        :param material_dict_base: Whether or not to build a new input with each step.
        :type material_dict_base: dictionary
        :param number_of_pixels: Filename (or full path if not in the same directory) to the MC solver template file.
        :type number_of_pixels: int
        :param region_definition: Number of neutron generations to run for each MC solve.
        :type region_definition: dictionary
        :param parameter_definition: Temperature of the material pixels in the system.
        :type parameter_definition: dictionary
        :param initial_parameter_df: Initial optimization parameters.
        :type initial_parameter_df: DataFrame

        :param generations: MC transport generations to run per solve.
        :type generations: int
        :param temperature: Temperature of the material pixels in the system.
        :type temperature: int or float

        :param transformation: Tranformation function for optimization parameters.
        :type transformation: func
        :param obj_derivative: Objective derivative function.
        :type obj_derivative: function

        :return: None - instantiates object attributes.
        :rtype: None



Options ADAM Runtime Parameters
-------------------------------

When instantiating the problem definition object, the user has the option to pass in a key-word arguement for ADAM_Runtime_Parameters.
This is a dictionary with intuitively named options as seen below. 
You can pass a dictionary with any or all of the options below and those given will replace the default.

.. code:: console

        ADAM_Runtime_Parameters_default = {     'Write Output'          :   True, 
                                                'Build Input'           :   True, 
                                                'Submit Job'            :   True,
                                                'Run Geometry Check'    :   False,

                                                'beta 1'    :   0.9, 
                                                'beta 2'    :   0.999,
                                                'epsilon'   :   1e-8,
                                                'alpha'     :   1e-3             } 


Geometry & Material Definition
------------------------------


The geometric space of the system is pixellated, this is motivated in part by the types of problems being solved and also by the conveinient bookeeping allowed by object arrays.
The :ref:`pixel object <pixel>` represents a single repeating unitcell in the geometry. One of it's attributes is a pixel id that is mapped to a geometric 
definition in the MC solver. Within each pixel, the user can define one or more regions in which there will be one or more material(s) and corresponding
set of optimization parameter(s). 

For example, a pixel of just one region with fuel and moderator materials optimized independently would correspond to that entire pixel being a homogenized mixture of fuel
and moderator. The ratio of the two and the total density of the pixel are what ADAM would be optimizing. 
To continue with this example lets look at what the input for this system would be:

.. code:: console

        self.region_definition   = {'whole_pixel':['fuel','moderator']}
        self.parameter_definition = {'whole_pixel':['theta0','theta1']}

Bother the region_definition and parameter_definition are dictionaries of the same structure, and both are required. 
The dictionary keys correspond to the region within the pixel, the key itself is arbitrary as long as it is consistent. 
The value-pair for a given region is a list that tells what materials are present in that region and what optimization parameters you want to apply to each.

As another example, if you wanted a pixel choose between a fuel or moderator, but if fuel then also a clad must be included, you could do something like this:

.. code:: console

        self.region_definition   = {'rod':['fuel','moderator'], 'clad':['zircalloy','moderator']}
        self.parameter_definition = {'rod':['theta0','theta1'], 'clad':['theta0','theta1']}

The material defintion is easily defined as a disctionary, but then converted to a dataframe within ADAM. The user defines a "base" set of materials
with keys that correspond the the materials defined the the region_definition. The number densities in this "base" definition are multiplied by the 
transformed optimization parameters before being put into the MC solver. This means that once you have converged to a solution, the corresponding 
number denstiy of a given material in the system will be:
base*trans(theta).

An example of a material dictionary is:

.. code:: console

    material_dict_base = {'fuel':{
                                    'u-235':8.59435E-04,
                                    'u-238':2.23686E-02,
                                    'o-16':4.64708E-02},
                    
                        'zircalloy':{'cr-52':6.98800E-05,
                                    'fe-56':1.42586E-04,
                                    'fe-58':4.38228E-07,
                                    'zr-94':7.37398E-03},

                        'moderator':{
                                    'o-16':3.3368E-02,
                                    'h-1':6.6733E-02}  
                                                        }

If using ADAM as-is with SCALE and the UTK NE cluster, the isotope keys must be in the shown format.


Objective & Transformation Funtions
-----------------------------------

:math:`\\frac{ \\sum_{t=0}^{N}f(t,k) }{N}`
