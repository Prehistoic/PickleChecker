from enum import Enum

class SafetyLevel(Enum):
    UNKNOWN = -1
    INNOCUOUS = 0
    SUSPICIOUS = 1
    DANGEROUS = 2