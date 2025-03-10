import random
import pandas as pd
import csv
from src.constants.core_msg import *
from src.common.utils import csv_length
from src.core.services.file_manager import FileManager
class Shuffle:
    """
    Handles shuffling of rows in a CSV file for anonymization purposes.
    """

    def __init__(self, input_file, origin_file, output_file):
        self.input_file = input_file
        self.origin_file = origin_file
        self.output_file = output_file
        self.chunksize = 10_000_000  # Number of rows processed at a time
        self.exception = None

    def process(self):
        """Main execution function for shuffling the dataset."""
        try:
            size = csv_length(self.origin_file)
            # Calculate total chunks
            chunks = (size // self.chunksize) + (1 if size % self.chunksize > 0 else 0)
            random_order = list(range(chunks))
            random.shuffle(random_order)

            for i in random_order:
                start_idx = self.chunksize * i
                rows_to_read = min(self.chunksize, size - start_idx)

                chunk = self.chunk_shuffler(self.input_file, start_idx, rows_to_read)
                chunk.to_csv(
                    self.output_file, mode="a", sep=SEPARATOR, index=False, header=False, lineterminator="\n"
                )
            return 0  # Success

        except Exception as e:
            self.exception = UNKNOWN_ERROR.format(str(e))
            return (self.exception, -1)


    def chunk_shuffler(self, file, start_idx, rows_to_read):
        """Reads a chunk from the CSV file, shuffles it, and returns as a DataFrame."""
        try:
            with open(file, "r") as f:
                reader = csv.reader(f, delimiter=SEPARATOR)
                chunk = [row for idx, row in enumerate(reader) if start_idx <= idx < start_idx + rows_to_read]
                random.shuffle(chunk)
                return pd.DataFrame(chunk)
        except Exception as e:
            self.exception = UNKNOWN_ERROR.format(str(e))
            return pd.DataFrame()