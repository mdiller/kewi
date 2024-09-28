from .cache import Cache
from .out import OutputBase, ConsoleOutput
from . import args

from .globals.globals import generate_globals
generate_globals()
from .globals._generated_globals import Globals


# Create a global instance of the Cache class
cache = Cache()
out = ConsoleOutput()
args = args
globals = Globals

def SET_INTERFACE(outputter: OutputBase):
	global out
	out = outputter

