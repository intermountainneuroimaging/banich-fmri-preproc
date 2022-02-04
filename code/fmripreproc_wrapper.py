#! usr/bin/env python

# ## PIPELINE: fmripreproc_wrapper.py
# ## USAGE: python3 fmripreproc_wrapper --in=<inputs> --out=<outputs> [OPTIONS]
#    * requires python3 and FSL (calls FSL via python subprocess)
#
# ## Author(s)
#
# * Amy K. Hegarty, Intermountain Neuroimaging Consortium, University of Colorado Boulder
# * University of Colorado Boulder
#
# ## Product
#
# FSL Pipelines
#
# ## License
#
# <!-- References -->
# [FSL]: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki
# [pybids]: Yarkoni et al., (2019). PyBIDS: Python tools for BIDS datasets. Journal of Open Source Software, 4(40), 1294, https://doi.org/10.21105/joss.01294
#           Yarkoni, Tal, Markiewicz, Christopher J., de la Vega, Alejandro, Gorgolewski, Krzysztof J., Halchenko, Yaroslav O., Salo, Taylor, ? Blair, Ross. (2019, August 8). bids-standard/pybids: 0.9.3 (Version 0.9.3). Zenodo. http://doi.org/10.5281/zenodo.3363985
#

# ------------------------------------------------------------------------------
#  Show usage information for this script
# ------------------------------------------------------------------------------

def print_help():
  print("""
    fMRI Preprocessing Pipeline
        Usage: """ + """ --in=<bids-inputs> --out=<outputs> --participant-label=<id> [OPTIONS]
        OPTIONS
          --help                      show this usage information and exit
          --participant-label=        participant name for processing (pass only 1)
          --work-dir=                 (Default: <outputs>/scratch/particiant-label) directory 
                                        path for working directory
          --clean-work-dir=           (Default: TRUE) clean working directory 
          --run-qc                    add flag to run automated quality 
                                        control for preprocessing
          --run-aroma                 add flag to run aroma noise removal on 
                                        preprocessed images
          --run-fix (?)               add flag to run fsl-fix noise removal on 
                                        preprocessed images
    ** OpenMP used for parellelized execution of XXX. Multiple cores (CPUs) 
       are recommended (XX cpus for each fmri scan).
       
    ** see github repository for more information and to report issues: 
       https://github.com/intermountainneuroimaging/fmri-preproc.git
        
        """)


# ------------------------------------------------------------------------------
#  Parse arguements for this script
# ------------------------------------------------------------------------------

def parse_arguments(argv):

    import os
    import sys
    import getopt

    #intialize arguements
    print("\nParsing User Inputs...")
    qc = False
    cleandir = False
    runaroma = False
    runfix = False
    overwrite=False


    try:
      opts, args = getopt.getopt(argv,"hi:o:",["in=","out=","help","participant-label=","work-dir=","clean-work-dir=","run-qc","run-aroma","run-fix"])
    except getopt.GetoptError:
      print_help()
      sys.exit(2)
    for opt, arg in opts:
      if opt in ("-h", "--help"):
         print_help()
         sys.exit()
      elif opt in ("-i", "--in"):
         inputs = arg
         if not os.path.exists(inputs):
           raise Exception("BIDS directory does not exist")
      elif opt in ("-o", "--out"):
         outputs = arg
      elif opt in ("--participant-label"):
         pid = arg
      elif opt in ("--work-dir"):
         wd = arg
      elif opt in ("--clean-work-dir"):
         cleandir = arg
      elif opt in ("--run-qc"):
         qc=True
      elif opt in ("--run-aroma"):
        runaroma = True
      elif opt in ("--run-fix"):
        runfix = True                                         
    if 'inputs' not in locals():
      print_help()
      raise Exception("Missing required argument --in=")
      sys.exit()
    if 'outputs' not in locals():
      print_help()
      raise Exception("Missing required argument --out=")
      sys.exit()
    if 'pid' not in locals():
      print_help()
      raise Exception("Missing required argument --participant-label=")
      sys.exit()
      

    if not "wd" in locals():
      wd=outputs + "/fmripreproc/scratch/sub-" + pid

    print('Input Bids directory:\t', inputs)
    print('Derivatives path:\t', outputs+'fmripreproc')
    print('Working directory:\t',wd)
    print('Participant:\t\t', str(pid))

    class args:
      def __init__(self, wd, inputs, outputs, pid, qc, cleandir, runaroma, runfix):
        self.wd = wd
        self.inputs = inputs
        self.outputs = outputs
        self.pid = pid
        self.runQC=qc
        self.cleandir=cleandir
        self.runaroma=runaroma
        self.runfix=runfix
        self.templates='/home/amhe4269/fmripreproc_code'
        self.overwrite=False

    entry = args(wd, inputs, outputs, pid, qc, cleandir, runaroma, runfix)

    return entry

