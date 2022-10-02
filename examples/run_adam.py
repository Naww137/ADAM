


from ADAM import ADAM_control_module
from ADAM import pixel
import Problem_Definition
from ADAM import cluster_interface


submit_job = False
run_geometry_check = False

pdef = Problem_Definition.Problem_Definition(True,run_geometry_check)

### Initializa pixel array
pixel_array = []
for i in range(pdef.number_of_pixels):
    pixel_array.append(pixel.pixel(pdef.region_definition, pdef.parameter_definition, pdef.material_df_base, i+1, pdef.temperature))

with open("run_adam.outfile", 'w') as f:
    f.write("Welcome to ADAM!\nYou have just started running, this file will print updates for each step")

step = 1
### Run ADAM 
while step < 10:

    # create a step
    ADAM_control_module.update(step, pixel_array, pdef)

    # run a step
    if submit_job:
        cluster_interface.submit_jobs_to_necluster('tsunami_job')
        cluster_interface.wait_on_submitted_job('tsunami_job')
        cluster_interface.remove_unwanted_files()

    # if tsunami job completed with no errors, continues, else re-run step

    step += 1
    with open("run_adam.outfile", 'a') as f:
        f.write(f"Step {step}: keff= \nMoving to step {step}.\n")


