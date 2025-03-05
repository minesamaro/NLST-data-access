"""
Script to process csv abnormalities of the NLST dataset and extract paths to slices or folders with abnormalities.

This script takes a CSV file with patient IDs (pids), study year, abnormality description and slice numbers (if 2D slice wanted), processes the available NLST data
to find the best slice or folder for each patient, and saves the results to a specified CSV file.

Usage:
    python script_name.py --df 'path_to_csv' --save 'path_to_save_csv' --NLST_data_path 'path_to_NLST_data' --slice_or_folder 'slice_or_folder_flag'

Arguments:
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

Returns:
    Saves CSV file with the paths to the slices or folders with the abnormalities in the abnormalities data CSV and information about the manufacturer, kernel, series number and slice thickness.
    Colummns in the saved CSV file:
        - pid: Patient ID.
        - study_yr: Study year.
        - sct_slice_num: Slice number (if present).
        - sct_ab_desc: Abnormality description.
        - patient_not_found: Flag to indicate if the patient is not found in the NLST data.
        - study_yr_not_found: Flag to indicate if the study year is not found in the NLST data for that patient.
        - path: Path to the slice or folder with the abnormality.
        - manufacturer: Manufacturer of the CT scanner.
        - kernel: Convolution kernel used for the reconstruction.
        - series_number: Series number of the slice.
        - slice_thickness: Thickness of the slice.
        - slice_not_found: Flag to indicate if the slice is not found in the NLST data.
        - wrong_slice_annotation: Flag to indicate if the slice number in the path is different from the expected slice number. 
        !!! warning " It is recommended not to use data where wrong_slice_annotation is True, as the dataset annotations might be wrong."


                             
Example:
    python script_name.py --df 'participant_data.csv' --save 'results.csv' --NLST_data_path '/path/to/data' --slice_or_folder 'slice'
    
    Or using the default values while in SLURM environment:
    python script_name.py --df 'participant_data.csv'
    
"""

import os
import pandas as pd
import pydicom
import argparse

def get_pid_paths(pid, data_path):
    """
    Get the path of the patient with the given pid.

    Args:
        pid (str): Patient ID.
        data_path (str): Path to the NLST data folder.

    Returns:
        folders (list): List of paths to the patient's folders.
        None: If the patient is not found.

    """
    # Get the path of the patient with pid
    path = os.path.join(data_path, str(pid))
    # Get the list of the folders in the path if they exist
    try:
        folders = os.listdir(path)
        folders =[os.path.join(path, folder) for folder in folders] 
    except FileNotFoundError:
        return None
    
    return folders

def get_study_yr_series(study_yr, folders):
    """
    Get the series folders for the specified study year.
    These refer to the folders of the examinations made in the wanted study year.

    Args:
        study_yr (int): Study year.
        folders (list): List of folders.

    Returns:
        series_folders (list): List of series folders.
        None: If the study year is not found.
    """
    # Get the folder with the study year
    study_folder = [folder for folder in folders if f'01-02-{1999 + study_yr}' in folder]
    if not study_folder:
        return None
    series_folders = os.listdir(study_folder[0])
    series_folders =[os.path.join(study_folder[0], serie) for serie in series_folders] 
    return series_folders

def get_slice_paths(series_folders, sct_slice_num):
    """
    Get the paths to the slices with the specified slice number.

    Args:
        series_folders (list): List of series folders.
        sct_slice_num (int): Slice number.

    Returns:
        slice_paths (list): List of paths to the slices in all the series folders (some may not exist)
    """
    # Go to each series folder and get the slice with the sct_slice_num
    slice_paths =[] 
    for serie in series_folders:
        # Get the path of the slice, the name of the slice is 1-xxx.dcm with 3 digits
        path = f'{serie}/1-{sct_slice_num:03}.dcm'
        slice_paths.append(path)
    return slice_paths

