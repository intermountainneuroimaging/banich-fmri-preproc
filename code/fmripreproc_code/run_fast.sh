#!/bin/bash
#  run_fast
#
# SYNTAX
#     run_fast $t1w $outfile $wd 
#
# DESCRIPTION
#
# Amy Hegarty, Intermountain Neuroimaging Consortium
# 12-16-2021
#______________________________________________________________________
#
#
bidst1w=$1
wd=$2
log=fast.log
#
mkdir -p $wd/segment
cd $wd/segment

currentDate=`date`
echo "time stamp: $currentDate" >> $log
echo "$PWD" >> $log

cmd="ln -s $bidst1w t1w_brain.nii.gz "
echo $cmd >> $log
$cmd >> $log 2>&1

cmd="fast -g t1w_brain.nii.gz"  
echo $cmd >> $log
$cmd >> $log 2>&1


exit 0

