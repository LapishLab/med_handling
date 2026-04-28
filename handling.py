from pathlib import Path
from shutil import copy2
from datetime import datetime
from pathlib import Path
import sys
from parsing import parse_all_files_in_folder, get_datetime_from_parsed_med
import pandas as pd
from scipy.io import savemat
import json
import pickle
import logging

def batch_copy_med(base_dir):
    base_dir = Path(base_dir)
    session_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    for session_dir in session_dirs:
        copy_med_files_to_box(session_dir)

def copy_med_files_to_box(dir_path):
    """
    dir_path: path to the session directory
    """
    dir_path = Path(dir_path)

    # Locate the med-pc folder
    medpc_folder = find_subfolder(dir_path, pattern="med-pc")
    if not medpc_folder:
        logging.warning(f"\nNo med-pc folder found for:\n {dir_path}")
        return False

    # Parse each med file and start saving info in a dataframe
    (path, parsed) = parse_all_files_in_folder(medpc_folder)
    med_table = pd.DataFrame({'path': path, 'parsed': parsed})

    # Each med file timestamp should be within 30 minutes of the session timestamp
    session_time = get_session_time(dir_path)

    try:
        med_table['datetime'] = med_table['parsed'].apply(get_datetime_from_parsed_med)
    except Exception as e:
        logging.warning(f"Error occurred while parsing Start time/date for med files in {dir_path}: {e}")
        return False    

    tdiff = (session_time - med_table['datetime']) / pd.Timedelta(minutes=1) # Time diff in minutes
    within_limits = tdiff.abs() < 40
    if not within_limits.all():
        bad_med = [p.name for p in med_table['path'].loc[~within_limits]]
        logging.warning("\nMed timestamps differ from session by more than 40 minutes \n" +
             f"    Session: {dir_path}\n" +
              "    Skipping the following med files:\n        " + 
             '\n        '.join(bad_med))
        med_table = med_table.loc[within_limits] # Keep only the med files within the time limits

    # Move the med files into the appropriate Box folders
    box_paths = get_box_paths(dir_path)
    if not box_paths:
        logging.warning(f"\nNo Box folders found for:\n {dir_path}")
        return False
    med_table['box'] = med_table['parsed'].apply(get_box_from_parsed_med)
    for r in med_table.itertuples():
        matching_box = [bp for bp in box_paths if bp.name.endswith(r.box)]
        if not matching_box:
            logging.warning(f"No matching box folder found for med file {r.path.name} (box {r.box})")
            continue
        if len(matching_box) >1:
            raise ValueError(f"Multiple matching box folders found for med file {r.path} with Box={r.box}: {[str(bp) for bp in matching_box]}")   
        matching_box = matching_box[0]
        box_paths.remove(matching_box) # Remove this box from the list
        med_out_folder = matching_box / "med"
        med_out_folder.mkdir(exist_ok=True)
        copy2(r.path, med_out_folder) # Copy the original med file (keep the original filename)

        # Also save the parsed med data as .mat, .json, and .pkl
        med_name = med_out_folder / "med.mat"
        mat_parsed = make_mat_safe_dict(r.parsed)
        savemat(med_name, mat_parsed)

        json_name = med_out_folder / "med.json"
        with open(json_name, 'w', encoding='utf-8') as f:
            json.dump(r.parsed, f, indent=4)

        pickle_name = med_out_folder / "med.pkl"
        with open(pickle_name, 'wb') as f:
            pickle.dump(r.parsed, f)

    if (box_paths):
        logging.warning("\nNo med files found for the following Box folders:\n" + 
              f"    Session: {dir_path}\n" +
              "    Unmatched Box folders:\n        " + 
              '\n        '.join(bp.name for bp in box_paths))
    return True

def get_box_from_parsed_med(parsed):
    box = parsed.get("Box", None)
    if box:
        box = int(box) # Convert to integer if possible
        box = str(box).zfill(2) # Pad with zeros to ensure 2 digits
    return box
    
def get_box_paths(dir_path):
    pi_folder = find_subfolder(dir_path, pattern="pi-data")
    if not pi_folder:
        return None
    return [p for p in pi_folder.iterdir() if p.is_dir() and p.name.lower().startswith("box")]

def find_subfolder(dir_path,pattern):
    dir_path = Path(dir_path)
    subfolders = [p for p in dir_path.iterdir() if p.is_dir() and p.name.startswith(pattern)]
    if len(subfolders) != 1:
        return None
    return subfolders[0]

def get_session_time(session_path):
    # Extract datetime from session folder name
    session_path = Path(session_path)
    date_str = session_path.name[:19] # "YYYY-MM-DD_HH-MM-SS" is 19 characters long
    return datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")

def make_mat_safe_dict(d):
    # MATLAB reserved keywords
    matlab_keywords = {
        'break', 'case', 'catch', 'classdef', 'continue', 'else', 'elseif', 
        'end', 'for', 'function', 'global', 'if', 'otherwise', 'parfor', 
        'persistent', 'return', 'spmd', 'switch', 'try', 'while'
    }

    for original_key in list(d.keys()):
        key = original_key.replace(' ', '_') # Replace spaces with underscores
        if len(key) > 63:
            key = key[:63] # Truncate to 63 characters
        if key in matlab_keywords or not key[0].isalpha():
            key = 'var_' + key # Add _var to reserved or non-alpha-starting keys
        d[key] = d.pop(original_key) # Save the new key and remove the old key
    return d

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise("Error: Provide starting folder path as 1st positional argument.")
    batch_copy_med(sys.argv[1])