def get_preference_rank(manufacturer, kernel):
    """
    Get the preference rank of the convolution kernel for a manufacturer.
    Based on the paper Suplementary Information from the paper by Ardila et al. "End-to-end lung cancer screening with three-dimensional deep learning 
    on low-dose chest computed tomography" Nat Med 25, 954–961 (2019). https://doi.org/10.1038/s41591-019-0447-x

    The preference rank defines the preference of the reconstruction kernel for each manufacturer, based on harder kernels commonly used in lung imaging in medical practise.

    Higher rank means the kernel is less preferred.

    Args:
        manufacturer (str): Manufacturer name.
        kernel (str): Convolution kernel name.

    Returns:
        int: Preference rank.
    """
    # Preference orders for different manufacturers
    preference_order = {
        'SIEMENS': ['B50f', 'B45f', 'B50s', 'B40f', 'B41s', 'B60f', 'B60s', 'B70f', 'B36f', 'B35f', 'B30f', 'B31s'],
        'GE MEDICAL SYSTEMS': ['LUNG', 'BONE', 'BODY FILTER/BONE', 'STANDARD', 'BODY FILTER/STANDARD', 'SOFT', 'EXPERIMENTAL7', 'BODY FILTER/EXPERIMENTAL7'],
        'Philips': ['D', 'C', 'B', 'A'],
        'TOSHIBA': ['FC51', 'FC50', 'FC52', 'FC53', 'FC30', 'FC11', 'FC10', 'FC82', 'FL04', 'FC02', 'FC01', 'FL01']
    }
    if manufacturer in preference_order:
        if kernel in preference_order[manufacturer]:
            return preference_order[manufacturer].index(kernel)
    return float('inf')  # Return a high value if the kernel is not found

        
def process_dicom_files(dicom_files, slice_or_folder, slice_num_in_path = None):
    """
    Process DICOM files to find the best file based on specified criteria.

    Args:
        dicom_files (list): List of DICOM file paths.
        slice_or_folder (str): Flag to indicate if the script should return the paths to the slices or to the folders.
        slice_num_in_path (int, optional): Slice number in the path. Defaults to None.

    Returns:
        best_file_s (pd.Series): Series containing information about the best DICOM file.
        Columns: path, manufacturer, kernel, series_number, not_found, slice_thickness, wrong_slice_annotation (if slice_or_folder is 'slice')
        
    """
    # Store the data about the best file in a Series
    best_file_s = pd.Series()

    if slice_or_folder == 'slice':
        best_file_s = pd.Series(index=['path', 'manufacturer', 'kernel', 'series_number', 'not_found', 'slice_thickness', 'wrong_slice_annotation'])
    else:
        best_file_s = pd.Series(index=['path', 'manufacturer', 'kernel', 'series_number', 'not_found', 'slice_thickness'])
    
    best_file = None
    best_kernel_rank = float('inf')
    highest_series_number = -1
    wrong_slice = None

    for file_path in dicom_files:
        if slice_or_folder == 'folder':
            file_path = file_path + '/1-003.dcm'
        
        if not os.path.exists(file_path):
            continue

        ct_1 = pydicom.dcmread(file_path)

        if ct_1.SliceThickness > 5:
            continue

        manufacturer = getattr(ct_1, 'Manufacturer', None)
        convolution_kernel = getattr(ct_1, 'ConvolutionKernel', None)
        kernel_rank = get_preference_rank(manufacturer, convolution_kernel)

        if kernel_rank < best_kernel_rank or (kernel_rank == best_kernel_rank and ct_1.SeriesNumber > highest_series_number):
            best_kernel_rank = kernel_rank
            highest_series_number = ct_1.SeriesNumber
            best_file = file_path
            if slice_or_folder == 'slice':
                wrong_slice = ct_1.InstanceNumber != slice_num_in_path
                

    if best_file:
        if slice_or_folder == 'slice':
            best_file_s['path'] = best_file
        else:
            best_file_s['path'] = best_file[:-10]
        best_file_s['manufacturer'] = manufacturer
        best_file_s['kernel'] = convolution_kernel
        best_file_s['series_number'] = ct_1.SeriesNumber
        best_file_s['slice_thickness'] = ct_1.SliceThickness
        if slice_or_folder == 'slice':
            best_file_s['wrong_slice_annotation'] = wrong_slice
            
    else:
        best_file_s['not_found'] = 1

    
    return best_file_s


