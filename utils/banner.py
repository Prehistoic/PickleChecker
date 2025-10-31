import pyfiglet

from config import PROJECT_NAME

def display_banner():
    """
    Display a beautiful banner !
    """
    banner = pyfiglet.figlet_format(PROJECT_NAME, font="slant")
    print(banner)