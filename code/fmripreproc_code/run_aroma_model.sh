#!/usr/bin/bash
#
# run_aroma_model
#
# SYNTAX
#     run_aroma_model $epi $t1w $fsf $stdimg $wd
#
# DESCRIPTION
# run fsl feat model for aroma 

# Amy Hegarty, Intermountain Neuroimaging Consortium
# 12-16-2021
#______________________________________________________________________
#

# assign inputs
epi_preproc=$1   							 # functional series for aroma calculation
epi_ref=${epi_preproc/bold/sbref}    	     # epi reference image (either mean vol or SBref)
t1w_brain=$2     							 # t1w image from bet (skull stripped)
fsf=$3										 # design file template for aroma
stdimg=$4        							 # standard space image for final registration
wd=$5

# pull task and run name (assumes bids convention!)
epiname=`basename $epi_preproc`
subj=`echo ${epiname#*sub-} | cut -d"_" -f1`
task=`echo ${epiname#*task-} | cut -d"_" -f1`
run=`echo ${epiname#*run-} | cut -d"_" -f1`

# setup
mkdir -p $wd/aroma/
cd $wd/aroma/

featname=${task}${run}_aroma_noHP.feat
log=${task}${run}_aroma_noHP.log

# create local links for epi and sbref
epi=$PWD/$task$run.nii.gz
ln -s $epi_preproc $epi

sbref=$PWD/${task}${run}_sbref.nii.gz
ln -s $epi_ref $sbref

t1w=$PWD/t1w_brain.nii.gz
if ! [ -f $t1w ]; then
	ln -s $t1w_brain $t1w
fi

t1w_head=$PWD/t1w.nii.gz
if ! [ -f $t1w_head ]; then
	ln -s ${t1w_brain//brain/head} $t1w_head
fi

# build fsf file...

here=$PWD

fsffile=`basename $fsf`
designfile=${task}${run}_${fsffile}
cp -p $fsf $wd/aroma/$designfile
cd $wd/aroma/

# Look for placeholders in template file
sed -i "s,OUTPUTFILE_PLACEHOLDER,$featname,g" $designfile
sed -i "s,INPUTFILE_PLACEHOLDER,$epi,g" $designfile
sed -i "s,ALT_REFERENCE_IMG_PLACEHOLDER,$sbref,g" $designfile
sed -i "s,STRUCTURAL_IMG_PLACEHOLDER,$t1w,g" $designfile

# add other metrics needed for feat
dim4=`fslval $epi_preproc dim4`
echo $dim4
sed -i "s,TOTAL_VOLUMES_PLACEHOLDER,$dim4,g" $designfile

tr=`fslval $epi_preproc pixdim4`
echo $tr
sed -i "s,REPETITION_TIME_PLACEHOLDER,$tr,g" $designfile

# !! figure out how to look for this!! #
unwrapdir=y-
sed -i "s,UNWARP_DIRECTION_PLACEHOLDER,${unwrapdir},g" $designfile

sed -i "s,BRAIN_STANDARD_PLACEHOLDER,$stdimg,g" $designfile

# run feat....
export FSL_SLURM_XNODE_NAME=bnode0101,bnode0102,bnode0103,bnode0104,bnode0105
export FSL_SLURM_NUM_CPU=3
export FSL_SLURM_UCB_ACCOUNT=blanca-ics-test
export FSL_SLURM_PARTITION_NAME=blanca-ics
export FSL_SLURM_QUEUE_NAME=blanca-ics
export FSL_SLURM_WALLTIME_MINUTES=1440
export FSL_SLURM_MB_RAM=8G

cmd="feat $designfile"
echo $cmd >> $log
$cmd >> $log 2>&1
cd $here

start=$SECONDS
killtime=21600  # 6 hours
while squeue | grep 'feat' | grep $USER > /dev/null ; 
do
    duration=$(( SECONDS - start ))
    if [[ $duration -gt $killtime ]]; then echo "Maximum Wait Time of $killtime seconds reached. Exiting with ERROR"; exit 1; fi
    echo "Waiting For Jobs To Complete: $duration seconds"
    sleep 30;
done;
sleep 30;