# NLST Accessing Script

!!! warning "This documentation is under development. For more clarification, see the "Contact Me" page"


## Overview

Script to process csv abnormalities of the NLST dataset and extract paths to slices or folders with abnormalities.

This script takes a CSV file with patient IDs (pids), study year, abnormality description and slice numbers (if 2D slice wanted), processes the available NLST data
to find the best slice or folder for each patient, and saves the results to a specified CSV file.

## Usage

### Arguments

- `--df (str)`: Path to the CSV file with the pids and study years of the abnormalities reported. (REQUIRED)
                Required columns: pid, study_yr, sct_slice_num, sct_ab_desc.
                e.g. 'dbs/participant_data.csv'
- `--save (str)`: Path to the CSV file where the paths information will be saved.
                  Default is 'path_df.csv' in the current working directory.
- `--NLST_data_path` (str): Path to the folder where the NLST data is stored.
                            Default is the SLURM folder'/nas-ctm01/sas-storage/data01/NLST'.
- `--slice_or_folder` (str): Flag to indicate if the script should return the paths to the slices or to the folders.
                             Possible values are 'slice' and 'folder'. Other values will be replaced by 'slice'.
                             Default is 'slice'.

### Example

```bash
python script_name.py --df path_to_participant_data.csv --save path_to_save_results.csv --NLST_data_path /path/to/data/NLST --slice_or_folder 'slice' 
```


