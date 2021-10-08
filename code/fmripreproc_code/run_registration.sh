#!/usr/bin/bash
#
# run_registration
#
# SYNTAX
#     run_registration $epi $t1w $stdimg $wd
#
# DESCRIPTION
# run registration for functional images to t1w and standard space. 

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 09-03-2021
#______________________________________________________________________
#

# assign inputs
epi=$1           # functional series for preprocessing
t1w=$2    	     # t1w image from bet (with skull)
t1w_brain=$3     # t1w image from bet (skull stripped)
stdimg=$4        # standard space image for final registration
wd=$5

# pull task and run name (assumes bids convention!)
task=`echo ${epi#*task-} | cut -d"_" -f1`
run=`echo ${epi#*run-} | cut -d"_" -f1`

# setup
mkdir -p $wd/reg/$task$run
cd $wd/reg/$task$run

log='registration.log'

# link t1w_brain to directory
cmd="ln -s $t1w_brain highres.nii.gz"
echo $cmd >> $log
$cmd >> $log 2>&1

maskfile=${t1w_brain/T1w.nii.gz/mask.nii.gz}
cmd="ln -s $maskfile mask.nii.gz"
echo $cmd >> $log
$cmd >> $log 2>&1


# link t1w to directory
cmd="ln -s $t1w  highres_head.nii.gz"
echo $cmd >> $log
$cmd >> $log 2>&1

# link standard image to directory
echo "Using standard image: $stdimg"
cmd="ln -s $stdimg standard.nii.gz"
echo $cmd >> $log
$cmd >> $log 2>&1

# get epi reference image...
cmd="fslmaths $epi func_data -odt float"
echo $cmd >> $log
$cmd >> $log 2>&1

sbrefile=${epi//bold/sbref}

if [ -f $sbrefile ] ; then 
	echo "SBref exists: Using single band reference for registration" >> $log
	cmd="ln -s ${epi//bold/sbref} example_func.nii.gz"
	echo $cmd >> $log
	$cmd >> $log 2>&1 
else
	echo "Using center frame for registration" >> $log
	let voln=`fslval $epi dim4`
	echo "Total original volumes: $voln" >> $log
	centerval=`bc <<<"scale=0; $voln / 2"`
	cmd="fslroi func_data example_func $centerval 1"
	echo $cmd >> $log
	$cmd >> $log 2>&1 
fi

# register epi to t1w
cmd="epi_reg --epi=example_func --t1=highres_head --t1brain=highres --out=example_func2highres"
echo $cmd >> $log
$cmd >> $log 2>&1 

# add transforms...
cmd="convert_xfm -inverse -omat highres2example_func.mat example_func2highres.mat"
echo $cmd >> $log
$cmd >> $log 2>&1 

# register t1w to standard space
cmd="flirt -in highres -ref standard -out highres2standard -omat highres2standard.mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear "
echo $cmd >> $log
$cmd >> $log 2>&1 

# add transforms...
cmd="convert_xfm -inverse -omat standard2highres.mat highres2standard.mat"
echo $cmd >> $log
$cmd >> $log 2>&1 

# add transforms...
cmd="convert_xfm -omat example_func2standard.mat -concat highres2standard.mat example_func2highres.mat"
echo $cmd >> $log
$cmd >> $log 2>&1 

# register example_func to standard space
cmd="flirt -ref standard -in example_func -out example_func2standard -applyxfm -init example_func2standard.mat -interp trilinear"
echo $cmd >> $log
$cmd >> $log 2>&1 

# register func to standard space
cmd="flirt -ref standard -in func_data -out func_data2standard -applyxfm -init example_func2standard.mat -interp trilinear"
echo $cmd >> $log
$cmd >> $log 2>&1 

# register brain mask to standard space
cmd="flirt -ref standard -in mask -out mask2standard -applyxfm -init highres2standard.mat -interp nearestneighbour"
echo $cmd >> $log
$cmd >> $log 2>&1 

# add transforms...
cmd="convert_xfm -inverse -omat standard2example_func.mat example_func2standard.mat"
echo $cmd >> $log
$cmd >> $log 2>&1 


# END SCRIPT