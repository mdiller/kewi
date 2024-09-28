import sys
import inspect
from enum import Enum
from typing import Any, List
from abc import ABC, abstractmethod
import os

# Global variable to hold the current runner instance
_current_runner = None

class KewiInputError(Exception):
	"""Custom exception to handle input validation errors."""
	
	def __init__(self, arg_name: str, value: str, expected_type: Any, error_message: str = None):
		self.arg_name = arg_name
		self.value = value
		self.expected_type = expected_type
		self.error_message = error_message
		
	def __str__(self):
		if self.error_message:
			return f"INPUT ERROR: {self.error_message}"
		return f"INPUT ERROR: Argument '{self.arg_name}' is of type '{self.expected_type.__name__}', and '{self.value}' is not a valid value."

class KewiArg:
	"""Class to represent a single argument."""
	
	def __init__(self, name, full_name, arg_type, position, default=None):
		self.name = name  # The name of the argument (e.g., "thing")
		self.full_name = full_name  # The full name of the argument (e.g., "ARG_thing")
		self.type = arg_type  # The type of the argument (e.g., int)
		self.position = position  # The zero-based position of the argument in the list
		self.default = default  # The default value, if specified
	
	@property
	def is_optional(self):
		"""Return True if the argument has a default value (is optional)."""
		return self.default is not inspect.Parameter.empty

class RunnerBase(ABC):
	"""Abstract base class for handling script arguments and errors."""
	
	@abstractmethod
	def get_argument_values(self, kewi_args: List[KewiArg]) -> List[Any]:
		"""
		Return argument values for the provided KewiArgs.
		"""
		pass

	@abstractmethod
	def handle_input_error(self, error: KewiInputError):
		"""
		Handle an input error detected in the script.
		"""
		pass


def set_current_runner(runner: RunnerBase):
	"""Set the current global runner."""
	global _current_runner
	_current_runner = runner


def get_current_runner() -> RunnerBase:
	"""Get the current global runner."""
	global _current_runner
	return _current_runner


def init(runner: RunnerBase = None):
	"""Initialize the arguments by parsing from command line or user input."""
	try:
		frame = inspect.currentframe().f_back
		
		# Retrieve the current runner if none is passed
		if runner is None:
			runner = get_current_runner()
		
		# Retrieve all annotated variables (ARG_*) from the global namespace
		arg_annotations = {k: v for k, v in frame.f_globals.get('__annotations__', {}).items() if k.startswith("ARG_")}
		
		# Create a list of KewiArg objects for each argument
		kewi_args = []
		for position, (arg_name, arg_type) in enumerate(arg_annotations.items()):
			full_name = arg_name
			name = arg_name[4:]  # Remove the "ARG_" prefix
			default = frame.f_globals.get(arg_name, inspect.Parameter.empty)
			kewi_arg = KewiArg(name, full_name, arg_type, position, default)
			kewi_args.append(kewi_arg)
		
		# If a runner is provided, delegate argument fetching to the runner
		if runner:
			inputs = runner.get_argument_values(kewi_args)
		else:
			# Map command-line arguments (positional) to the KewiArg variables
			inputs = parse_command_line_args(kewi_args)
		
		# Assign values to globals or prompt for input
		for kewi_arg, input_value in zip(kewi_args, inputs):
			frame.f_globals[kewi_arg.full_name] = parse_input_value(kewi_arg.name, kewi_arg.type, input_value)
		
		# For any arguments not provided, prompt for input if necessary
		for kewi_arg in kewi_args[len(inputs):]:
			if kewi_arg.full_name not in frame.f_globals:
				frame.f_globals[kewi_arg.full_name] = request_input(kewi_arg.name, kewi_arg.type)
	except KewiInputError as e:
		if runner:
			# Delegate error handling to the runner
			runner.handle_input_error(e)
		else:
			print(e)
		sys.exit(1)


def parse_command_line_args(kewi_args: List[KewiArg]):
	"""Parse positional arguments from the command line."""
	args = sys.argv[1:]  # Skip the script name
	if len(args) > len(kewi_args):
		raise KewiInputError("Too many arguments", args, list)
	return args


def request_input(arg_name: str, arg_type: Any) -> Any:
	"""Request input for missing arguments."""
	try:
		if inspect.isclass(arg_type) and issubclass(arg_type, Enum):
			# Handle enums
			options = [f"{i+1}. {e.name}" for i, e in enumerate(arg_type)]
			print(f"Please select a value for {arg_name}:")
			for option in options:
				print(option)
			user_input = input("> ")
			return parse_enum_input(arg_name, arg_type, user_input)
		elif arg_type == bool:
			# Handle booleans
			user_input = input(f"Please enter True/False for {arg_name}: ")
			return parse_bool_input(arg_name, user_input)
		elif hasattr(arg_type, "request_input"):
			# Handle custom classes
			return arg_type.request_input()
		else:
			# For all other types (int, str, etc.)
			user_input = input(f"Please enter a value for {arg_name} (type {arg_type.__name__}): ")
			return parse_input_value(arg_name, arg_type, user_input)
	except ValueError as ve:
		raise KewiInputError(arg_name, user_input, arg_type) from ve


def parse_input_value(arg_name: str, arg_type: Any, value: str) -> Any:
	"""Parse and validate input based on the argument type."""
	try:
		if arg_type == int:
			return int(value)
		elif arg_type == str:
			return value
		elif arg_type == bool:
			return parse_bool_input(arg_name, value)
		elif inspect.isclass(arg_type) and issubclass(arg_type, Enum):
			return parse_enum_input(arg_name, arg_type, value)
		elif hasattr(arg_type, "parse"):
			return arg_type.parse(arg_name, arg_type, value)
		else:
			raise KewiInputError(arg_name, value, arg_type)
	except ValueError as ve:
		raise KewiInputError(arg_name, value, arg_type) from ve


def parse_enum_input(arg_name: str, enum_type: Enum, value: str) -> Enum:
	"""Handle enum input, case-insensitive and supports numbered options."""
	try:
		if value.isdigit():
			value = int(value)
			return list(enum_type)[value - 1]
		return enum_type[value.upper()]
	except (IndexError, KeyError):
		raise KewiInputError(arg_name, value, enum_type)


def parse_bool_input(arg_name: str, value: str) -> bool:
	"""Handle boolean input."""
	true_values = ["yes", "y", "true", "enable", "1"]
	false_values = ["no", "n", "false", "disable", "0"]
	if value.lower() in true_values:
		return True
	elif value.lower() in false_values:
		return False
	else:
		raise KewiInputError(arg_name, value, bool)

# TODO: maybe add a separate version of this that doesnt verify that the file exists when parsing??
class FilePath():
	def __init__(self, fullpath: str):
		self.fullpath = fullpath
	
	@classmethod
	def parse(cls, arg_name: str, arg_type: Any, value: str):
		# TODO: add support for aliases here to get stuff like "the last cache file saved" etc.
		result = FilePath(value)
		if not result.exists():
			raise KewiInputError(arg_name, arg_type, value, f"'{value}' is not an existing file")
		return result
	
	def __str__(self):
		return self.fullpath

	def exists(self):
		return os.path.exists(self.fullpath)

	def ext(self):
		return os.path.splitext(self.fullpath)[1]

