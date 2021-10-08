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
          --work-dir=                 (Default: <outputs>/scratch) directory path for working 
                                        directory
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
      wd=outputs + "/scratch/sub-" + pid

    print('Input Bids directory:\t', inputs)
    print('Derivatives path:\t', outputs)
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
      os.makedirs(entry.outputs,exist_ok=True)
      os.makedirs(entry.outputs + '/fmripreproc', exist_ok=True)

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

def run_bet(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

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

    

    # -------- run command  -------- #
    cmd = "bash " + entry.templates + "/run_bet.sh " + imgpath + " " + entry.wd
    name = "bet" 
    p = multiprocessing.Process(target=worker, args=(name,cmd))
    p.start()
    print(p)

    p.join()  # blocks further execution until job is finished

def save_bet(layout,entry):
  import os
  import sys

  t1w=layout.get(subject=entry.pid, extension='nii.gz', suffix='T1w')
  imgpath=t1w[0].path

  # output filename...
  ent = layout.parse_file_entities(imgpath)
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

  ent['desc'] = 'skull'
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

  # check if output exists already
  if os.path.exists(entry.wd + '/topup/topup4_field_APPA.nii.gz') and not entry.overwrite:
    print('Topup output exists...skipping')

  else:         # Run Topup
    print("\nRunning Topup...\n")

    # check two fieldmaps collected with opposing phase encoding directions
    ap=False ; pa=False
    for fmap in layout.get(subject=entry.pid, extension='nii.gz', suffix='epi'):
        ent = fmap.get_entities()
        
        if 'AP' in ent['direction']:
          ap=True; img1=fmap.path ; meta=fmap.get_metadata()
        elif 'PA' in ent['direction']:
          pa=True ; img2=fmap.path

    if not ap and not pa:
      # continue topup... (else throw error?)
      raise Exception("Topup cannot be run...Missing AP or PA fieldmaps")

    # run script
    cmd = "bash " + entry.templates + "/run_topup.sh " + img1 + " " + img2 + " " + entry.wd + " " + str(meta['TotalReadoutTime'])
    name = "topup"
    p = multiprocessing.Process(target=worker, args=(name,cmd))
    p.start()
    print(p)

    p.join()  # blocks further execution until job is finished

    ## end run_topup

def run_distcorrepi(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  itr=0;
  nfiles = len(layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'))
  jobs=[];

  for func in layout.get(subject=entry.pid, extension='nii.gz', suffix=['bold','sbref']):
      
      imgpath = func.path
      imgname = func.filename
      # output filename...
      ent = layout.parse_file_entities(imgpath)

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

      # -------- run command  -------- #
      cmd = "bash " + entry.templates + "/run_distcorrepi.sh " + imgpath + " " + fout + " " + param + " " + entry.wd
      print(cmd)
      print(" ")
      name = "distcorr-" + ent['task'] + str(ent['run']) + "-" + ent['suffix']
      p = multiprocessing.Process(target=worker, args=(name,cmd))
      jobs.append(p)
      p.start()

      itr = itr+1
      print(p)

  for job in jobs:
    job.join()  #wait for all distcorrepi commands to finish
      
  ## end run_discorrpei

def run_preprocess(layout,entry):
  import os
  import sys
  import subprocess
  import multiprocessing

  itr=0;
  nfiles = len(layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'))
  jobs=[];

  for func in layout.get(subject=entry.pid, extension='nii.gz', suffix='bold'):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)

      
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

  for job in jobs:
    job.join()  # wait for all preproc commands to finish
      
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

  # add derivatives to bids object
  layout.add_derivatives(entry.outputs)
  
  jobs=[];

  for func in layout.get(subject=entry.pid, desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)

      t1w = layout.get(subject=entry.pid,  desc='brain', extension='nii.gz', suffix='T1w')
      t1wpath = t1w[0].path

      t1whead = layout.get(subject=entry.pid,  desc='skull', extension='nii.gz', suffix='T1w')
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

  for job in jobs:
    job.join()  # wait for all preproc commands to finish

  
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

  for func in layout.get(subject=entry.pid, space='native', desc='preproc', extension='nii.gz', suffix=['bold']):
      
      imgpath = func.path
      imgname = func.filename
      ent = layout.parse_file_entities(imgpath)

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

  for job in jobs:
    job.join()  # wait for all preproc commands to finish


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

                                             
def run_cleanup(entry):

  import os
  import sys
  import subprocess
  import multiprocessing

  jobs=[];
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

  os.makedirs(entry.wd, exist_ok=True)
  logdir = entry.wd + '/logs'

  os.makedirs(logdir, exist_ok=True)

  # get participant bids path:
  bids = bids_data(entry)

  # pipeline: (1) BET, (2) topup, (3) distortion correction, (4) mcflirt
  run_bet(bids,entry)
  save_bet(bids,entry)

  # distortion correction
  run_topup(bids,entry)
  run_distcorrepi(bids,entry)

  # motion correction + trim
  run_preprocess(bids,entry)
  save_preprocess(bids,entry)

  # registration
  run_registration(bids,entry)
  save_registration(bids,entry)

  #snr
  run_snr(bids,entry)
  save_snr(bids,entry)
  
  # clean-up
  run_cleanup(entry)
    

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
