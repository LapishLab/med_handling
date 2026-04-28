from datetime import datetime
from pathlib import Path


def parse_all_files_in_folder(folder_path):
    folder_path = Path(folder_path)
    path = []
    parsed = []
    for file in folder_path.iterdir():
        if file.is_file():
            parsed.append(parse_med_file(file))
            path.append(file)
    return (path, parsed)

def parse_med_file(path):
    arrays = read_arrays(path)
    parsed =  [parse_array(a) for a in arrays]
    return dict(parsed)

def parse_array(array):
    # Split each row of the array by the colon
    keys =[]
    data =[]
    for a in array:
        (k, _, d) = a.partition(':')
        keys.append(k.strip())
        data.append(d.strip())
    
    # Only keep the key for the first line (the rest are just value indexes)
    key = keys[0]

    # If there are multiple rows, split each row by whitespace and merge into single row
    if len(data)>1:
        split_rows = [row.split() for row in data if row]
        data = [val for row in split_rows for val in row if val]
    
    # Convert data to numbers if possible
    try:
        data = [float(d) for d in data]
    except:
        pass

    # Remove trailing zeros
    while len(data)>1 and data[-1] == 0:
        data.pop()

    # If only 1 item is in the data list, pull it out of list
    if len(data)==1:
        data = data[0]

    return (key, data)
        

def read_arrays(path):
    all_arrays = []
    current_array = []

    with open(path, "r") as file:
        for line in file:
            if line[0].isspace(): # if the line starts with a space
                if line.strip(): # and isn't empty
                    current_array.append(line) # Add it to the current array
            else: # if the line doesn't start with a space
                if current_array: # and the current array isn't empty
                    all_arrays.append(current_array) # save the current array
                current_array = [line] # and start a new current array starting with this line
    return all_arrays

def get_datetime_from_parsed_med(parsed):
    date = datetime.strptime(parsed["Start Date"], "%m/%d/%y")  # MM/DD/YY
    time = datetime.strptime(parsed["Start Time"], "%H:%M:%S")  # HH:MM:SS
    return datetime.combine(date.date(), time.time())