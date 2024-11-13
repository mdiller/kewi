from abc import ABC, abstractmethod
import asyncio
import inspect
import os
import sys
import traceback
from types import FrameType
import websockets
from typing import List, Any
from enum import Enum
from aiohttp.web_request import Request
from aiohttp import web

from kewi.args import KewiArg
from .args import KewiArg, KewiInputError, RunnerBase, args_from_frame, args_set_frame, request_input_console


class TableAlign(Enum):
	LEFT = "left"
	RIGHT = "right"
	CENTER = "center"

KEWI_CONTEXT_GLOBALNAME = "__kewi_current_ctx__"

# # represents the context a given kewi script is called from. this is used to determine things like how we route output from a script 
class KewiContext(ABC):
	def __init__(self, arg_inputs: List[Any]):
		self.arg_inputs = arg_inputs
		self.kewi_args = None
		self.SKIP_SETTING_ARGS = False
	
	def to_exec_globals(self):
		globals_dict = {}
		globals_dict[KEWI_CONTEXT_GLOBALNAME] = self
		return globals_dict

	@classmethod
	def get_current(cls, frame: FrameType) -> 'KewiContext':
		globals_dict = frame.f_globals
		if KEWI_CONTEXT_GLOBALNAME in globals_dict:
			return globals_dict[KEWI_CONTEXT_GLOBALNAME]
		else:
			ctx = KewiContextConsole.new_from_console()
			globals_dict[KEWI_CONTEXT_GLOBALNAME] = ctx
			return ctx

	# inits args at the top of a script
	def init(self):
		frame = inspect.currentframe().f_back
		try:
			self.kewi_args = args_from_frame(frame)
			if self.SKIP_SETTING_ARGS:
				return True
			args_set_frame(self.arg_inputs, self.kewi_args, frame, self.request_arg_input)
		except KewiInputError as e:
			self.handle_input_error(e)
			# TODO: figure out a way to stop script execution if we get this error. ill just raise for now
			raise
		finally:
			del frame

	def request_arg_input(self, arg: KewiArg):
		raise KewiInputError(arg.name, arg.type, "<empty>", "Required argument not provided")

	# ABSTRACT METHODS

	# TODO: handle differently for web?
	def handle_input_error(self, error: KewiInputError):
		self.print(str(error)) # TODO: make this print in red for console
		
	def show_text_file(self, file_path: str) -> None:
		os.startfile(file_path)

	@abstractmethod
	def print(self, message: str) -> None:
		"""Print a message"""
		pass

	@abstractmethod
	def print_table(self, rows: list[list[str]], headers: list[str] = None,  align: TableAlign | list[TableAlign] = TableAlign.LEFT) -> None:
		"""Print a formatted table"""
		pass

# CONSOLE STUFF


class KewiContextConsole(KewiContext):
	"""
	Output that prints output to the console.
	"""
	
	@classmethod
	def new_from_console(cls) -> 'KewiContextConsole':
		args = sys.argv[1:]  # Skip the script name
		# if len(args) > len(kewi_args):
		# 	raise KewiInputError("Too many arguments", args, list)
		return KewiContextConsole(args)

	def print(self, message: str) -> None:
		"""Print a message to the console"""
		print(message)

	def print_table(self, rows: list[list[str]], headers: list[str] = None, align: TableAlign | list[TableAlign] = TableAlign.LEFT) -> None:
		"""Print a table to the console"""
		if headers is None:
			column_count = len(rows[0])
			headers = ["" for _ in range(column_count)]  # Empty headers
		else:
			column_count = len(headers)

		# Calculate the maximum width for each column
		col_widths = [max(len(str(headers[i])), max(len(str(row[i])) for row in rows)) for i in range(column_count)]

		# Helper function to format a cell based on align
		def format_cell(content: str, width: int, align: TableAlign) -> str:
			if align == TableAlign.LEFT:
				return content.ljust(width)
			elif align == TableAlign.RIGHT:
				return content.rjust(width)
			elif align == TableAlign.CENTER:
				return content.center(width)
			else:
				return content.ljust(width)  # Default to left if something goes wrong
		

		# If align is not a list, use the same align for all columns
		if isinstance(align, TableAlign):
			align = [align] * column_count

		if headers != [""] * column_count:
			# Print the headers
			header_row = " | ".join(format_cell(header, col_widths[i], align[i]) for i, header in enumerate(headers))
			print(header_row)
			print("-" * len(header_row))

		# Print each row
		for row in rows:
			row_str = " | ".join(format_cell(str(row[i]), col_widths[i], align[i]) for i in range(column_count))
			print(row_str)
	
	def request_arg_input(self, arg: KewiArg):
		request_input_console(arg.name, arg.type)

# Web stuff

class KewiContextWebJson(KewiContext):
	"""
	A web request called this and the response should be in a json format
	"""
	def __init__(self, request: Request):
		i = 0
		arg_inputs = []
		query_params = request.rel_url.query
		while True:
			arg_value = query_params.get(f"ARG_{i}")
			if arg_value is not None:
				arg_inputs.append(arg_value)
			else:
				break
		self.log_lines = []
		self.errors = []
		self.html_items = []
		super().__init__(arg_inputs)
	
	def to_web_response(self):
		json = {
			"text": self.log_lines,
			"errors": self.errors,
			"html": self.html_items
		}
		return web.json_response(json)
	
	def handle_error(self, error: Exception):
		self.print("EXCEPTION: " + str(error))
		self.errors.append({
			"messages": str(error),
			"stacktrace": traceback.format_exc()
		})
	
	def print(self, message: str) -> None:
		self.log_lines.append(message)

	# TODO: rework this to be an html/json table
	def print_table(self, rows: list[list[str]], headers: list[str] = None, align: TableAlign | list[TableAlign] = TableAlign.LEFT) -> None:
		"""Print a table to the console"""
		if headers is None:
			column_count = len(rows[0])
			headers = ["" for _ in range(column_count)]  # Empty headers
		else:
			column_count = len(headers)

		# Calculate the maximum width for each column
		col_widths = [max(len(str(headers[i])), max(len(str(row[i])) for row in rows)) for i in range(column_count)]

		# Helper function to format a cell based on align
		def format_cell(content: str, width: int, align: TableAlign) -> str:
			if align == TableAlign.LEFT:
				return content.ljust(width)
			elif align == TableAlign.RIGHT:
				return content.rjust(width)
			elif align == TableAlign.CENTER:
				return content.center(width)
			else:
				return content.ljust(width)  # Default to left if something goes wrong
		

		# If align is not a list, use the same align for all columns
		if isinstance(align, TableAlign):
			align = [align] * column_count

		if headers != [""] * column_count:
			# Print the headers
			header_row = " | ".join(format_cell(header, col_widths[i], align[i]) for i, header in enumerate(headers))
			self.print(header_row)
			self.print("-" * len(header_row))

		# Print each row
		for row in rows:
			row_str = " | ".join(format_cell(str(row[i]), col_widths[i], align[i]) for i in range(column_count))
			self.print(row_str)

	def show_text_file(self, file_path: str) -> None:
		with open(file_path, "r") as f:
			text = f.read()
		code_html = f"<code>{text}</code>"
		self.html_items.append(code_html)
