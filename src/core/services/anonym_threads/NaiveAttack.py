import json
import csv
from collections import defaultdict
from datetime import date
from src.extensions import db
from src.constants.core_msg import *

class NaiveAttack:
    """
    Executes a naive attack to re-identify individuals based on GPS data in anonymized datasets.
    """
    
    def __init__(self, original_file, anonym_file, answer_json):
        self.original_file = original_file
        self.anonym_file = anonym_file
        self.answer_json = answer_json
        self.score = -1
        self.original_dict = None
        self.anonym_dict = None
    
    def generate_sum_gps(self, file):
        """Generates a dictionary mapping each month to the sum of GPS coordinates."""
        dict_sum_gps = defaultdict(lambda: [0.0, 0.0])
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=SEPARATOR)
            for row in reader:
                if row[0] != "DEL":
                    y, m, d = row[1][:10].split("-")
                    calendar = date(int(y), int(m), int(d)).isocalendar()
                    id_date = f"{row[0]}.{calendar[0]}-{calendar[1]}"
                    dict_sum_gps[id_date][0] += float(row[-2])
                    dict_sum_gps[id_date][1] += float(row[-1])
        return dict_sum_gps
    
    def match_gps_data(self):
        """Matches anonymized GPS data with original data to re-identify records."""
        self.original_dict = self.generate_sum_gps(self.original_file)
        self.anonym_dict = self.generate_sum_gps(self.anonym_file)

        sol = defaultdict(dict)
        for key in self.original_dict:
            original_gps = self.original_dict[key]
            min_distance = float('inf')
            best_match = ""
            
            for key2 in self.anonym_dict:
                difference = abs(original_gps[0] - self.anonym_dict[key2][0]) + \
                             abs(original_gps[1] - self.anonym_dict[key2][1])
                if difference < min_distance:
                    min_distance = difference
                    best_match = key2
            
            sol[key.split(".")[0]][key.split(".")[1]] = [best_match.split(".")[0]]
        
        return sol
    
    def calculate_score(self, sol):
        """Calculates the attack success score by comparing with ground truth data."""
        with open(self.answer_json) as json_file:
            data = json.load(json_file)
            total_entries = sum(len(data[tab]) for tab in data)
            correct_matches = sum(
                1 for tab in data for month in data[tab] if data[tab][month][0] == sol[tab][month][0]
            )
            self.score = correct_matches / total_entries if total_entries > 0 else 0

    
    def process(self):
        """Executes the naive attack and updates the database."""
        solution = self.match_gps_data()
        self.calculate_score(solution)
        return self.result()
    
    def result(self):
        """Returns the final attack score."""
        return self.score 
