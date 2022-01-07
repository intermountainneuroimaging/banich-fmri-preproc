#!/usr/bin/bash
#
# run_outliers
#
# SYNTAX
#     run_outliers $epi $t1w $wd
#
# DESCRIPTION
# run fsl motion outlier detection for preprocessed images

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 12-16-2021
#______________________________________________________________________
#

# assign inputs
epi_preproc=$1   							 # functional series BEFORE motion correction from preproc working directory...
epi_preproc_mcf=$2 							 # functional series AFTER motion correction from preproc working directory...
# mask=$3							 		     # Brain mask for functional series
wd=$3

# setup
mkdir -p $wd/preproc/
cd $wd/preproc/

prefix=`echo $epi_preproc | cut -d"." -f1`
log=${prefix}_outlier_detection.log


# ---------- Framewise Displacement Outliers --------- #

outname=${prefix}_fd_outliers.tsv
metricsfile=${prefix}_fd_metrics.tsv


# run outlier detection for framewise displacement on **pre-motion corrected images**
cmd="fsl_motion_outliers -i $epi_preproc -o $outname -s $metricsfile -p ${metricsfile//.tsv/.png} --fd"
echo $cmd >> $log
$cmd >> $log 2>&1
cd $here


# ---------- DVARS Outliers --------- #
outname=${prefix}_dvars_outliers.tsv
metricsfile=${prefix}_dvars_metrics.tsv

# run outlier detection for framewise displacement on **pre-motion corrected images**
cmd="fsl_motion_outliers -i $epi_preproc_mcf -o $outname -s $metricsfile -p ${metricsfile//.tsv/.png} --dvars --nomoco"
echo $cmd >> $log
$cmd >> $log 2>&1
cd $here

counfoundsname=${prefix}_confounds.tsv

# puth the outlier files + metrics together + motion (?)
	# 1. make all consistent format...
	# 2. add headers...
	# 3. paste together

