Derivatives
***********

This module houses functions used to convert the derivatives with respect to nuclides and or specific regions to derivatives with respect to the optimization parameters.
Often the output of a given MC Transport/sensitivity calculation is the derivative of some figure of merit to the macroscopic cross section of each isotope in the problem.
Macroscopic cross secitons are proportional to the number density of that isotope by a factor equivalent to the unchanging microscopic cross seciton.
.. math:: \deltak_{eff}/\deltaN_{i}*\sigma
Where i is specific to a given isotope in the problem. What we can reasonable control in a system is the density of some material or compound, which is a function of the
densities of each constituent isotope. This require a chain rule for derivatives, i.e.,
.. math:: \deltak_{eff}/\delta\rho = sum(\deltak_{eff}/\deltaN_i * \deltaN_i/\deltarho)
Furthermore, the ADAM solver is generally not setup to optimized directly over the density parameter $\rho$, rather, some transformation funciton is applied to contrain 
the domain of this parameter without constraining the algorithm itself. This transformation function and the execution of its chain rule is actually housed in the
:doc:'Problem Definition' object since it is thought of as a problem constraint.
test link is :doc:'ADAM_control_module'
 
.. automodule:: ADAM.derivatives
      :members: