# NLST Accessing Script

This documentation is under development. For more details, access documentation @[GitPage Documentation ](https://minesamaro.github.io/NLST-data-access/)


## Overview

This script processes DICOM files to extract paths to slices or folders containing abnormalities based on specified criteria. It takes input from a CSV file containing patient IDs (pids), study years, and slice numbers, and saves the results to another CSV file.

![NLST data accessing (1)](https://github.com/minesamaro/NLST-data-access/assets/87450213/7d8c89e1-0843-4d2c-9c05-f52ec3386332)

## Usage

### Arguments

    --df (str): Path to the CSV file with the pids and study years of the abnormalities reported. (REQUIRED)
                Required columns: pid, study_yr, sct_slice_num, sct_ab_desc.
                e.g. 'dbs/participant_data.csv'
    --save (str): Path to the CSV file where the paths information will be saved.
                  Default is 'path_df.csv' in the current working directory.
    --NLST_data_path (str): Path to the folder where the NLST data is stored.
                            Default is the SLURM folder'/nas-ctm01/sas-storage/data01/NLST'.
    --slice_or_folder (str): Flag to indicate if the script should return the paths to the slices or to the folders.
                             Possible values are 'slice' and 'folder'. Other values will be replaced by 'slice'.
                             Default is 'slice'.

### Example

```bash
python script_name.py --df path_to_participant_data.csv --save path_to_save_results.csv --NLST_data_path /path/to/data/NLST --slice_or_folder 'slice' 
```
