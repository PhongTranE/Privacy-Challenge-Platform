import csv
import json
import datetime
from src.constants.core_msg import SEPARATOR

from collections import defaultdict

# Default function for dictionary structure
def dict_structure(): return defaultdict(int)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
#                    METRIC NAME: MOVEMENTS MADE                     
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# PURPOSE:
# This metric calculates the **difference in coverage area** of an individual 
# over the **12 weeks of study**.
#
# The idea is as follows:
# - The metric ensures that, overall, the **anonymized version preserves** 
#   an individual’s **movement patterns** and **coverage areas**.
# - To achieve this, we measure the **number of distinct cells** where the user has stayed.
#
# SCORE CALCULATION:
#   - **Sum over all individuals (i):** 
#       - If `num_cells_original > num_cells_anonymized`:  
#           `score = num_cells_anonymized / num_cells_original`
#       - Otherwise:  
#           `score = num_cells_original / num_cells_anonymized`
#
# The final score is normalized **to a value between 0 and 1**.
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

##############################
# --- CELL SIZE CONFIGURATION --- #
##############################
size = 2
#  4 : cell at the meter level
#  3 : cell at the street level
#  2 : cell at the neighborhood level
#  1 : cell at the city level
#  0 : cell at the regional level (France)
# -1 : cell at the country level

def main(original_file, anonymized_file, parameters=None):
    """Compute the movement-based utility score by comparing original and anonymized data."""

    if parameters is None:
        parameters = {"size": 2}

    global size
    size = parameters.get("size", 2)

    # Open original and anonymized files
    with open(original_file, newline='') as fd_original, open(anonymized_file, newline='') as fd_anonymized:
        original_reader = csv.reader(fd_original, delimiter=separator)
        anonymized_reader = csv.reader(fd_anonymized, delimiter=separator)

        original_cells = defaultdict(dict_structure)
        anonymized_cells = defaultdict(dict_structure)

        for line_ori, line_ano in zip(original_reader, anonymized_reader):
            # --- Process original file ---
            user_id = line_ori[0]
            gps_original = (round(float(line_ori[2]), size), round(float(line_ori[3]), size))
            original_cells[user_id][gps_original] += 1

            # --- Process anonymized file ---
            if line_ano[0] != "DEL":
                gps_anonymized = (round(float(line_ano[2]), size), round(float(line_ano[3]), size))
                anonymized_cells[user_id][gps_anonymized] += 1

    # Count the number of unique visited locations per user
    final_original_cells = {user_id: len(original_cells[user_id]) for user_id in original_cells}
    final_anonymized_cells = {user_id: len(anonymized_cells[user_id]) for user_id in original_cells}

    total_users = len(final_original_cells)
    score = 0

    for user_id in final_original_cells:
        if final_original_cells[user_id] > final_anonymized_cells[user_id]:
            score += final_anonymized_cells[user_id] / final_original_cells[user_id]
        else:
            score += final_original_cells[user_id] / final_anonymized_cells[user_id]

    return score / total_users if total_users > 0 else 0  # Prevent division by zero