#!/bin/bash
#  run_bet
#
# SYNTAX
#     run_bet $t1w $outfile $wd 
#
# DESCRIPTION
#
# Amy Hegarty, Intermountain Neuroimaging Consortium
# 09-03-2021
#______________________________________________________________________
#
#
bidst1w=$1
wd=$2
log=bet.log
#
mkdir -p $wd/bet
cd $wd/bet

currentDate=`date`
echo "time stamp: $currentDate" >> $log
echo "$PWD" >> $log

cmd="ln -s $bidst1w t1w.nii.gz "
echo $cmd >> $log
$cmd >> $log 2>&1

cmd="t1_fnirt_bet2 $PWD/t1w.nii.gz 0.8mm "  ## t1_fnirt_bet2 is a banich lab tool!!
echo $cmd >> $log
$cmd >> $log 2>&1


exit 0
