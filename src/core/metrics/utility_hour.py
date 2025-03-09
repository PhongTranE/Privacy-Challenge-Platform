import csv
from src.constants.core_msg import SEPARATOR 

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
#                      METRIC NAME: HOUR GAP                        
#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

# PURPOSE:
# This metric calculates the time gap for each row in the anonymized file.
# It ensures the authenticity of the recorded time when the GPS position was captured.
#
# The modification of the **day of the week is not penalized**. 
# For example: 
# - A GPS position recorded on Tuesday at 16:00 and moved to Wednesday at 16:00 **keeps its full utility score**.
#
# SCORE CALCULATION:
# - Each row starts with a score of 1 point.
# - A fraction of a point is deducted based on the time difference, following the `hour_penalty` table.

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

def main(original_file, anonymized_file, parameters=None):
    """Computes the utility score based on the time difference between the original and anonymized data."""

    total_score = 0
    file_size = 0

    # Time penalty table based on the hour gap
    hour_penalty = [1, 0.9, 0.8, 0.6, 0.4, 0.2, 0, 0.1, 0.2, 0.3, 0.4, 0.5,
                    0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0, 0.2, 0.4, 0.6, 0.8, 0.9]

    # Open original and anonymized files
    with open(original_file, "r") as fd_nona_file, open(anonymized_file, "r") as fd_anon_file:
        nona_reader = csv.reader(fd_nona_file, delimiter=SEPARATOR)
        anon_reader = csv.reader(fd_anon_file, delimiter=SEPARATOR)

        for row_original, row_anonymized in zip(nona_reader, anon_reader):
            score = 1  # Start each row with full score
            file_size += 1

            if row_anonymized[0] == "DEL":
                continue  # Ignore deleted rows

            if len(row_anonymized[1]) > 13 and len(row_anonymized[0]) > 0:
                hour_anon = int(row_anonymized[1][11:13])  # Extract hour from anonymized timestamp
                hour_original = int(row_original[1][11:13])  # Extract hour from original timestamp

                if 0 <= hour_anon < 24 and 0 <= hour_original < 24:
                    time_diff = abs(hour_anon - hour_original)
                    if time_diff:  
                        score -= hour_penalty[time_diff]  # Deduct score based on time difference
                else:
                    return (-1, file_size)  # Error: Invalid time values
            else:
                return (-1, file_size)  # Error: Invalid timestamp format

            total_score += max(0, score)  # Ensure score does not go below 0

    return total_score / file_size if file_size > 0 else 0  # Return average utility score