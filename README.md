# NLST Accessing Script

This documentation is under development. For more details, access documentation @[GitPage Documentation ](https://minesamaro.github.io/NLST-data-access/)


## Overview

This script processes DICOM files to extract paths to slices or folders containing abnormalities based on specified criteria. It takes input from a CSV file containing patient IDs (pids), study years, and slice numbers, and saves the results to another CSV file.

## Usage

### Arguments

- `--df <path_to_csv>`: Path to the CSV file with patient IDs and study years (REQUIRED).
    - Required columns: `pid`, `study_yr`, `sct_slice_num`, `sct_ab_desc` (only if `'slice_or_folder' == 'slice'`).
- `--save <path_to_save_csv>`: Path to save the CSV file with paths information.
    - Default: `path_df.csv` in the current working directory.
- `--NLST_data_path <path_to_NLST_data>`: Path to the folder where NLST data is stored.
    - Default: `/nas-ctm01/sas-storage/data01/NLST`.
- `--slice_or_folder <slice_or_folder_flag>`: Flag to indicate if the script should return paths to slices or folders.
    - Possible values: `slice`, `folder`.
    - Default: `slice`.

### Example

```bash
python script_name.py --df path_to_participant_data.csv --save path_to_save_results.csv --NLST_data_path /path/to/data/NLST --slice_or_folder 'slice' 
```
