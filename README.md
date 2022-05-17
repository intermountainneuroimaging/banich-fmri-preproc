# Banich Lab fMRI Preprocessing Pipeline
Custom preprocessing pipeline built using FMRIB Software Library (FSL) v6.0 for functional neuroimaging. The pipeline is built using fsl best practices and conforms to BIDS format.  

Contents:
  - [Workflow Summary](#workfolw-summary)
  - [Installation](#installation)
  - [Bids Format](#bids-format)
  - [Command-Line Arguments](#command-line-arguments)
  - [Examples](#docker-examples)
    - [Docker](#docker)
    - [Singularity](#singularity)
- [Known Issues](#known-issues)

# Workflow Summary
_fmripreprpoc_ is a single command line tool used to run a standard fsl based preprocessing scheme for functional neuroimaging data. Key components of the pipeline include: skull stripping and tissue segmentation, fielmap estimation and distortion correction, motion correction, outlier detection, trimming, normalization to standard space, and AROMA denoising. 

![fmripreproc workflow diagram](https://github.com/intermountainneuroimaging/banich-fmri-preproc/blob/main/support_images/fmripreproc-pipeline-workflow.jpg)

"fMRI data were preprocessed using FMRIB software library (FSL). Standard processing steps including brain extraction using Brain Extraction Tool (BET), distortion correction, and motion correction using a 12 degree of freedom model were performed for each functional image. Distortion correction was applied using fieldmap images derived from B0 mapping image pairs for each functional series. The intial 10 volumes of each functional series were removed to ensure intensity stabilization. Two stage image registration were used to spatially transform all functional series to MNI152 standard space using a 6 degree of freedom model between a single band reference image and high resolution strcutral scan, followed by a 12 degree of freedom model between the subject's high resolution strucutral scan and MNI152 high resolution scan. Scrubbing was performed by first detecting all functional frames with DVARS values exceeding 75th percentile + 1.5xIQR, and framewise displacement (FD) exceeding 0.9 mm. where DVARS is computed as the root mean square of the temporal change of the fMRI voxel-wise signal (cite), and FD is computed as the sum of the absolute values of the differentiated realignment estimates (by backwards differences) at every timepoint (Power et al., 2012). Denoising was performed using AROMA, where nonagrressive noise removal was used."


```bash
    fMRI Preprocessing Pipeline
        Usage:  --in=<bids-inputs> --out=<outputs> --participant-label=<id> [OPTIONS]
        OPTIONS
          --help                      show this usage information and exit
          --participant-label=        participant name for processing (pass only 1)
          --work-dir=                 (Default: <outputs>/scratch/particiant-label) directory 
                                        path for working directory
          --clean-work-dir=           (Default: TRUE) clean working directory 
          --trimvols=                 (Default: 10) trim inital volumes from all bold scans
          --dummyscans=               (Default: 10) add dummy scan indicator variables in confounds
                                        file. DO NOT use with "trim-vols"
          --outliers-fd=              (Default: 0.9mm) generate indicator variables for framewise
                                        displacement outliers above given threshold
          --outliers-dvars=           (Default: XX) generate indicator variables for dvars outliers
                                        above given threshold
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
```


# Installation

Use the _fmripreprpoc_ Docker image (recommended):

```shell
docker run --rm amhe4269/fmripreprpoc:0.0.1 --help
```

Use the _fmripreprpoc_ Singularity image (recommended):

```shell
singularity pull fmripreprpoc docker://amhe4269/fmripreprpoc:0.0.1
singularity run amhe4269/fmripreprpoc:0.0.1 --help
```
# BIDS format
The fsl-fdt workflow takes advantage of the BIDS naming convention and supporting metadata. The input data must be in a valid BIDS format, and include at least one dwi image with accompanying bval and bvec files. Metadata including readoutime must be including in a json sidecar file for each dwi image. See [dcm2niix](https://github.com/rordenlab/dcm2niix) and [BIDS Validator](https://bids-standard.github.io/bids-validator/) for more details. 

> ### Important
> If running multiple instances of fmripreprpoc, you _MUST_ create a unique working directory for each instance to avoid loop contamination.

# Running _fmripreprpoc_ using Docker Engine
This pipeline is built with the intented to be used with docker or singularity engines. Compiled in the docker image includes all python packages and FSL version (6.0.3) for the pipeline.
```shell
$ docker run -ti --rm \
    -v path/to/data:/data:ro \
    -v path/to/output:/out \
    amhe4269/fmripreprpoc:<latest-version> /data /out --participant-label=[ID] [OPTIONS] 
```

## Docker examples

The canonical examples install ANTs version 2.3.1 on Debian 9 (Stretch).

_Note_: Do not use the `-t/--tty` flag with `docker run` or non-printable characters will be a part of the output (see [moby/moby#8513 (comment)](https://github.com/moby/moby/issues/8513#issuecomment-216191236)).

### Docker
Run the Diffusion Toolbox pipleine using docker. We first mount appropriate volumes (external directories) and assign relevant arguments including participant-label.
```shell
$ docker run -ti --rm \
    -v $studydir/BIDS:/data:ro \
    -v $studydir/ANALYSIS:/out \
    -v $studydir/tmp/ds005-workdir:/work \
    amhe4269/fmripreprpoc:<latest-version> \
    /data /out/ --participant-label=0001 --work-dir /work --clean-work-dir=FALSE
```

### Singularity
Run the Diffusion Toolbox pipleine using singularity. We first mount appropriate volumes (external directories) and assign relevant arguments including participant-label.
```shell
$ singularity run 
    -bind $studydir/BIDS:/data:ro \
    -bind $studydir/ANALYSIS:/out \
    -bind $studydir/tmp/ds005-workdir:/work \
    amhe4269/fmripreprpoc:<latest-version> \
    /data /out/ --participant-label=0001 --work-dir /work --clean-work-dir=FALSE
```

# Known Issues
Working directory must be explicitly defined (in sperate locations) if running multiple instances of fmripreprpoc pipeline on the same computational resources.
