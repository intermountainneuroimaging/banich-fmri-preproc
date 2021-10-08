#!/usr/bin/bash
#
# run_snr
#
# SYNTAX
#     run_snr $epi $t1w $wd
#
# DESCRIPTION
# run signal to noise ratio for functional images  

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 09-03-2021
#______________________________________________________________________
#

# assign inputs
epi_preproc=$1   							 # functional series for snr calculation
epi_ref=${epi_preproc/bold/sbref}    	     # t1w image from bet (with skull)
t1w_brain=$2     							 # t1w image from bet (skull stripped)
wd=$3

# pull task and run name (assumes bids convention!)
epiname=`basename $epi_preproc`
subj=`echo ${epiname#*sub-} | cut -d"_" -f1`
task=`echo ${epiname#*task-} | cut -d"_" -f1`
run=`echo ${epiname#*run-} | cut -d"_" -f1`

# setup
mkdir -p $wd/snr/$task$run
cd $wd/snr/$task$run

log='snr.log'

# create local links for epi and sbref
epi=$task$run.nii.gz
ln -s $epi_preproc $epi

sbref=${task}${run}_sbref.nii.gz
ln -s $epi_ref $sbref

t1w=t1w.nii.gz
ln -s $t1w_brain $t1w

# run snr calculation....
cmd="mb_snr_calc $subj $task $epi $sbref $t1w $t1w"
echo $cmd >> $log
$cmd >> $log 2>&1