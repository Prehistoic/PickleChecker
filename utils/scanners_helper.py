import importlib
import inspect
from typing import List, Tuple
from pathlib import Path

from utils.logging_helper import get_logger
from utils.pickle_helper import PickleAnalyzer, PickleAnalysis
from scanners import Scanner, ScanResult

class ScannersHelper:

    logger = get_logger(__name__)

    @classmethod
    def run_directory_scan_all_scanners(self, dirpath: str) -> Tuple[List[ScanResult], List[PickleAnalysis]]:
        """
        Dynamically loads all modules in the 'scanners' directory and executes 
        the run_directory_scan method on any class inheriting from Scanner.
        """
        target_path = Path(dirpath)

        if not target_path.is_dir():
            self.logger.error(f"Directory not found at {dirpath}")
            return

        # First we analyze all pickle files in directory
        pickle_analyses = PickleAnalyzer.analyze_directory(dirpath)

        # Then we run all scanners
        scanner_results = []
        
        # 1. Get all scanner module files (e.g., 'fickling.py', 'picklescan.py')
        # Filter for files that don't start with '_' (like __init__.py) and end with '.py'
        scanner_files = Path("scanners").glob("[!_]*.py") 

        for module_file in scanner_files:
            module_name = f"scanners.{module_file.stem}" # e.g., 'scanners.fickling'
            
            try:
                # 2. Dynamically import the module
                module = importlib.import_module(module_name)
                
                # 3. Inspect the module for classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    
                    # 4. Check if the class inherits from Scanner (but isn't Scanner itself)
                    if issubclass(obj, Scanner) and obj is not Scanner:
                        
                        # 5. Instantiate the scanner and run the method
                        scanner_instance = obj(name=module_file.stem)
                        scanner_results.extend(scanner_instance.run_directory_scan(target_path))
                        
            except ImportError as e:
                self.logger.warning(f"Could not import {module_name}: {e}")
            except Exception as e:
                self.logger.error(f"Error while running {module_name}: {e}")

        return scanner_results, pickle_analyses

    @classmethod
    def run_file_scan_all_scanners(self, filepath: str) -> Tuple[List[ScanResult], List[PickleAnalysis]]:
        """
        Dynamically loads all modules in the 'scanners' directory and executes 
        the run_file_scan method on any class inheriting from Scanner.
        """
        target_path = Path(filepath)

        if not target_path.exists():
            self.logger.error(f"File not found at {filepath}")
            return
        
        # First we analyze the provided pickle file
        pickle_analysis = PickleAnalyzer.analyze_pickle(filepath)

        # Then we run all scanners
        scanner_results = []

        # 1. Get all scanner module files (e.g., 'fickling.py', 'picklescan.py')
        # Filter for files that don't start with '_' (like __init__.py) and end with '.py'
        scanner_files = Path("scanners").glob("[!_]*.py") 

        for module_file in scanner_files:
            module_name = f"scanners.{module_file.stem}" # e.g., 'scanners.fickling'
            
            try:
                # 2. Dynamically import the module
                module = importlib.import_module(module_name)
                
                # 3. Inspect the module for classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    
                    # 4. Check if the class inherits from Scanner (but isn't Scanner itself)
                    if issubclass(obj, Scanner) and obj is not Scanner:
                        
                        # 5. Instantiate the scanner and run the method
                        scanner_instance = obj()
                        scanner_results.append(scanner_instance.run_file_scan(target_path))
                        
            except ImportError as e:
                self.logger.warning(f"Could not import {module_name}: {e}")
            except Exception as e:
                self.logger.error(f"Error while running {module_name} scanner: {e}")

        return scanner_results, [pickle_analysis]