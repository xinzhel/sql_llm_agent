# read all the 'txt' files in templates/
import os
import glob
import re
from typing import List, Dict, Tuple

def read_template_from_txt_files(directory="templates/sql/", print_statistics=True) -> Dict[str, List[str]]:
    """ Read all the txt files in the directory and return a dictionary of lists
    where the key is the table name and the value is a list of templates.
    """
    # Path to the directory
    directory_path = directory

    # List to hold the contents of each txt file
    file_contents = {}

    # Loop through all txt files in the directory
    for filepath in glob.glob(os.path.join(directory_path, '*.txt')):
        # file name
        filename = filepath.split('/')[-1][:-4]
        with open(filepath, 'r') as file:
            # read a list of lines
            content = file.readlines()
            # remove whitespace characters like `\n` at the end of each line
            content = [x.strip() for x in content]
            file_contents[filename] = content

    if print_statistics:
        print("Number of templates for each table:")
        for key, value in file_contents.items():
            print(key, len(value))

        print("Total number of templates: ", sum([len(file_contents[table]) for table in file_contents]))

    return file_contents
