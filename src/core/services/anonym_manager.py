from concurrent.futures import ThreadPoolExecutor, as_completed
from src.core.services.anonym_threads import Footprint, Utility, Shuffle, NaiveAttack
from src.constants.core_msg import *
from src.core.utils import *

class AnonymManager:
    """Handles anonymization processing, including footprint generation and utility calculation."""
    
    def __init__(self, app, input_file, origin_file, shuffled_file, footprint_file):
        self.input_file = input_file
        self.origin_file = origin_file
        self.shuffled_file = shuffled_file
        self.footprint_file = footprint_file
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.app = app
        
    def _run_footprint(self):
        """Runs Footprint calculation in a separate thread."""
        with self.app.app_context():
            footprint = Footprint(self.input_file, self.origin_file, self.footprint_file)
            return footprint.process()

    def _run_utility(self):
        """Runs Utility calculation in a separate thread."""
        with self.app.app_context():
            utility = Utility(self.input_file, self.origin_file)
            return utility.process() 
        
    def _run_shuffle(self):
        """Runs Shuffle in a separate thread."""
        with self.app.app_context():
            shuffle = Shuffle(self.input_file, self.origin_file, self.shuffled_file)
            return shuffle.process() 

    def _run_naive_attack(self):
        """Runs Naive Attack in a separate thread after shuffle is completed."""
        with self.app.app_context():
            naive_attack = NaiveAttack(self.origin_file, self.input_file, self.footprint_file)
            return naive_attack.process()
        
    def process(self):
        """Executes the anonymization process with concurrency."""
        check = checking_shape(self.input_file, self.origin_file)
        if isinstance(check, tuple):
            raise ValueError(f"Invalid file shape: {check[0]}")

        results = {}

        try:
            with self.executor as executor:  
                # Run both functions asynchronously
                future_footprint = executor.submit(self._run_footprint)
                future_utility = executor.submit(self._run_utility)
                future_shuffle = executor.submit(self._run_shuffle)
                
                # Wait for completion and store results
                for future in as_completed([future_footprint, future_utility, future_shuffle]):
                    try:

                        result = future.result()
                        if future == future_footprint:
                            results["footprint"] = result
                        elif future == future_utility:
                            results["utility"] = result
                        elif future == future_shuffle:
                            results["shuffle"] = result
                            # Start naive attack after shuffle is done
                            future_naive_attack = executor.submit(self._run_naive_attack)
                            results["naive_attack"] = future_naive_attack.result()
                    except Exception as e:
                        print(f"Error in task execution: {str(e)}")
                        raise RuntimeError(UNKNOWN_ERROR.format(str(e)))
                
                for key, value in results.items():
                    if isinstance(value, tuple):
                        raise Exception(value[0])

                return (results.get("utility", 0), results.get("naive_attack", -1))
        
        except Exception as e:
            raise RuntimeError(UNKNOWN_ERROR.format(str(e)))