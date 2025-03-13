import json
import csv
from datetime import date
from src.constants.core_msg import *
from src.extensions import db
from src.modules.anonymisation.models import AnonymModel 
from sqlalchemy import select

class Footprint:
    """
    Generates a footprint for anonymized data and updates the database.
    """

    def __init__(self, input_file, origin_file, footprint_file):
        self.input_file = input_file
        self.origin_file = origin_file
        self.footprint_file = footprint_file
        self.exception = None

    def process(self):
        """Main execution function for footprint generation."""
        try:
            # Open original and anonymized files
            with open(self.origin_file, "r") as fd_nona_file, open(self.input_file, "r") as fd_anon_file:
                nona_reader = csv.reader(fd_nona_file, delimiter=SEPARATOR)
                anon_reader = csv.reader(fd_anon_file, delimiter=SEPARATOR)

                found_ids_weeks = {}  # {user_id: [list of weeks]}
                linktable = {}  # {user_id: {week_number: [list of anonymized IDs]}}

                for index, (row1, row2) in enumerate(zip(nona_reader, anon_reader), start=1):
                    if not row2[0]:  # Missing anonymized user ID
                        self.exception = MISSING_USER_ID.format(index)
                        return (self.exception, -1)

                    if row2[0] != "DEL":
                        try:
                            y2, m2, d2 = row2[1][0:10].split("-")
                            weeknum2 = date(int(y2), int(m2), int(d2)).isocalendar()[0:2]
                            weeknum2 = f"{weeknum2[0]}-{weeknum2[1]}"
                        except:
                            self.exception = INVALID_DATE_FORMAT.format(index)
                            return (self.exception, -1)

                        y1, m1, d1 = row1[1][0:10].split("-")
                        weeknum1 = date(int(y1), int(m1), int(d1)).isocalendar()[0:2]
                        weeknum1 = f"{weeknum1[0]}-{weeknum1[1]}"

                        if weeknum1 != weeknum2:
                            self.exception = DUPLICATE_USER_ID_WEEK.format(index)
                            return (self.exception, -1)

                        if row1[0] not in found_ids_weeks:
                            found_ids_weeks[row1[0]] = [weeknum1]
                            linktable[row1[0]] = {weeknum1: [row2[0]]}
                        elif weeknum1 not in found_ids_weeks[row1[0]]:
                            found_ids_weeks[row1[0]].append(weeknum1)
                            linktable[row1[0]][weeknum1] = [row2[0]]
                        elif linktable[row1[0]][weeknum1][0] != row2[0]:
                            self.exception = DUPLICATE_USER_ID_WEEK.format(index)
                            return (self.exception, -1)

            with open(self.footprint_file, 'w') as result:
                json.dump(linktable, result)
            return 0 # Success 
        
        except Exception as e:
            self.exception = UNKNOWN_ERROR.format(str(e))
            return (self.exception, -1)
    