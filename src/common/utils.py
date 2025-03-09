
#################################
#       Global functions        #
#################################
from src.constants.core_msg import *
import uuid

# Count the number of lines in csv file
def csv_length(filename):
    try:
        return sum(1 for _ in open(filename))
    except:
        return -1

# Count the number of columns in the first row of a CSV file based on a separator
def csv_width(filename):
    return sum(1 for char in next(open(filename)) if char == SEPARATOR) + 1

def checking_shape(input, default):
    length = 0
    size = (csv_length(default), csv_width(default))
    if size[0] < 0 or size[1] < 0 : 
        return (INVALID_ORIGINAL_FILE, -1) 

    try:
        for line in open(input):
            if line[0:3]!="DEL" and sum(1 for char in line if char == SEPARATOR) + 1 != size[1]:
                return (INVALID_UPLOADED_FILE_COLUMNS, length)
            length += 1
    except:
        return (INVALID_UPLOADED_FILE_FORMAT, 0)
    return (INVALID_UPLOADED_FILE_ROWS, length) if length != size[0] else 0

def generate_secure_filename():
    """
    Generates a short, unique, and secure filename.

    :return: A secure filename like '6335f2d9fa1e4047'
    """
    return uuid.uuid4().hex[:16]  # Short 16-character UUID