# ------------------------------------------------------------------------------
#  Parse Bids inputs for this script
# ------------------------------------------------------------------------------
def bids_data(entry):
    import os
    import glob
    import bids
    import json

    bids.config.set_option('extension_initial_dot', True)

    layout = bids.BIDSLayout(entry.inputs, derivatives=False, absolute_paths=True)

    if not os.path.exists(entry.outputs + '/fmripreproc') or os.path.exists(entry.outputs + '/fmripreproc/' + 'dataset_description.json'):
      os.makedirs(entry.outputs,mode=511,exist_ok=True)
      os.makedirs(entry.outputs + '/fmripreproc', mode=511,exist_ok=True)

      # make dataset_description file...
      import json

      data = {
        'Name': 'FSL fMRI Minimal Preprocessing',
        "BIDSVersion": "1.1.1",
        "PipelineDescription": { 
              "Name": "FSL fMRI Minimal Preprocessing",
              "Version": "0.0.1",
              "CodeURL": "..."
              },
        "CodeURL": "https://github.com/intermountainneuroimaging/fmri-preproc.git",
        "HowToAcknowledge": "Please cite all relevant works for FSL tools: bet, topup, mcflirt, aroma and python tools: pybids ( https://doi.org/10.21105/joss.01294,  https://doi.org/10.21105/joss.01294)"}

      with open(entry.outputs + '/fmripreproc/' + 'dataset_description.json', 'w') as outfile:
          json.dump(data, outfile, indent=2)

    return layout

# ------------------------------------------------------------------------------
#  Main Pipeline Starts Here...
# ------------------------------------------------------------------------------

def worker(name,cmdfile):
    """Executes the bash script"""
    import subprocess
    from subprocess import PIPE
    process = subprocess.Popen(cmdfile.split(), stdout=PIPE, stderr=PIPE, universal_newlines=True)
    output, error = process.communicate()
    print(error)
    print('Worker: ' + name + ' finished')
    return

def writelist(filename,outlist):
  textfile = open(filename, "w")
  for element in outlist:
      textfile.write(element + "\n")
  textfile.close()

def checkfile_string(filename,txt):
    with open(filename) as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if txt in line:
            return True # The string is found
    return False  # The string does not exist in the file

