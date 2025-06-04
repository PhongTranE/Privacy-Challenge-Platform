import json
import importlib
from statistics import mean, median
from sqlalchemy import select
from src.constants.core_msg import *
from src.extensions import db
from src.modules.anonymisation.models import AnonymModel
from src.modules.anonymisation.models import MetricModel, AggregationModel

class Utility:
    """
    Evaluates the utility of an anonymized dataset by executing various 
    metric scripts and computing an aggregated score.
    """

    def __init__(self, input_file, origin_file):
        self.input_file = input_file
        self.origin_file = origin_file
        self.error_message = None
        self.scripts = []  # List of selected metric scripts
        self.scores = []  # Stores scores from executed scripts

    def process(self):
        """Fetches selected metric scripts from the database and executes them."""
        try:
            # Fetch selected metric scripts and parameters from the database
            stmt = select(MetricModel.name, MetricModel.parameters).where(MetricModel.is_selected == True)
            results = db.session.execute(stmt).fetchall()
            self.scripts = [(row[0], row[1]) for row in results]
            # Execute each script
            for script_name, parameters in self.scripts:
                try:

                    metric_module = importlib.import_module(f"src.core.metrics.{script_name}")
                    result = metric_module.main(self.origin_file, self.input_file, json.loads(parameters))
                    
                    if isinstance(result, tuple):  # Error in the submitted file
                        self.error_message = UTILITY_CALCULATION_ERROR.format(script_name, result[1])
                        return (self.error_message, -1)
                    else:
                        self.scores.append(result)  # Store valid results
                except Exception as e:
                    self.error_message = SCRIPT_ERROR.format(script_name, str(e))
                    return (self.error_message, -1)
            return self.result()  # Success

        except Exception as e:
            self.error_message = UNKNOWN_ERROR.format(str(e))
            return (self.error_message, -1)

    def result(self):
        """Returns the final utility score based on the selected aggregation method."""
        if self.error_message:
            return (self.error_message, -1)

        if not self.scores:
            return (NO_WORKING_UTILITY_SCRIPT, -1)

        # Fetch the aggregation method from the database
        stmt = select(AggregationModel.name).where(AggregationModel.is_selected == True)
        aggregation_method = db.session.execute(stmt).scalar()

        # Compute and return the final aggregated score
        aggregation_functions = {
            "mean": mean,
            "median": median,
            "max": max,
            "min": min
        }
        return aggregation_functions.get(aggregation_method, mean)(self.scores)  # Default to mean