Pixel
*****

.. _pixel:

The pixel object is used to define the geometry of the system being optimized. There are two major motivations for setting up the geometry input in this manner:

1) Traditional and some advanced nuclear system designs often leverage repeating lattice structures

2) The most inspiring goal for this optimization work is to optimize the shape of fuel for fuel performance. 
The methodology for which requires the pixelation of geometric space such that the algorithm can step towards a continuous shape in the limit of infinitesimal pixel size.

The pixel object houses information about the materials/regions within the repeating unit. 
A number of methods are also included that perform functions such as applying the update of materials given some set of transformed optimization parameters. 
This object-oriented structure also helps with bookeeping whenever the number of pixels, and therefore optimization parameters, becomes very large.


.. automodule:: ADAM.pixel
      :members: 
      :undoc-members:
