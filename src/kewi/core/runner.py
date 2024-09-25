import os
import typing

from ..utils import REPO_PATH

class ScriptInfo():
	"""
	Holds the information about the loaded script
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
	For the listing and running of scripts
	"""
	script_infos: typing.List[ScriptInfo]
	def __init__(self):
		self.script_dirs = [
			REPO_PATH("src/scripts"),
		]
		self.script_infos = []
		self.load_scripts()
	
	def load_scripts(self):
		"""Load the list of scripts"""
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
		for info in self.script_infos:
			if info.name.lower() == scriptname.lower():
				return info
		return None
	
	def list_scripts(self) -> typing.List[ScriptInfo]:
		"""List all available scripts."""
		return self.script_infos

	def run_script(self, script_info: ScriptInfo):
		"""Run a script by its name."""
		if script_info is None:
			return None
		
		with open(script_info.fullpath) as f:
			script_content = f.read()
		# print(f"Running script: {script_info.filename}") # GOOD PLACE FOR A LOG_INFO THING
		exec(script_content, globals())