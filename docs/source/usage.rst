How to Use The ADAM Project
===========================

Installation
------------

To use **ADAM**, you can install install it using pip:

:code:`pip install git+https://github.com/Naww137/ADAM`

If a new version of ADAM has been release, you can update ADAM by running:

:code:`pip install --upgrade git+https://github.com/Naww137/ADAM`

If you would like to run in `development mode <https://setuptools.pypa.io/en/latest/userguide/development_mode.html>`_, install using:

:code:`pip install -e`

This project comes with significant documentation. In order to devlop and compile this documentation with `sphinx <https://www.sphinx-doc.org/en/master/>`_
follow the next few steps. If you are only a user, all of the ADAM documentation is hosted on this site.

First make sure you have sphinx installed as well as the cloud theme

:code:`pip install sphinx`

:code:`pip install cloud-sptheme`

From the directory where you cloned ADAM run:

:code:`sphinx-build -b html docs/source/ docs/build/html`

To update documetation from the restructured text files without having to rebuild, navigate to the docs/ directory and run:

:code:`make html`

Any changes to the conf.py file will not take effect unless you rebuild.
The HTML files will be created in docs/build/html. The main page can be reached by openning the index.html file. 
This will launch an HTML page and any of the subsequent pages can be reached from here.




Methodology
-----------
Write up some of the methodology here.



.. _usersguide:

Users Guide
-----------

This User's Guide will give a high level overview of how ADAM runs and how to use it. The purpose of the ADAM project is to couple a Monte Carlo
neutron transport/sensitivity calculation to the `ADAM stochastic gradient descent algorithm <https://arxiv.org/pdf/1412.6980.pdf/>`_. 
The current execution of this process is done using the Department of Nuclear Engineering's computing cluster at the University of Tennessee (UTK NE Computing cluster). 
The current MC solver being used is the SCALE TSUNAMI sequence developed at `Oak Ridge National Laboratory <https://www.ornl.gov/scale>`_.
While access to both the UTK NE cluster and SCALE are restricted, this project is structured such that these parts are interchangeable. 
It is likely more intuitive to learn the stucture of this project before discussing how to run on a different machine or with a different MC solver.

In order to run ADAM, the user must supply 4 files. All of these files must be in the directory you wish to run ADAM from.

1. run_adam.py

   This is a short script that executes the algorithm at the highest level. 

   The purpose of this script is twofold. First it imports the ADAM package and instantiates the Problem Definition object and pixel array (discussed later).
   Second, this script loops through a specified number of steps or until a stopping criteria. With each loop, the 
   :ref:`UTK NE Cluster Interface Module <cluster_interface>` of ADAM is called to run the MC solver and wait for it to complete, then the 
   :ref:`ADAM Control Module <ADAM_control_module>` is called to read the output and update the parameters. What this script may look like is the following:

   .. code:: console

         # Import ADAM modules
         from ADAM import ADAM_control_module
         from ADAM import pixel
         import Problem_Definition
         from ADAM import cluster_interface
         # Instantiate problem defintion object
         run_geometry_check = False
         pdef = Problem_Definition.Problem_Definition(True,run_geometry_check)
         # Instantiate pixel array
         pixel_array = []
         for i in range(pdef.number_of_pixels):
            pixel_array.append(pixel.pixel(pdef.region_definition, pdef.parameter_definition, pdef.material_df_base, i+1, pdef.temperature))
         # Run ADAM 
         step = 1
         while step < 5:
            ADAM_control_module.update(step, pixel_array, pdef)
            cluster_interface.submit_jobs_to_necluster('tsunami_job')
            cluster_interface.wait_on_submitted_job('tsunami_job')
            step += 1


   Here is where one could make edits in order to change the machine that the MC solver is running on, i.e. rather than running the cluster_interface module that is specific
   to the UTK NE Cluster, one could create their own module to interface with a machine of their choise.
   This script is not a part of the ADAM package, however, an example is included in the cloned repository.

2. :ref:`Problem_Definition.py <problem_definition>`

   This file is a python class that houses information about the materials, geometery, optimization parameters, objective function, and ADAM hyperparameters.
   This information is instantiated with the run_adam.py script, then passed to the ADAM Control Module. 
   This is the primary control for the problem setup, see the :ref:`documentation <problem_definition>` on this object to learn how to define a problem.
   This script is not a part of the ADAM package, however, an example is included in the cloned repository.

3. The template file

   The current setup of ADAM is to optimize over a set parameters that are controlling the density of different materials in a system. 
   ADAM bookeeps this data in dataframes belonging to :ref:`pixel <pixel>` objects. Becuase the MC solver is supposed to be interchangeable,
   with each step ADAM provides a material density and an ID, that ID corresponds to a specific numbering scheme that can be matched to the 
   geometry definition in a MC solver input file. For using the ADAM project with SCALE, a template file must be supplied. 
   The :ref:`Scale Interface Module <scale_interface>` of ADAM copies that template file and fills this the material definitions
   with IDs corresponding to geometric IDs.
   If you are using this package and replacing the scale interface, this file may not be necessary.

   .. note::
      These template files are not included in the repository because SCALE is an export controlled code.

4. Shell script

   The necessity of this file is an artifact of the machine ADAM interfaces with. A shell script is used to send the MC solver "job"
   to a job management system that will send it to a particular computing node. This file is machine specific and therefore not included 
   in the distribution of ADAM.





The :ref:`ADAM Control Module <ADAM_control_module>` is considered the primary control module for the algorithm. 
This module is called to update the parameters for each step of the gradient descent. This is seen in the code snipet above for the run_adam.py script.
The update function within this module will do the following:
* Read the previous step's (or starting) parameters 
* Perform the ADAM update to parameters
* Write the new parameters to a csv file in ./parameter_data
* Create a new MC solver input file
Then, as seen in the code snippet, a module is called to run and wait on that MC solution.




