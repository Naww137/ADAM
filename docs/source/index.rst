.. ADAM documentation master file, created by
   sphinx-quickstart on Mon Sep 12 11:18:58 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to The ADAM Project's documentation!
============================================
**ADAM** is a python-based project that leverages the stochastic gradient descent algorithm ADAM to optimize nuclear systems.
This project is a part of Noah Walton's PhD work and is collaboratively developed by members of Dr. Vladimir Sobes' research group 
at the **University of Tennessee**. The ADAM stochastic gradient descent algorithm in it's most general form can be found `here <https://arxiv.org/abs/1412.6980>`_. 
The methodology as it applies to nuclear systems is inspired by the ability to calculate stochastic sensititvies when solving Monte Carlo neutron transport calculations. 
These sensitivities can be converted to derivatives and used as input to a gradient descent algorithm, or in this case ADAM. 
It follows then that the purpose of this python package is to couple a **Monte Carlo neutron transport** solver to the execution of the ADAM algorithm and automate 
the step-by-step gradient descent. A scientific journal paper that details three challenge problems solved by ADAM is currently in the review process. 
A scientific conference article on the execution of the algorithm and its publication/open source availability is also currently in-process.

The following sections will describe how to install and use ADAM. Also, the API give more documentation on the internal source code for development and 
expansion of capabilities.


Contents
--------

.. toctree::
   :caption: Cntents:

   usage
   problem_definition
   source_api/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
