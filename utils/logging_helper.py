import logging
import sys

from config import PROJECT_NAME

def setup_logging(level=logging.INFO):
    """
    Sets up the global logging configuration.
    
    1. Silences all loggers outside of the 'MyProject' hierarchy (third-party libraries).
    2. Configures the handler and formatter for 'MyProject' loggers.
    
    Args:
        level: The minimum logging level to display for 'MyProject' loggers.
    """
    
    # --- Step 1: Silence External Libraries ---
    # Set the level of the root logger to CRITICAL. 
    # Loggers without an explicit level (most third-party libraries) inherit this, 
    # effectively silencing them.
    logging.getLogger().setLevel(logging.CRITICAL) 
    
    # --- Step 2: Configure Your Project Logger ---
    # Get the top-level logger for your project
    project_root_logger = logging.getLogger(PROJECT_NAME)
    project_root_logger.setLevel(level)

    # Use a StreamHandler to output logs to the console
    handler = logging.StreamHandler(sys.stdout)
    
    # Define a clean, informative format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Ensure no duplicate handlers if setup_logging is called multiple times
    if not project_root_logger.handlers:
        project_root_logger.addHandler(handler)

# Helper function for easy inclusion in classes
def get_logger(name):
    """
    Returns a child logger instance for a given module or class name.
    The logger name will be prefixed with the project name.
    """
    # E.g., if name is MyClass, the final logger name is MyProject.MyClass
    return logging.getLogger(f"{PROJECT_NAME}.{name}")

# IMPORTANT: Call this function once at the start of your main script
setup_logging(level=logging.INFO)