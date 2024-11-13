import os
import typing
import kewi.args  # Import kewi.args to handle argument initialization
from kewi.context import KewiContext, KewiContextConsole
from ..utils import REPO_PATH

class ScriptInfo():
	"""
	Holds the information about the loaded script.
	"""
	def __init__(self, fullpath: str, root: str):
		self.root = root
		self.fullpath = fullpath
		self.filename = os.path.basename(fullpath)
		self.relpath = os.path.relpath(fullpath, root)
		name, ext = os.path.splitext(self.relpath)
		name = name.replace("\\", ".")
		self.name = name


class Runner():
	"""
	For the listing and running of scripts.
	"""
	script_infos: typing.List[ScriptInfo]
	cli_args: typing.List[str] = []  # Store CLI arguments passed to the script

	def __init__(self):
		self.script_dirs = [REPO_PATH("src/scripts")]
		self.script_infos = []
		self.cli_args = None
		self.last_args_seen: typing.List[kewi.args.KewiArg] = None
		self.load_scripts()

	def load_scripts(self):
		"""Load the list of scripts."""
		result = []
		for dir in self.script_dirs:
			for root, dirs, files in os.walk(dir):
				for file in files:
					fullpath = os.path.abspath(os.path.join(root, file))
					name, extension = os.path.splitext(file)
					if os.path.isfile(fullpath) and extension == ".py":
						result.append(ScriptInfo(fullpath, dir))
		self.script_infos = result

	def get_script(self, scriptname: str) -> ScriptInfo:
		"""Get a ScriptInfo object by its name."""
		if scriptname is None:
			return None
		for info in self.script_infos:
			if info.name.lower() == scriptname.lower():
				return info
		return None

	def list_scripts(self) -> typing.List[ScriptInfo]:
		"""List all available scripts."""
		return self.script_infos

	def run_script(self, script_info: ScriptInfo, ctx: KewiContext, only_run_args = False):
		"""Run a script by its name."""
		if script_info is None:
			return None

		globals_dict = ctx.to_exec_globals()
		globals_dict["__name__"] = "__main__"
		globals_dict["__file__"] = script_info.fullpath

		with open(script_info.fullpath) as f:
			script_content = f.read()
		
		if only_run_args:
			lines = script_content.splitlines()
			newlines = []
			found = False
			for i, line in enumerate(lines):
				newlines.append(line)
				if "kewi.ctx.init()" in line:
					# Return lines up to and including the line with the keyword
					found = True
					break
			if not found:
				return None
			script_content = "\n".join(newlines)

		try:
			# Execute the script normally, and init will use the global runner
			exec(script_content, globals_dict)
		except kewi.args.KewiInputError as e:
			if not only_run_args:
				ctx.handle_input_error(e)
			else:
				raise
	
	def query_script_args(self, script_info: ScriptInfo) -> typing.List[kewi.args.KewiArg]:
		ctx = KewiContextConsole.new_from_console() # TODO: replace this with some other empty stub call
		self.run_script(script_info, ctx, only_run_args=True)
		return ctx.kewi_args

