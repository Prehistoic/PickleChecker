import logging

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from picklechecker.core.results import AnalysisResult

class ConsoleResultsFormatter:

    logger = logging.getLogger(__name__)
    console = Console()