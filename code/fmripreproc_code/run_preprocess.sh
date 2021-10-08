#!/bin/bash
# ldrc_preprocess
#
# SYNTAX
#     run_preprocess $epi $func $outputname $wd $trimvol
#
# DESCRIPTION
# Create in analysis/preproc the accession-based subject number directories with input from:
#    analysis/BET/??????
#    analysis/topup/??????
#
# Into each new analysis/preproc/???? directory, add
#     a link to t1bet/struc_acpc_brain.nii.gz -> t1w_brain.nii.gz
#     a link to t1bet/struc_acpc.nii.gz -> t1w.nii.gz
#     trimmed versions of analysis/topup/$subj/Nifti/dcorr files (removing from the front $trimvol):
#         dc_<task>_abs.nii.gz         -> <task>.nii.gz
#
#     untrimmed versions of data/images/????cf1/Nifti/dcorr files:
#         dc_<task>_SBRef_abs.nii.gz   -> <task>_SBRef.nii.gz
#
# Run mcflirt motion correction on the 7 functional series using the
# matching SBRef series as the reference volume with output in:
#        <task>_mcf.nii.gz
#
# Run bet on the SBRef files in analysis/preproc/* using:
#    bet SBRef SBRef_bet -f 0.3
#
# Amy Hegarty, Intermountain Neuroimaging Consortium
# 09-03-2021
#______________________________________________________________________
#
#
# assign inputs
epi=$1           # functional series for distortion correction
func=$2
wd=$3
let trimvol=${4:-0}  # number of input volumes from epi
#
dcdir=$wd/distcorrepi
betdir=$wd/bet
if [ ! -d $dcdir ]; then
    echo no $subj topup directory
    exit 7
fi
if [ ! -d $betdir ]; then
    echo no $subj bet directory
    exit 7
fi
#
mkdir -p $wd/preproc
cd $wd/preproc 
log=${func}_preprocess.log
#
currentDate=`date`
echo "time stamp: $currentDate" >> $log
echo "$PWD" >> $log
#
t1w_head=$wd/bet/t1bet/struc_acpc.nii.gz
if [ -f $t1w_head ]; then
    headname=t1w.nii.gz
    if ! [ -f $headname ]; then
        echo "... GET HEAD" >> $log
        cmd="ln -s $t1w_head $headname"
        echo $cmd >> $log
        $cmd >> $log 2>&1
    fi
fi
#
t1w_brain=$wd/bet/t1bet/struc_acpc_brain.nii.gz
if [ -f $t1w_brain ] ; then   
    brainname=t1w_brain.nii.gz
    if ! [ -f $brainname ]; then
        echo "... GET EXTRACTED BRAIN" >> $log
        cmd="ln -s $t1w_brain $brainname"
        echo $cmd >> $log
        $cmd >> $log 2>&1
    fi
fi
#
epifile=`basename $epi`
raw=$dcdir/dc_${epifile//.nii/_abs.nii}
echo $raw >> $log
if [ -f $raw ]; then
    echo "... TRIM FUNCTIONAL SERIES: $func" >> $log
    let rawsize="`fslval $raw dim4`"
    let trimmedsize=$rawsize-$trimvol
    trimmed=${func}.nii.gz     
    cmd="fslroi $raw $trimmed $trimvol $trimmedsize"
    echo $cmd >> $log
    $cmd >> $log 2>&1
#
    raw_SBRef=${raw//bold/sbref}
    SBRef=${func}_SBRef.nii.gz
    if [ -f $raw_SBRef ]; then
        echo "... GET SBREF: $func" >> $log
        cmd="ln -s $raw_SBRef $SBRef"
        echo $cmd >> $log
        $cmd >> $log 2>&1
        echo "... MOTION CORRECT FUNCTIONAL SERIES: $func" >> $log
        cmd="mcflirt -in $trimmed -reffile $SBRef -stats -plots -report"
        echo $cmd >> $log
        $cmd >> $log 2>&1
#
        echo "... GET BRAIN EXTRACT: ${func}_SBRef" >> $log
        SBRef_bet=${func}_SBRef_bet.nii.gz
        cmd="bet $SBRef $SBRef_bet -f 0.3"
        echo $cmd >> $log
        $cmd >> $log 2>&1

        echo "... MOVE OUTPUT TO FINAL LOCATION: $outfile " >> $log
        cmd="cp ${func} $outfile"
        echo $cmd >> $log
        $cmd >> $log 2>&1

    else
        # ---- SBref not provided!! ---- #
        echo "... MOTION CORRECT FUNCTIONAL SERIES: $func" >> $log
        cmd="mcflirt -in $trimmed -stats -plots -report"
        echo $cmd >> $log
        $cmd >> $log 2>&1
#
        echo "... NO SBref PROVIDED, REFERENCE VOLUME FROM MCFLIRT: ${func}_meanvol" >> $log
        Ref_bet=${func}_meanvol_bet.nii.gz
        cmd="bet ${func}_mcf_meanvol $Ref_bet -f 0.3"
        echo $cmd >> $log
        $cmd >> $log 2>&1
    fi
    # # move files to final location...
    # outpath=`dirname $outfile`
    # mkdir -p $outpath 
    # cmd="cp -p ${func}_mcf.nii.gz $outfile"
    # echo $cmd >> $log
    # $cmd >> $log 2>&1

    # mkdir -p ../logs
    # cmd="cp -p *.log ../logs"
    # echo $cmd >> $log
    # $cmd >> $log 2>&1

fi 

#
cd $here
exit 0
