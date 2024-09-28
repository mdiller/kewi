import os
import typing
import kewi.args  # Import kewi.args to handle argument initialization
from kewi.args import RunnerBase, set_current_runner
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


class Runner(RunnerBase):
	"""
	For the listing and running of scripts.
	"""
	script_infos: typing.List[ScriptInfo]
	cli_args: typing.List[str] = []  # Store CLI arguments passed to the script

	def __init__(self):
		self.script_dirs = [REPO_PATH("src/scripts")]
		self.script_infos = []
		self.cli_args = None
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
		for info in self.script_infos:
			if info.name.lower() == scriptname.lower():
				return info
		return None

	def list_scripts(self) -> typing.List[ScriptInfo]:
		"""List all available scripts."""
		return self.script_infos

	def run_script(self, script_info: ScriptInfo, cli_args: typing.List[str]):
		"""Run a script by its name."""
		if script_info is None:
			return None

		# Store the CLI arguments passed to this script
		self.cli_args = cli_args

		# Set this runner as the current global runner
		set_current_runner(self)

		globals_dict = {
			"__name__": "__main__",
			"__file__": script_info.fullpath,
		}

		with open(script_info.fullpath) as f:
			script_content = f.read()

		try:
			# Execute the script normally, and init will use the global runner
			exec(script_content, globals_dict)
		except kewi.args.KewiInputError as e:
			self.handle_input_error(e)

		self.cli_args = None

	def get_argument_values(self, kewi_args: typing.List[kewi.args.KewiArg]) -> typing.List[str]:
		"""
		Fetch argument values based on the kewi_args and CLI arguments passed.
		"""
		if self.cli_args is not None:
			# Use the provided CLI argument if available
			return self.cli_args

		return []

	def handle_input_error(self, error: kewi.args.KewiInputError):
		"""
		Handle an input error detected in the script.
		"""
		# You can customize this to log or report the error differently
		print(f"Runner handling input error: {error}")
