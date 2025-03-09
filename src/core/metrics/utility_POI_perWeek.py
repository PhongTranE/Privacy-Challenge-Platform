import csv
import json
import datetime
from src.constants.core_msg import SEPARATOR 

from collections import defaultdict

# Default functions for handling missing values
def default_timedelta(): return datetime.timedelta()
def default_none(): return None
def nested_defaultdict(): return defaultdict(default_timedelta)
def deep_nested_defaultdict(): return defaultdict(nested_defaultdict)

# Lambda function to find the max value in a dictionary
max_dict = lambda d: max(d, key=lambda key: d[key])

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
#          METRIC NAME: EXTRACTION OF POINTS OF INTEREST           
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# PURPOSE:
# This metric detects an individual's **points of interest (POIs)**.
# Points of interest correspond to the locations where the user has spent the most time.
#
# In this utility function, we analyze **one POI per week per individual** by default.
# A POI corresponds to three main locations:
#   - **Home** (22:00 to 06:00)
#   - **Workplace** (09:00 to 16:00)
#   - **Activity location** (Weekends from 10:00 to 18:00)
#
# The goal is to **verify whether the key locations in an individual’s life** are retained in the anonymized dataset.
#
# SCORE CALCULATION:
#   - **Sum over all individuals (i):** 
#       - **Sum over all POIs:** 
#           - If `POI_time_original > POI_time_anonymized`:  
#               `score = POI_time_anonymized / POI_time_original`
#           - Otherwise:  
#               `score = POI_time_original / POI_time_anonymized`
#
# The final score is normalized to **a value between 0 and 1**.
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

#######################################
# --- SIZE OF POINTS OF INTEREST --- #
#######################################
size = 2
# 4 : cell at the meter level
# 3 : cell at the street level
# 2 : cell at the neighborhood level
# 1 : cell at the city level
# 0 : cell at the region level
# -1 : cell at the country level

######################################
# --- NUMBER OF POIs TO VERIFY PER ID --- #
######################################
num_POIs = 1
# 3: Check the top 3 most visited POIs in terms of time spent.

################################
# --- TIME INTERVAL DEFINITIONS --- #
################################
# Time intervals for detecting POIs (night, work, and weekend):
night_start, night_end = 22, 6  # From 22:00 to 06:00
work_start, work_end = 9, 16  # From 09:00 to 16:00
weekend_start, weekend_end = 10, 18  # From 10:00 to 18:00 (weekends)

def get_top_POIs(poi_dict):
    """Retrieve the top POIs based on time spent."""
    result = defaultdict(default_timedelta)
    for _ in range(num_POIs):
        if len(poi_dict) == 0:
            break
        key = max_dict(poi_dict)
        result[key] = poi_dict[key]
        del poi_dict[key]
    return result

# Track last recorded timestamps for original and anonymized data
last_date_original = defaultdict(default_none)
last_date_anonymized = defaultdict(default_none)

def compute_time_difference(key, current_time, last_timestamp_dict):
    """Compute the time difference between two consecutive timestamps for the same user."""
    if last_timestamp_dict[key] is None:
        last_timestamp_dict[key] = current_time
        return datetime.timedelta()
    else:
        time_difference = current_time - last_timestamp_dict[key]
        last_timestamp_dict[key] = current_time
        return time_difference

def main(original_file, anonymized_file, parameters=None):
    """Compute the POI-based utility score by comparing original and anonymized data."""
    
    if parameters is None:
        parameters = {
            "size": 2,
            "num_POIs": 1,
            "night_start": 22, "night_end": 6,
            "work_start": 9, "work_end": 16,
            "weekend_start": 10, "weekend_end": 18
        }

    # Update global parameters
    global size, num_POIs, night_start, night_end, work_start, work_end, weekend_start, weekend_end
    size = parameters.get("size", 2)
    num_POIs = parameters.get("num_POIs", 1)
    night_start = parameters.get("night_start", 22)
    night_end = parameters.get("night_end", 6)
    work_start = parameters.get("work_start", 9)
    work_end = parameters.get("work_end", 16)
    weekend_start = parameters.get("weekend_start", 10)
    weekend_end = parameters.get("weekend_end", 18)

    # Open original and anonymized files
    with open(original_file, newline='') as fd_original, open(anonymized_file, newline='') as fd_anonymized:
        original_reader = csv.reader(fd_original, delimiter=SEPARATOR)
        anonymized_reader = csv.reader(fd_anonymized, delimiter=SEPARATOR)

        original_POIs = defaultdict(deep_nested_defaultdict)
        anonymized_POIs = defaultdict(deep_nested_defaultdict)

        for line_ori, line_ano in zip(original_reader, anonymized_reader):
            # --- Process original file ---
            user_id = line_ori[0]
            timestamp = datetime.datetime.fromisoformat(line_ori[1][:19])
            week_info = timestamp.date().isocalendar()
            key = (user_id, week_info[0], week_info[1])

            location = (round(float(line_ori[2]), size), round(float(line_ori[3]), size))

            if timestamp.weekday() < 5:  # Weekday
                if timestamp.time() > datetime.time(night_start, 0) or timestamp.time() < datetime.time(night_end, 0):
                    original_POIs[key]['night'][location] += compute_time_difference(key, timestamp, last_date_original)
                elif work_start <= timestamp.time().hour < work_end:
                    original_POIs[key]['work'][location] += compute_time_difference(key, timestamp, last_date_original)

            # --- Process anonymized file ---
            if line_ano[0] != "DEL":
                timestamp = datetime.datetime.fromisoformat(line_ano[1][:19])
                location = (round(float(line_ano[2]), size), round(float(line_ano[3]), size))

                if timestamp.weekday() < 5:  # Weekday
                    if timestamp.time() > datetime.time(night_start, 0) or timestamp.time() < datetime.time(night_end, 0):
                        anonymized_POIs[key]['night'][location] += compute_time_difference(key, timestamp, last_date_anonymized)
                    elif work_start <= timestamp.time().hour < work_end:
                        anonymized_POIs[key]['work'][location] += compute_time_difference(key, timestamp, last_date_anonymized)

    final_original_POIs = defaultdict(deep_nested_defaultdict)
    final_anonymized_POIs = defaultdict(deep_nested_defaultdict)

    for user_id in original_POIs:
        for poi_type in original_POIs[user_id]:
            final_original_POIs[user_id][poi_type] = get_top_POIs(original_POIs[user_id][poi_type])
            final_anonymized_POIs[user_id][poi_type] = get_top_POIs(anonymized_POIs[user_id][poi_type])

    total_pois = sum(len(final_original_POIs[user_id][poi_type]) for user_id in final_original_POIs for poi_type in final_original_POIs[user_id])
    score = 0

    for user_id in final_original_POIs:
        for poi_type in final_original_POIs[user_id]:
            for location in final_original_POIs[user_id][poi_type]:
                original_time = final_original_POIs[user_id][poi_type][location].total_seconds()
                anonymized_time = final_anonymized_POIs[user_id][poi_type][location].total_seconds()

                if original_time > anonymized_time:
                    score += anonymized_time / original_time
                else:
                    score += original_time / anonymized_time

    return score / total_pois if total_pois > 0 else 0