def run_bet(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  returnflag=False

  # check if output exists already
  if os.path.exists(entry.wd + '/bet/t1bet/struc_acpc_brain.nii.gz') and not entry.overwrite:
    print('Brain Extraction output exists...skipping')

  else:         # Run BET
    print("\nRunning BET...\n")
    t1w=layout.get(subject=entry.pid, extension='nii.gz', suffix='T1w')
    t1w=t1w[0]
    imgpath = t1w.path
    imgname = t1w.filename
    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # -------- run command  -------- #
    cmd = "bash " + entry.templates + "/run_bet.sh " + imgpath + " " + entry.wd
    name = "bet" 
    p = multiprocessing.Process(target=worker, args=(name,cmd))
    p.start()
    print(p)
    returnflag=True

    p.join()  # blocks further execution until job is finished

  return returnflag


def save_bet(layout,entry):
  import os
  import sys

  t1w=layout.get(subject=entry.pid, extension='nii.gz', suffix='T1w')
  imgpath=t1w[0].path

  # output filename...
  ent = layout.parse_file_entities(imgpath)
  if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

  # Define the pattern to build out of the components passed in the dictionary
  pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

  # Add additional info to output file entities
  ent['type'] = 'anat'
  ent['space'] = 'T1w'
  ent['desc'] = 'brain'
  outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  ent['desc'] = 'brain'
  ent['suffix'] = 'mask'
  outmask = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  ent['desc'] = 'head'
  ent['suffix'] = 'T1w'
  outhead = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
  os.system('cp -p ' + entry.wd + '/bet/t1bet/struc_acpc_brain.nii.gz ' + entry.outputs + "/" + outfile)
  os.system('cp -p ' + entry.wd + '/bet/t1bet/struc_acpc_brain_mask.nii.gz ' + entry.outputs + "/" + outmask)
  os.system('cp -p ' + entry.wd + '/bet/t1bet/struc_acpc.nii.gz ' + entry.outputs + "/" + outhead)
    
  ## end run_bet

def run_topup(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing
  import numpy as np
  import re

  # check for number of feildmap pairs
  fmapfiles=layout.get(subject=entry.pid, extension='nii.gz', suffix='epi');
  jobs=[]
  returnflag=False

  if np.remainder(len(fmapfiles), 2) != 0:
    raise Exception("Topup cannot be run...unbalanced Fieldmap pairs")

  npairs = int(len(fmapfiles)/2)
  print(fmapfiles)

  fmapfilenames = [item.path for item in fmapfiles]

  for r in range(1,npairs+1):
    run=str(r).zfill(2)

    fmappair = [x for x in fmapfilenames if 'run-'+run in x]

    if not fmappair:
      fmappair = fmapfilenames

    # check if output exists already
    if os.path.exists(entry.wd + '/topup-'+run+'/topup4_field_APPA.nii.gz') and not entry.overwrite:
      print('Topup-' + run + ' output exists...skipping')
      continue
      print(" ")

    # Run Topup
    print("\nRunning Topup...\n")

    # check two fieldmaps collected with opposing phase encoding directions
    ap=False ; pa=False
    for fmap in fmappair:
      img = layout.get_file(fmap)
      ent = img.get_entities()
      
      if 'AP' in ent['direction']:
        ap=True; img1=img.path ; meta=img.get_metadata()
      elif 'PA' in ent['direction']:
        pa=True ; img2=img.path

    if not ap and not pa:
      # continue topup... (else throw error?)
      raise Exception("Topup cannot be run...Missing AP or PA fieldmaps")

    # add notes on intended in working dir
    os.makedirs(entry.wd + '/topup-'+run,exist_ok=True)
    writelist(entry.wd + '/topup-'+run+'/intendedfor.list', meta['IntendedFor'])
    

    # run script
    cmd = "bash " + entry.templates + "/run_topup.sh " + img1 + " " + img2 + " " + entry.wd+'/topup-'+run + " " + str(meta['TotalReadoutTime'])
    name = "topup"+run
    p = multiprocessing.Process(target=worker, args=(name,cmd))
    jobs.append(p)
    p.start()
    print(p)
    returnflag=True

  for job in jobs:
    job.join()  #wait for all topup commands to finish

  return returnflag
    ## end run_topup

def run_distcorrepi(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing
  import glob

  itr=0;
  nfiles = len(layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'))
  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, extension='nii.gz', suffix=['bold','sbref']):
      
      imgpath = func.path
      imgname = func.filename
      # output filename...
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      # get file metadata
      meta=func.get_metadata()
      aqdir=meta['PhaseEncodingDirection']

      
      if os.path.exists(entry.wd + '/distcorrepi/' + 'dc_' + imgname) and not entry.overwrite:
          itr=itr+1
          print("Distortion correction output exists...skipping: " + imgname)
          continue
          print(" ")

      # ------- Running distortion correction ------- #

      # select topup file based on aquistion direction
      if aqdir == "j-":
        param = "acqparams_AP.txt"
        fout = "topup4_field_APPA"
      elif aqdir == "j":
        param = "acqparams_PA.txt"
        fout = "topup4_field_PAAP"

      s=', '
      print('Using: ' + imgpath)
      print('Using: ' + param)
      print('Using: ' + fout)

      print("distortion corrected image: " + 'dc_' + imgname)

      # select correct topup directory
      topupdir=[]
      for ff in glob.iglob(entry.wd + '/topup-*/intendedfor.list'):
        if checkfile_string(ff,imgname):
          s='/'
          topupdir = ff.split('/')[-2]
      if not topupdir:
        raise Exception("Cannot identify fieldmap intended for distortion correction:" +imgname)

      # -------- run command  -------- #
      cmd = "bash " + entry.templates + "/run_distcorrepi.sh " + imgpath + " " + fout + " " + param + " " + topupdir + " " + entry.wd
      print(cmd)
      print(" ")
      name = "distcorr-" + ent['task'] + str(ent['run']) + "-" + ent['suffix']
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      itr = itr+1
      print(p)
      returnflag=True

  for job in jobs:
    job.join()  #wait for all distcorrepi commands to finish
  
  return returnflag    
  ## end run_discorrpei

def run_preprocess(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  itr=0;
  nfiles = len(layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'))
  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)
      
      if os.path.exists(entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_mcf.nii.gz') and not entry.overwrite:
          itr=itr+1
          print("Motion correction output exists...skipping: " + imgname)
          continue
          print(" ")

      # ------- Running preprocessing: motion correction + trimming ------- #

      s=', '
      print('Using: ' + imgpath)

      # -------- run command  -------- #
      entry.trimvols=10;  # make input!!

      cmd = "bash " + entry.templates + "/run_preprocess.sh " + imgpath + " " + ent['task'] + str(ent['run']) + " " + entry.wd + " " + str(entry.trimvols)
      print(cmd)
      print(" ")
      name = "preproc-" + ent['task'] + str(ent['run'])
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      itr = itr+1
      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all preproc commands to finish
  
  return returnflag    
  ## end run_preprocess

def save_preprocess(layout,entry):
  import os
  import sys

  # Move output files to permanent location
  for func in layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'):
      
    imgpath = func.path
    imgname = func.filename

    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # Define the pattern to build out of the components passed in the dictionary
    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

    # Add additional info to output file entities
    ent['type'] = 'func'
    ent['space'] = 'native'
    ent['desc'] = 'preproc'

    outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    # Add additional info to output file entities
    ent['space'] = 'native'
    ent['desc'] = 'preproc'
    ent['suffix'] = 'sbref'

    outfile_sbref = layout.build_path(ent, pattern, validate=False, absolute_paths=False)
    
    print("Motion corrected image: " + outfile)

    os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
    os.system('cp -p ' + entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_mcf.nii.gz ' + entry.outputs + "/" + outfile)
    if os.path.exists(entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_SBRef_bet.nii.gz'):
      os.system('cp -p ' + entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_SBRef_bet.nii.gz ' + entry.outputs + "/" + outfile_sbref)
    else:
      os.system('cp -p ' + entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_meanvol_bet.nii.gz ' + entry.outputs + "/" + outfile_sbref)

  ## END SAVE_PREPROCESS

def run_registration(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing
  
  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      t1w = layout.get(subject=entry.pid,  desc='brain', extension='nii.gz', suffix='T1w')
      t1wpath = t1w[0].path

      t1whead = layout.get(subject=entry.pid,  desc='head', extension='nii.gz', suffix='T1w')
      t1wheadpath = t1whead[0].path

      if os.path.exists(entry.wd + '/reg/' + ent['task'] + str(ent['run']) +'/' + 'func_data2standard.nii.gz') and not entry.overwrite:
          print("Registration complete...skipping: " + imgname)
          continue
          print(" ")

      # ------- Running registration: T1w space and MNI152Nonlin2006 (FSLstandard) ------- #

      s=', '
      print('Registering: ' + imgpath)
      print('Using: ' + t1wpath)

      # -------- run command  -------- #
      stdpath = os.popen('echo $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz').read().rstrip()

      cmd = "bash " + entry.templates + "/run_registration.sh " + imgpath + " " + t1wheadpath + " " + t1wpath + " " + stdpath + " " + entry.wd 
      name = "registration-" + ent['task'] + str(ent['run']) + "-" + ent['suffix']
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all preproc commands to finish

  return returnflag
  
  ## end run_registration

def save_registration(layout,entry):
  import os
  import sys

  # move outputs to permanent location...
  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
    imgpath = func.path
    imgname = func.filename

    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # Define the pattern to build out of the components passed in the dictionary
    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

    # Add additional info to output file entities
    ent['type'] = 'func'
    ent['space'] = 'MNI152Nonlin2006'
    ent['desc'] = 'preproc'

    outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    ent['suffix'] = 'sbref'
    outfile_sbref = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_desc-{desc}]_{suffix}/",
    ent['type'] = 'func'
    ent['desc'] = []
    ent['suffix'] = 'reg'
    outdir_reg = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    print("Registered image: " + outfile)

    os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
    os.system('cp -p ' + entry.wd + '/reg/' + ent['task'] + str(ent['run']) + '/' + 'func_data2standard.nii.gz ' + entry.outputs + '/' + outfile)
    os.system('cp -p ' + entry.wd + '/reg/' + ent['task'] + str(ent['run']) + '/' + 'example_func2standard.nii.gz ' + entry.outputs + '/' + outfile_sbref)
    # copy registration matricies
    os.system('mkdir -p ' + entry.outputs + '/' + outdir_reg)
    os.system('cp -p ' + entry.wd + '/reg/' + ent['task'] + str(ent['run']) + '/' + '*.mat ' + entry.outputs + '/' + outdir_reg)

  # move t1w images...
  t1w = layout.get(subject=entry.pid, desc='brain', extension='nii.gz', suffix='T1w')
  t1wpath = t1w[0].path

  # output filename...
  entfunc = layout.parse_file_entities(imgpath)  # save from above
  ent = layout.parse_file_entities(t1wpath)
  if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

  # Define the pattern to build out of the components passed in the dictionary
  pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

  # Add additional info to output file entities
  ent['type'] = 'anat'
  ent['space'] = 'MNI152Nonlin2006'
  ent['desc'] = 'brain'

  outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  ent['suffix'] = 'mask'
  maskfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  print("Registered image: " + outfile)

  os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
  os.system('cp -p ' + entry.wd + '/reg/' + entfunc['task'] + str(entfunc['run']) + '/' + 'highres2standard.nii.gz ' + entry.outputs + outfile)
  os.system('cp -p ' + entry.wd + '/reg/' + entfunc['task'] + str(entfunc['run']) + '/' + 'mask2standard.nii.gz ' + entry.outputs + maskfile)

## END SAVE_REGISTRATION



def run_snr(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing


  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      t1w = layout.get(subject=entry.pid, space='T1w', desc='brain', extension='nii.gz', suffix='T1w')
      t1wpath = t1w[0].path

      if os.path.exists(entry.wd + '/snr/' + ent['task'] + str(ent['run']) +'/snr_calc/' + ent['task'] + '/' + 'snr.nii.gz') and not entry.overwrite:
          print("SNR complete...skipping: " + imgname)
          continue
          print(" ")

      # ------- Running registration: T1w space and MNI152Nonlin2006 (FSLstandard) ------- #

      s=', '
      print('Calculating SNR: ' + imgpath)

      # -------- run command  -------- #
      
      cmd = "bash " + entry.templates + "/run_snr.sh " + imgpath + " " + t1wpath + " " + entry.wd 
      name = "snr-" + ent['task'] + str(ent['run']) + "-" + ent['suffix']
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all preproc commands to finish

  return returnflag

  ## end run_snr

def save_snr(layout,entry):
  import os
  import sys

  # move outputs to permanent location...
  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
    imgpath = func.path
    imgname = func.filename

    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # Define the pattern to build out of the components passed in the dictionary
    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

    # Add additional info to output file entities
    ent['type'] = 'func'
    ent['space'] = 'MNI152Nonlin2006'
    ent['desc'] = 'preproc'
    ent['suffix'] = 'snr'

    outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    print("SNR image: " + outfile)

    os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
    os.system('cp -p ' + entry.wd + '/snr/' + ent['task'] + str(ent['run']) +'/snr_calc/' + ent['task'] + '/' + 'snr.nii.gz ' + entry.outputs + '/' + outfile)

#  --------------------- complete -------------------------- #

def run_outliers(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      imgpath = func.path
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      # run from preproc images...
      img1=ent['task'] + str(ent['run'])+".nii.gz"
      img2=ent['task'] + str(ent['run'])+"_mcf.nii.gz"
      path=entry.wd + '/preproc/'

      if os.path.exists(entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_fd_outliers.tsv') and not entry.overwrite:
          print("Outlier Detection complete...skipping: " + ent['task'] + str(ent['run']))
          continue
          print(" ")

      # ------- Running registration: T1w space and MNI152Nonlin2006 (FSLstandard) ------- #

      s=', '
      print('Calculating Outliers: ' + imgpath)

      # -------- run command  -------- #
      
      cmd = "bash " + entry.templates + "/run_outliers.sh " + path+img1 + " " + path+img2 + " " + entry.wd 
      name = "outlier-" + ent['task'] + str(ent['run']) + "-" + ent['suffix']
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all preproc commands to finish

  return returnflag

  ## end run_outliers

def save_outliers(layout,entry):
  import os
  import sys

  # move outputs to permanent location...
  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
    imgpath = func.path
    imgname = func.filename

    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # compile all outputs to single confounds file
    workingpath=entry.wd + '/preproc/'
    generate_confounds_file(workingpath,ent['task'] + str(ent['run']))


    # Define the pattern to build out of the components passed in the dictionary
    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.tsv",

    # Add additional info to output file entities
    ent['type'] = 'func'
    ent['space'] = []
    ent['desc'] = 'preproc'
    ent['suffix'] = 'confounds'

    outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    print("Outliers file: " + outfile)

    os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
    os.system('cp -p ' + entry.wd + '/preproc/' + ent['task'] + str(ent['run']) + '_confounds.tsv ' + entry.outputs + '/' + outfile)

    #save_outliers


def run_fast(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  returnflag=False

  # check if output exists already
  if os.path.exists(entry.wd + '/segment/t1w_brain_seg.nii.gz') and not entry.overwrite:
    print('Tissue Segmentation output exists...skipping')

  else:         # Run BET
    print("\nRunning FAST...\n")
    t1w=layout.get(subject=entry.pid, extension='nii.gz', suffix='T1w')
    t1w=t1w[0]
    imgpath = t1w.path
    imgname = t1w.filename
    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    

    # -------- run command  -------- #
    cmd = "bash " + entry.templates + "/run_fast.sh " + imgpath + " " + entry.wd
    name = "fast" 
    p = multiprocessing.Process(target=worker, args=(name,cmd))
    p.start()
    print(p)
    returnflag=True

    p.join()  # blocks further execution until job is finished
  return returnflag

def save_fast(layout,entry):
  import os
  import sys

  t1w=layout.get(subject=entry.pid, extension='nii.gz', suffix='T1w')
  imgpath=t1w[0].path

  # output filename...
  ent = layout.parse_file_entities(imgpath)
  if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)
  # Define the pattern to build out of the components passed in the dictionary
  pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz"

  # Add additional info to output file entities
  ent['type'] = 'anat'
  ent['space'] = 'T1w'
  ent['desc'] = 'whitematter'
  ent['suffix'] = 'mask'
  out_wm_mask = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  ent['desc'] = 'greymatter'
  out_gm_mask = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  ent['desc'] = 'csf'
  out_csf_mask = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

  os.system('mkdir -p $(dirname ' + entry.outputs + '/' + out_wm_mask + ')')
  os.system('cp -p ' + entry.wd + '/segment/t1w_brain_seg_0.nii.gz ' + entry.outputs + "/" + out_csf_mask)
  os.system('cp -p ' + entry.wd + '/segment/t1w_brain_seg_1.nii.gz ' + entry.outputs + "/" + out_gm_mask)
  os.system('cp -p ' + entry.wd + '/segment/t1w_brain_seg_2.nii.gz ' + entry.outputs + "/" + out_wm_mask)
    
  ## end save_fast


def run_aroma_icamodel(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing


  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      t1w = layout.get(subject=entry.pid, space='T1w', desc='brain', extension='nii.gz', suffix='T1w')
      t1wpath = t1w[0].path

      if os.path.exists(entry.wd + '/aroma/' + ent['task'] + str(ent['run']) +'_aroma_noHP.feat' + '/' + 'filtered_func_data.nii.gz') and not entry.overwrite:
          print("AROMA model complete...skipping: " + imgname)
          continue
          print(" ")

      # ------- Running registration: T1w space and MNI152Nonlin2006 (FSLstandard) ------- #
      fsf_template = entry.templates + "/models/aroma_noHP.fsf"
      stdimg = os.popen('echo $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz').read().rstrip()

      s=', '
      print('Running AROMA Model: ' + imgpath)


      # -------- run command  -------- #

      cmd = "bash " + entry.templates + "/run_aroma_model.sh " + imgpath + " " + t1wpath + " " + fsf_template + " " + stdimg + " " + entry.wd 
      name = "aroma-model-" + ent['task'] + str(ent['run']) 
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all aroma model commands to finish

  return returnflag
  ## end run_aroma_icamodel


def run_aroma_classify(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing


  jobs=[];
  returnflag=False

  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)
      if 'run' in ent:
        ent['run']=str(ent['run']).zfill(2)

      t1w = layout.get(subject=entry.pid, space='T1w', desc='brain', extension='nii.gz', suffix='T1w')
      t1wpath = t1w[0].path

      if os.path.exists(entry.wd + '/aroma/aroma_classify/' + ent['task'] + str(ent['run']) + '/' + 'denoised_func_data_nonaggr.nii.gz') and not entry.overwrite:
          print("AROMA classification complete...skipping: " + ent['task'] + str(ent['run']) )
          continue
          print(" ")

      # check necessary input exists
      if not os.path.exists(entry.wd + '/aroma/' + ent['task'] + str(ent['run']) +'_aroma_noHP.feat' + '/' + 'filtered_func_data.nii.gz'):
        raise Exception("Cannot identify aroma feat model intended for aroma classification:" +ent['task'] + str(ent['run']) )

      # ------- Running registration: T1w space and MNI152Nonlin2006 (FSLstandard) ------- #
      
      print('Running classification Model: ' + ent['task'] + str(ent['run']) )


      # -------- run command  -------- #
      featdir=entry.wd + '/aroma/' + ent['task'] + str(ent['run']) +'_aroma_noHP.feat'
      outdir=entry.wd + '/aroma/aroma_classify/' + ent['task'] + str(ent['run'])

      cmd = "bash " + entry.templates + "/run_aroma_classify.sh " + featdir + " " + outdir 

      name = "aroma-classify-" + ent['task'] + str(ent['run']) 
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      print(p)
      returnflag=True

  for job in jobs:
    job.join()  # wait for all preproc commands to finish

  return returnflag


def save_aroma_outputs(layout,entry):
  import os
  import sys

  # move outputs to permanent location...
  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
    imgpath = func.path
    imgname = func.filename

    # output filename...
    ent = layout.parse_file_entities(imgpath)
    if 'run' in ent:
      ent['run']=str(ent['run']).zfill(2)

    # Define the pattern to build out of the components passed in the dictionary
    pattern = "fmripreproc/sub-{subject}/[ses-{session}/][{type}/]sub-{subject}[_ses-{session}][_task-{task}][_acq-{acquisition}][_rec-{reconstruction}][_run-{run}][_echo-{echo}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz",

    # Add additional info to output file entities
    ent['type'] = 'func'
    ent['space'] = 'native'
    ent['desc'] = 'smoothAROMAnonaggr'
    ent['suffix'] = 'bold'

    outfile = layout.build_path(ent, pattern, validate=False, absolute_paths=False)

    print("AROMA image: " + outfile)

    os.system('mkdir -p $(dirname ' + entry.outputs + '/' + outfile + ')')
    infile = entry.wd + '/aroma/aroma_classify/' + ent['task'] + str(ent['run']) + '/' + 'denoised_func_data_nonaggr.nii.gz'
    os.system('cp -p ' + infile + ' ' + entry.outputs + '/' + outfile)

def generate_confounds_file(path,task):
  import os
  import sys
  import pandas as pd

  # after running fsl outliers - put all coundounds into one file
  
  df=pd.DataFrame()

  files = ["dvars_metrics", "fd_metrics" ]
  for f in files:
    d=pd.read_csv(path + "/" + task + "_" + f + ".tsv",sep="\s+")  

    colnames = f.strip("metrics").strip("_")

    d.columns = [colnames]
    df = pd.concat([df,d],axis=1)

  files = ["dvars_outliers", "fd_outliers" ]
  for f in files:
    if os.path.exists(path+"/"+ task + "_" + f + ".tsv"):
      d=pd.read_csv(path+"/"+ task + "_" + f + ".tsv",sep="\s+")  

      mylist=list(range(0,d.shape[1])) 
      colnames = [f + "_" + str(s) for s in mylist]

      d.columns = colnames
      df = pd.concat([df,d],axis=1)

  # output a single confounds file
  df.to_csv(path +"/"+ task + "_confounds.tsv",sep="\t")

  # END GENERATE_CONFOUNDS_FILE


# def run_aroma_preprocess(layout,entry):
#   # run second motion correction - seems uncessesary??

def generate_report():
  # generates a summary report of the preprocessing pipeline.
  # 1. registration quality (fsl images)
  # 2. outlier detection (plot)
  # 3. carpet plot for each func? - before / after aroma?
  # 4. description of methods

  return True


  # generate snr tests...
  # /projects/ics/software/fsl/6.0.3/bin/slicer highres2standard standard -s 2 -x 0.35 sla.png -x 0.45 slb.png -x 0.55 slc.png -x 0.65 sld.png -y 0.35 sle.png -y 0.45 slf.png -y 0.55 slg.png -y 0.65 slh.png -z 0.35 sli.png -z 0.45 slj.png -z 0.55 slk.png -z 0.65 sll.png ; /projects/ics/software/fsl/6.0.3/bin/pngappend sla.png + slb.png + slc.png + sld.png + sle.png + slf.png + slg.png + slh.png + sli.png + slj.png + slk.png + sll.png highres2standard1.png
  # /projects/ics/software/fsl/6.0.3/bin/fsl_tsplot -i prefiltered_func_data_mcf.par -t 'MCFLIRT estimated translations (mm)' -u 1 --start=4 --finish=6 -a x,y,z -w 640 -h 144 -o trans.png
   


def run_cleanup(entry):

  import os
  import sys
  import subprocess
  import multiprocessing

  jobs=[];

  #concatenate and move logs to final dir...

  # remove working directory if requested...


  if entry.cleandir == True:

    os.system('rm -Rf ' + entry.wd)
      
    ## end run_cleanup


def main(argv):
  import glob
  import re
  import os
  import sys
  import warnings

  # get user entry
  entry = parse_arguments(argv)

  os.makedirs(entry.wd, mode=511, exist_ok=True)
  logdir = entry.wd + '/logs'

  os.makedirs(logdir, mode=511, exist_ok=True)

  # get participant bids path:
  bids = bids_data(entry)

  # pipeline: (1) BET, (2) topup, (3) distortion correction, (4) mcflirt
  # bet
  if run_bet(bids,entry):
    save_bet(bids,entry)

  # distortion correction
  run_topup(bids,entry)
  run_distcorrepi(bids,entry)

  # motion correction + trim
  if run_preprocess(bids,entry):
    save_preprocess(bids,entry)

  # add derivatives to bids object
  bids.add_derivatives(entry.outputs + '/fmripreproc/')

  # registration
  if run_registration(bids,entry):
    save_registration(bids,entry)

  # snr
  if run_snr(bids,entry):
    save_snr(bids,entry)

  # generate confounds
  run_outliers(bids,entry)
  save_outliers(bids,entry)

  # fast
  if run_fast(bids,entry):
    save_fast(bids,entry)

  # aroma
  if run_aroma_icamodel(bids,entry) or run_aroma_classify(bids,entry):
    save_aroma_outputs(bids,entry)

  save_bet(bids,entry)
  save_preprocess(bids,entry)
  save_registration(bids,entry)
  save_snr(bids,entry)
  save_fast(bids,entry)
  save_aroma_outputs(bids,entry)
  # clean-up
  # run_cleanup(entry)
    
__version__ = "0.0.2"  # version is needed for packaging

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