# DATA ACCESSING SCRIPT
# Arguments for running the script
# -- df.csv - Path to the csv with the pids of the patients with cancer diagnosis and abnormalities reported
#     It should have the columns: pid, study_yr, sct_slice_num, sct_ab_desc
# --save.csv - Path to the csv where the paths of the slices with the nodules will be saved
# --NLST_data_path - Path to the folder where the NLST data is stored
# --slice_or_folder - Flag to indicate if the path is to the slice or to the folder

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process the paths of the slices with nodules')
    parser.add_argument('--df', type=str, help='Path to the csv with the pids and study years of the abnormalities reported (if slice, required the sct_abn_desc and sct_slice_num)', required=True)
    parser.add_argument('--save', type=str, help='Path to the csv where the csv with the paths information will be saved', required = False, default=os.path.join(os.getcwd(), 'path_df.csv'))
    parser.add_argument('--NLST_data_path', type=str, help='Path to the folder where the NLST data is stored, default is SLURM nas storage', required = False, default='/nas-ctm01/sas-storage/data01/NLST')
    parser.add_argument('--slice_or_folder', type=str, help='Flag to indicate if the script should return the paths to the slices or to the folders of the abnormalities in the abnormalities data csv', required = False, default='slice')
    args = parser.parse_args()


    # Load the csv with the pids of the patients with cancer diagnosis and abnormalities reported
    participant_abn_data = pd.read_csv(args.df, low_memory=False)
    if args.slice_or_folder != 'slice' and args.slice_or_folder != 'folder':
        args.slice_or_folder = 'slice'
        # Give a warning that the flag is not correct and the default value is used
        print("The flag --slice_or_folder is not correct, the default value 'slice' will be used")

    if args.slice_or_folder == 'slice':
        # Select only the patients with abnormalities 51
        participant_abn_data = participant_abn_data[participant_abn_data['sct_ab_desc'] == 51]
    
    # Common columns to all the dataframes
    participant_abn_data['patient_not_found'] = None
    participant_abn_data['study_yr_not_found'] = None
    participant_abn_data['path'] = None
    participant_abn_data['manufacturer'] = None
    participant_abn_data['kernel'] = None
    participant_abn_data['series_number'] = None
    participant_abn_data['slice_thickness'] = None

    if args.slice_or_folder == 'slice':
        participant_abn_data['slice_not_found'] = None
        participant_abn_data['wrong_slice_annotation'] = None

    
    
    # Create the list of the paths of the slices with the nodules
    # Load and show the slices with the nodules
    path_df = pd.DataFrame()

    # PID is stored as a string e.g.: '100012'
    # study year is stored as int e.g. 0
    # sct_slice_num is stored as int e.g. 38
    for index, row in participant_abn_data.iterrows():
        pid = str(int(row['pid']))
        study_yr = int(row['study_yr'])
        if args.slice_or_folder == 'slice':
            sct_slice_num = int(row['sct_slice_num'])
        else:
            sct_slice_num = None

        # 1 - Access all Exminations of the patient
        folders = get_pid_paths(pid, args.NLST_data_path)

        #PID NOT IN THE DATABASE
        # Document the patients that are not found
        if folders is None:
            participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)), 'patient_not_found'] = 1
            continue

        # Get the series of the study year (examinations made in the same year)
        series_folders = get_study_yr_series(study_yr, folders)

        # Document the study years that are not found
        if series_folders is None:
            participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'study_yr_not_found'] = 1
            continue

        if args.slice_or_folder == 'slice':
            # Get the slice corresponding to the series with highest quality
            slice_path = get_slice_paths(series_folders, sct_slice_num)
        else:
            slice_path = series_folders
        
        
        correct_slice = process_dicom_files(slice_path, args.slice_or_folder, sct_slice_num)

        # Append the slice path to the dataframe
        participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'path'] = correct_slice['path']
        participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'manufacturer'] = correct_slice['manufacturer']
        participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'kernel'] = correct_slice['kernel']
        participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'series_number'] = correct_slice['series_number']
        participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'slice_thickness'] = correct_slice['slice_thickness']

        if args.slice_or_folder == 'slice':
            participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'slice_not_found'] = correct_slice['not_found']
            participant_abn_data.loc[(participant_abn_data['pid'] == int(pid)) & (participant_abn_data['study_yr'] == study_yr), 'wrong_slice_annotation'] = correct_slice['wrong_slice_annotation']

    participant_abn_data.to_csv(args.save, index=False)

