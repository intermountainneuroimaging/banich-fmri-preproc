#!/usr/bin/bash
#
# run_discorrepi
#
# SYNTAX
#     run_discorrepi XXXXX
#
# DESCRIPTION
# Run distortion correction with FSL topup if prescan normalization filter set.
#
# Outputs saved in analyis/topup/$subj/Nifti/dcorr within studydir:
#     dc_${func}
#     dc_${func}_sbref
#     appa_dist_corr (if any functional series with AP orientation)
#     paap_dist_corr (if any functional series with PA orientation)
#
# Whether to apply APPA or PAAP is determined from:
#     data/images/$subj/$session/log/*orient.log per functional series
#
# For each dc_raw output, these outputs are also added:
#     _abs  -- converted negatives to absolute value
#
# The FSL topup guide recommends abs when subsequent software expects
# only positive intensities.
# MRN auto-analysis has used threshold at zero instead.

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 09-03-2021
#______________________________________________________________________
#

# assign inputs
epi=$1           # functional series for distortion correction
topup_fout=$2    # output from topup  
params=$3        # parameters for aquisition sequence
topupdir=$4
wd=$5

mkdir -p $wd/distcorrepi
cd $wd/distcorrepi

log="${wd}/distcorrepi/distcorrepi.log"

# get file name from full file, and softlink to working dir...
epifile=${epi##*/}
ln -sf $epi $epifile    # soft link from input file to working directory

sname=`echo $epifile | sed -e 's,.nii.gz,,'`
distcorrepi=dc_${sname}
distcorrepi_abs=dc_${sname}_abs

# apply distortion correction to functional series
cmd="applytopup --imain=$epifile --inindex=1 --topup=../$topupdir/$topup_fout --datain=../$topupdir/$params --method=jac --interp=spline --out=$distcorrepi"
echo $cmd >> $log
$cmd >> $log 2>&1

#removing spline interpolation negative values by replacing with absolute value
cmd="fslmaths $distcorrepi -abs $distcorrepi_abs -odt short"
echo "REMOVING ALL NEGATIVE VALUES AFTER SPLINE INTERPOLATION" >> $log
echo $cmd >> $log
$cmd >> $log 2>&1


# END RUN_DISTCORREPI


