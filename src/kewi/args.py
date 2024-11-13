import sys
import inspect
from enum import Enum
from types import FrameType
from typing import Any, Callable, List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import os
from .globals._generated_globals import Globals
import pytz
import re

globals = Globals()

# Global variable to hold the current runner instance
_current_runner = None

class KewiInputError(Exception):
	"""Custom exception to handle input validation errors."""
	
	def __init__(self, arg_name: str, expected_type: Any, value: str, error_message: str = None):
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
	
	def to_json(self):
		return {
			"name": str(self.name),
			"full_name": str(self.full_name),
			"type": str(self.type.__name__),
			"position": str(self.position),
			"default": str(self.default)
		}
	
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

# gets the args in the given frame for the script
def args_from_frame(frame: FrameType) -> List[KewiArg]:	
	# TODO: fix this so i dont have to necessarily assign a type to my variable
	# Retrieve all annotated variables (ARG_*) from the global namespace
	arg_annotations = {k: v for k, v in frame.f_globals.get('__annotations__', {}).items() if k.startswith("ARG_")}
	
	# Create a list of KewiArg objects for each argument
	kewi_args = []
	for position, (arg_name, arg_type) in enumerate(arg_annotations.items()):
		full_name = arg_name
		name = arg_name[4:]  # Remove the "ARG_" prefix
		default = frame.f_globals.get(arg_name, None)

		if default is not None and not isinstance(default, arg_type) and hasattr(arg_type, "parse"):
			default = arg_type.parse(name + "(DEFAULT_VALUE)", arg_type, default)
			frame.f_globals[full_name] = default

		kewi_arg = KewiArg(name, full_name, arg_type, position, default)
		kewi_args.append(kewi_arg)
	return kewi_args

# sets the args in the given frame for the script
def args_set_frame(inputs: List[Any], kewi_args: List[KewiArg], frame: FrameType, request_input: Callable):
	# Assign values to globals or prompt for input
	for kewi_arg, input_value in zip(kewi_args, inputs):
		frame.f_globals[kewi_arg.full_name] = parse_input_value(kewi_arg.name, kewi_arg.type, input_value)

	# For any arguments not provided, prompt for input if necessary
	for kewi_arg in kewi_args[len(inputs):]:
		if kewi_arg.full_name not in frame.f_globals:
			frame.f_globals[kewi_arg.full_name] = request_input(kewi_arg)
	

def parse_command_line_args(kewi_args: List[KewiArg]):
	"""Parse positional arguments from the command line."""
	args = sys.argv[1:]  # Skip the script name
	if len(args) > len(kewi_args):
		raise KewiInputError("Too many arguments", args, list)
	return args


def request_input_console(arg_name: str, arg_type: Any) -> Any:
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
		raise KewiInputError(arg_name, arg_type, user_input) from ve


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
			raise KewiInputError(arg_name, arg_type, value)
	except ValueError as ve:
		raise KewiInputError(arg_name, arg_type, value) from ve


def parse_enum_input(arg_name: str, enum_type: Enum, value: str) -> Enum:
	"""Handle enum input, case-insensitive and supports numbered options."""
	try:
		if value.isdigit():
			value = int(value)
			return list(enum_type)[value - 1]
		return enum_type[value.upper()]
	except (IndexError, KeyError):
		raise KewiInputError(arg_name, enum_type, value)


def parse_bool_input(arg_name: str, value: str) -> bool:
	"""Handle boolean input."""
	true_values = ["yes", "y", "true", "enable", "1"]
	false_values = ["no", "n", "false", "disable", "0"]
	if value.lower() in true_values:
		return True
	elif value.lower() in false_values:
		return False
	else:
		raise KewiInputError(arg_name, bool, value)

# TODO: maybe add a separate version of this that doesnt verify that the file exists when parsing??
class FilePath():
	def __init__(self, fullpath: str):
		self.fullpath = fullpath
	
	@classmethod
	def parse(cls, arg_name: str, arg_type: Any, value: str):
		# TODO: add support for aliases here to get stuff like "the last cache file saved" etc.
		if not os.path.exists(value):
			value = os.path.join(globals.Obsidian.VAULT_ROOT, value)
		if not os.path.exists(value):
			raise KewiInputError(arg_name, arg_type, value, f"'{value}' is not an existing file")
		return FilePath(value)
	
	def __str__(self):
		return self.fullpath

	def exists(self):
		return os.path.exists(self.fullpath)

	def ext(self):
		return os.path.splitext(self.fullpath)[1]


