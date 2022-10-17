
from ADAM import ADAM_control_module
from ADAM import pixel
import Problem_Definition
from ADAM import cluster_interface


### Instantiate problem definition
run_geometry_check = False
pdef = Problem_Definition.Problem_Definition(True,run_geometry_check)


### Initialize pixel array
pixel_array = []
for i in range(pdef.number_of_pixels):
    pixel_array.append(pixel.pixel(pdef.region_definition, pdef.parameter_definition, pdef.material_df_base, i+1, pdef.temperature))

with open("run_adam.outfile", 'w') as f:
    f.write("Welcome to ADAM!\nYou have just started running, this file will print updates for each step")


step = 1
### Run ADAM 
while step < 3:

    keff = ADAM_control_module.run(step, pixel_array, pdef)

    step += 1
    with open("run_adam.outfile", 'a') as f:
        f.write(f"Step {step}: keff={keff} \nMoving to step {step}.\n")


