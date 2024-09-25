from abc import ABC, abstractmethod
import asyncio
import websockets
from enum import Enum


class TableAlign(Enum):
	LEFT = "left"
	RIGHT = "right"
	CENTER = "center"

class OutputBase(ABC):
	"""
	Abstract base class for Outputs. Defines the interface for sending output.
	"""
	
	@abstractmethod
	def print(self, message: str) -> None:
		"""Print a message"""
		pass

	# TODO: add a print-list that prints a list of values. also i should have default implementations of these?

	@abstractmethod
	def print_table(self, rows: list[list[str]], headers: list[str] = None,  align: TableAlign | list[TableAlign] = TableAlign.LEFT) -> None:
		"""Print a formatted table"""
		pass

# TODO: maybe use a linter to make sure we always have all the abstract methods implemented. could add a method for opening a file for example

class ConsoleOutput(OutputBase):
	"""
	Output that prints output to the console.
	"""
	
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


# class WebSocketOutput(OutputBase):
# 	"""
# 	Output that sends output through a WebSocket connection.
# 	"""
# 	def __init__(self, uri: str):
# 		self.uri = uri

# 	async def _send_message(self, message: str) -> None:
# 		"""Send a message over a WebSocket connection"""
# 		async with websockets.connect(self.uri) as websocket:
# 			await websocket.send(message)

# 	def print(self, message: str) -> None:
# 		"""Send a message through the WebSocket"""
# 		asyncio.run(self._send_message(message))

# 	def print_table(self, headers: list[str], rows: list[list[str]]) -> None:
# 		"""Send a table through the WebSocket"""
# 		# Format the table as a string to send over the WebSocket
# 		table_str = "\t".join(headers) + "\n"
# 		for row in rows:
# 			table_str += "\t".join(row) + "\n"
# 		asyncio.run(self._send_message(table_str))
