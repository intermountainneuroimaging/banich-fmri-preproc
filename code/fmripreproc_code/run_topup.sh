#!/usr/bin/bash
#
# run_topup
#
# SYNTAX
#     run_topup XXXXX
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
apfmap=$1
pafmap=$2
wd=$3
TotalReadoutTime=${4:-0.0759712}

mkdir -p ${wd}/topup
wd="${wd}/topup"
cd $wd
log="${wd}/topup.log"

currentDate=`date`
echo "time stamp: $currentDate" >> $log
echo "$PWD" >> $log


# generate new aquisition parameters...
# ------- AP Aquisition ------- #
n=`fslval $apfmap dim4`
for ((i = 1; i <= n; i++)); do echo "0 -1 0 $TotalReadoutTime"; done > $wd/acqparams_AP.txt 

n=`fslval $pafmap dim4`
for ((i = 1; i <= n; i++)); do echo "0 1 0 $TotalReadoutTime"; done >> $wd/acqparams_AP.txt 

# ------- PA Aquisition ------- #
n=`fslval $pafmap dim4`
for ((i = 1; i <= n; i++)); do echo "0 1 0 $TotalReadoutTime"; done > $wd/acqparams_PA.txt 

n=`fslval $apfmap dim4`
for ((i = 1; i <= n; i++)); do echo "0 -1 0 $TotalReadoutTime"; done >> $wd/acqparams_PA.txt 


# get fieldmap files and make float (could be INT or FLOAT)
if [ ! -f  raw_ap_dist_corr.nii.gz ]; then
    cmd1="fslmaths $apfmap raw_ap_dist_corr -odt float"
    echo $cmd1 >> $log
    $cmd1 >> $log 2>&1
fi
#
if [ ! -f  raw_pa_dist_corr.nii.gz ]; then
    cmd2="fslmaths $pafmap raw_pa_dist_corr -odt float"
    echo $cmd2 >> $log
    $cmd2 >> $log 2>&1
fi

# combine fieldmap files for topup
cmd="fslmerge -t distcorrAPPA raw_ap_dist_corr raw_pa_dist_corr"
echo $cmd >> $log
$cmd >> $log 2>&1

# run topup AP,PA
read -r -d '' cmd << EOM
topup --imain=distcorrAPPA \
  --datain=acqparams_AP.txt \
  --config=b02b0.cnf \
  --out=topup4_results_APPA \
  --fout=topup4_field_APPA \
  --iout=dewarped4_seEPI_APPA \
  --logout=topup
EOM
echo $cmd >> $log
$cmd >> $log 2>&1

cmd="fslmerge -t distcorrPAAP raw_pa_dist_corr raw_ap_dist_corr"
echo $cmd >> $log
$cmd >> $log 2>&1

# run topup PA,AP
read -r -d '' cmd << EOM
topup --imain=distcorrPAAP \
  --datain=acqparams_PA.txt \
  --config=b02b0.cnf \
  --out=topup4_results_PAAP \
  --fout=topup4_field_PAAP \
  --iout=dewarped4_seEPI_PAAP \
  --logout=topup
EOM
echo $cmd >> $log
$cmd >> $log 2>&1

# END RUN_TOPUP


