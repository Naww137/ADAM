#!/bin/bash
#PBS -q fill
#PBS -V
#PBS -l nodes=1:ppn=1

module load mpi
module load scale/6.2.3

TMPDIR=/tmp/$USER/scale.$$

cd $PBS_O_WORKDIR

scalerte -m -T $TMPDIR tsunami_job.inp
grep -a "final result" tsunami_job.inp.out > tsunami_job.inp_done.dat

rm -rf $TMPDIR