#%%
from ADAM import ADAM_control_module
from ADAM import pixel
import Problem_Definition
from ADAM import cluster_interface
import os


### Instantiate problem definition
run_geometry_check = False
pdef = Problem_Definition.Problem_Definition(True,run_geometry_check)

### define path to runtime output file
output_filepath = os.path.join(os.getcwd(), "run_adam.outfile")

### Initialize pixel array
pixel_array = []
for i in range(pdef.number_of_pixels):
    pixel_array.append(pixel.pixel(pdef.region_definition, pdef.parameter_definition, pdef.material_df_base, i+1, pdef.temperature))

### Input starting step
step = 598
if step == 1:
    with open(output_filepath, 'w') as f:
        f.write("Welcome to ADAM!\nYou have just started running, this file will print updates for each step\n")
else:
    with open(output_filepath, 'a') as f:
        f.write(f"ADAM was interrupted, retarting from step {step}\n")


### Run ADAM 
while step < 600:

    keff = ADAM_control_module.run(step, pixel_array, pdef, output_filepath)

    step += 1




# %%
