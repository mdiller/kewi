from .cache import Cache
from .out import OutputBase, ConsoleOutput

# Create a global instance of the Cache class
cache = Cache()
out = ConsoleOutput()


def SET_INTERFACE(outputter: OutputBase):
	global out
	out = outputter

