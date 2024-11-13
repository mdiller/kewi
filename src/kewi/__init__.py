import inspect
from .cache import Cache
from .context import KewiContext

from .globals.globals import generate_globals
generate_globals()
from .globals._generated_globals import Globals

# for special dynamic handling of getting a kewi context
def __getattr__(name) -> KewiContext:
	if name == "ctx":
		frame = inspect.currentframe().f_back
		try:
			return KewiContext.get_current(frame)
		finally:
			del frame
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

cache = Cache()
globals = Globals
ctx: KewiContext

