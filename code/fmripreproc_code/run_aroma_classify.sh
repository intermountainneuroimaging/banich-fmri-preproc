#!/usr/bin/bash
#
# run_aroma_classify
#
# SYNTAX
#     run_aroma_classify featdir outputdir
#
# DESCRIPTION
# Run aroma classification and denoising. Use FSL first level model as input.
#
# requires special python version and path setup.

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 12-19-2021
#______________________________________________________________________
#

featdir=$1		# first level model feat directory (input)
outdir=$2		# output location for results

module load python/2.7.9
export PYTHONPATH=/work/ics/data/projects/banichlab/examples/aroma/tmp_py/site-packages:/curc/tools/x_86_64/rh6/python/2.7.9/gcc/4.9.2
apath=/work/ics/data/projects/banichlab/examples/aroma/src

mkdir -p $outdir

echo "FEAT Direcotry: "$featdir
python $apath/ICA_AROMA.py -feat $featdir -out $outdir  ## imprtant, these paths must be full path(not relative!)

module unload python/2.7.9