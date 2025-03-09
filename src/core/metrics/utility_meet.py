import csv
import json
from collections import defaultdict
from src.constants.core_msg import SEPARATOR 

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
#                      METRIC NAME: CROSSINGS                        
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# PURPOSE:
# This metric identifies the cells where the highest number of users circulate.

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

#############################################################
# --- PERCENTAGE OF MOST VISITED CELLS TO VERIFY --- #
#############################################################
pt = 0.1
# 0.1: 10% of the most visited cells must be present in 10% of the cells 
# in the anonymized file.

def main(original_file, anonymized_file, parameters=None):
    """Compute the crossing metric comparing original and anonymized data."""

    # Define global variables
    if parameters is None:
        parameters = {"size": 2, "pt": 0.1}

    global size
    size = parameters.get("size", 3)
    global pt
    pt = parameters.get("pt", 0.2)

    # Open original and anonymized files
    fd_original = open(original_file, newline='')
    fd_anonymized = open(anonymized_file, newline='')
    original_reader = csv.reader(fd_original, delimiter=SEPARATOR)
    anonymized_reader = csv.reader(fd_anonymized, delimiter=SEPARATOR)

    original_cells = defaultdict(int)
    anonymized_cells = defaultdict(int)

    for line_ori, line_ano in zip(original_reader, anonymized_reader):
        # --- Process original file
        key = (round(float(line_ori[2]), size), round(float(line_ori[3]), size))
        original_cells[key] += 1

        # --- Process anonymized file
        if line_ano[0] != "DEL":
            gps2 = (round(float(line_ano[2]), size), round(float(line_ano[3]), size))
            anonymized_cells[gps2] += 1

    num_cells_to_check = int(len(original_cells) * pt)
    score = 0

    # Sort original and anonymized cell data based on visit frequency (descending order)
    sorted_original_cells = sorted(original_cells.items(), key=lambda t: t[1], reverse=True)
    sorted_anonymized_cells = sorted(anonymized_cells.items(), key=lambda t: t[1], reverse=True)

    top_original_cells = sorted_original_cells[:num_cells_to_check]
    top_anonymized_cells = dict(sorted_anonymized_cells[:min(len(anonymized_cells), num_cells_to_check)])

    # Compute final score based on common highly visited cells
    for cell in top_original_cells:
        cell = cell[0]
        if cell in top_anonymized_cells:
            score += 1

    return score / num_cells_to_check