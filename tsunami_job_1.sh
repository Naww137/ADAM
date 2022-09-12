#!/bin/bash
#PBS -q corei7
#PBS -V
#PBS -l nodes=1:ppn=1

module load mpi
module load scale/6.2.3

TMPDIR=/tmp/$USER/scale.$$

cd $PBS_O_WORKDIR

scalerte -m -T $TMPDIR tsunami_job_1.inp
grep -a "final result" tsunami_job_1.inp.out > tsunami_job_1.inp_done.dat

rm -rf $TMPDIR