PAST_MIDNIGHT_HOURS = 5 # how many hours past midnight is still considered the same day
LOCAL_TZ = pytz.timezone(globals.TIMEZONE)
class TimeSpan:
	def __init__(self, start: datetime, end: datetime):
		self.start = start.astimezone(LOCAL_TZ)
		self.end = end.astimezone(LOCAL_TZ)

	def __str__(self):
		result = "start: " + self.start.strftime("%I:%M %p - %d-%b-%Y")
		result += "\n  end: " + self.end.strftime("%I:%M %p - %d-%b-%Y")
		return result

	def contains(self, date: datetime):
		return self.start < date and self.end > date
	
	def intersects(self, span: 'TimeSpan'):
		return (
			span.start < self.start and span.end > self.end
			or self.start < span.start and self.end > span.start
			or self.start < span.end and self.end > span.end
	  )

	@classmethod
	def from_day(cls, text: str):
		day: datetime
		pattern1 = r" ?(?:—|â€”|\u2014)? ?([0-9]{2}/[0-9]{2}/[0-9]{4})"

		if isinstance(text, datetime):
			if text.tzinfo is not None and text.tzinfo.utcoffset(text) is not None:
				day = text.astimezone(LOCAL_TZ)
			else:
				day = LOCAL_TZ.localize(text)
			day -= timedelta(hours=PAST_MIDNIGHT_HOURS)
			day = day.replace(hour=0, minute=0, second=0)
		elif re.match(pattern1, text):
			match = re.match(pattern1, text)
			text = match.group(1)
			day = datetime.strptime(text, "%m/%d/%Y")
			day = LOCAL_TZ.localize(day)
		else:
			day = datetime.strptime(text, "%Y-%m-%d")
			day = LOCAL_TZ.localize(day)
		day = day.replace(hour=PAST_MIDNIGHT_HOURS, minute=0, second=0)
		end = day + timedelta(hours=24)
		return TimeSpan(day, end)

	@classmethod
	def last_x_hours(cls, hours: int):
		now = datetime.now(LOCAL_TZ)
		then = now - timedelta(hours=hours)
		return TimeSpan(then, now)
		
	@classmethod
	def parse(cls, arg_name: str, arg_type: Any, value: str):
		time_kinds = {
			"minute": 1,
			"hour": 60,
			"day": 60 * 24,
			"week": 60 * 24 * 7
		}
		time_kinds_pattern =  "|".join(map(lambda k: k + "s?", time_kinds.keys()))
		pattern = f"last (\d+) ({time_kinds_pattern})"
		match = re.match(pattern, value)
		if match:
			number = int(match.group(1))
			time_kind = match.group(2)
			time_kind = time_kind.replace("s", "")

			now = datetime.now(LOCAL_TZ)
			kind_modifier = time_kinds[time_kind]
			then = now - timedelta(minutes=(number * kind_modifier))
			return TimeSpan(then, now)

		if value == "today":
			return TimeSpan.from_day(datetime.now(LOCAL_TZ))
		if value == "yesterday":
			day = datetime.now(LOCAL_TZ)
			day -= timedelta(days=1)
			return TimeSpan.from_day(day)

		pattern = f"(\d+) days? ago"
		match = re.match(pattern, value)
		if match:
			number = int(match.group(1))
			day = datetime.now(LOCAL_TZ)
			day -= timedelta(days=number)
			return TimeSpan.from_day(day)

		weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
		if value in map(lambda d: "last " + d, weekdays):
			value = value.replace("last ", "")
		if value in weekdays:
			day = datetime.now(LOCAL_TZ)
			current_weekday = day.weekday()
			target_weekday = weekdays.index(value)
			days_ago = (current_weekday - target_weekday) % 7 or 7
			day -= timedelta(days=days_ago)
			return TimeSpan.from_day(day)

		try:
			return TimeSpan.from_day(value)
		except ValueError as e:
			raise KewiInputError(arg_name, arg_type, value)

