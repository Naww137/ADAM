#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:39:52 2022

@author: noahwalton
"""

import os
import time



multithreaded_scale_script = """#!/bin/bash
#PBS -q gen5
#PBS -V
#PBS -l nodes=3:ppn=8

module load mpi
module load scale/6.2.3

cat ${PBS_NODEFILE}
#NP=$(grep -c node ${PBS_NODEFILE})

cd $PBS_O_WORKDIR

#echo $NP
scalerte -m -N 24 -M ${PBS_NODEFILE} -T /home/tmp_scale/$USER/scale.$$ %%%input_flag%%%.inp
grep -a "final result" %%%input_flag%%%.inp.out > %%%input_flag%%%.inp_done.dat"""

singlethreaded_scale_script = \
"""#!/bin/bash
#PBS -q corei7
#PBS -V
#PBS -l nodes=1:ppn=1

module load mpi
module load scale/6.2.3

TMPDIR=/tmp/$USER/scale.$$

cd $PBS_O_WORKDIR

scalerte -m -T $TMPDIR %%%input_flag%%%.inp
grep -a "final result" %%%input_flag%%%.inp.out > %%%input_flag%%%.inp_done.dat

rm -rf $TMPDIR"""





def build_scale_submission_script(file_name_flag, solve_type):
    if solve_type == 'keno':
        script = multithreaded_scale_script
    if solve_type == 'tsunami':
        script = singlethreaded_scale_script

    script = script.replace('%%%input_flag%%%', file_name_flag)

    scale_script_file = open(file_name_flag + '.sh', 'w')
    scale_script_file.write(script)
    scale_script_file.close()
    
    
    
    
def submit_jobs_to_necluster(file_name_flag):
    ### Removing any "_done" files, they are how the code knows to continue
    for file in os.listdir("."):
        if "_done" in file:
            os.remove(file)

    remove_unwanted_files()
    ### Submitting current file script
    current_Dir = os.getcwd()
    os.system('ssh -tt necluster.ne.utk.edu "cd ' + current_Dir + ' && qsub ' + file_name_flag + '.sh' + '"')
    
    
    
    
def wait_on_submitted_job(file_name_flag, output_filepath):

    with open(output_filepath, 'a') as f:
        f.write("Waiting on job\n")

        _ = 0
        total_time = 0
        while _ == 0:
            for file in os.listdir("."):
                if '_done' in file:
                    #time.sleep(5)
                    f.write("Job complete! Continuing...\n")
                    return
                if 'job.sh.' in file:
                    f.write("Cluster job finished, checking output files \n")
                    return

            f.write(f"Not yet complete, waiting 60 seconds. Total: {total_time/60} minutes\n")
            total_time += 60
            time.sleep(60)
            
        f.close()

def remove_unwanted_files():
    # os.system('ssh -tt necluster.ne.utk.edu "cd ' + os.getcwd() + ' && rm -rf *.html *.htmd *.sh.* *.sdf *.txt *.3dmap')
    os.system('ssh -tt necluster.ne.utk.edu "cd ' + os.getcwd() + ' && rm -rf *job.sh.*"')


def remove_out_files():
    os.system('ssh -tt necluster.ne.utk.edu "cd ' + os.getcwd() + ' && rm -rf *job.out* *.sdf*"')


def check_outfiles_or_rerun(tsunami_file_string,output_filepath):
    if os.path.isfile(f'{tsunami_file_string}.sdf') and os.path.isfile(f'{tsunami_file_string}.out'):
        return
    else:
        submit_jobs_to_necluster(tsunami_file_string)
        wait_on_submitted_job(tsunami_file_string, output_filepath)
        remove_unwanted_files()

    return









