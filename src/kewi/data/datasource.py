
from ..args import TimeSpan
from abc import ABC, abstractmethod
from ..args import TimeSpan
from ..utils import SimpleTimer
import typing

class DataItem(ABC):
	# Inherited properties
	uri: str
	timestamp: TimeSpan

	# Abstract properties
	title: typing.Optional[str] = None
	description: typing.Optional[str] = None
	link: typing.Optional[str] = None
	info: typing.Optional[dict] = None
	color: typing.Optional[str] = None

	def __init__(self, uri: str, timestamp: TimeSpan):
		self.uri = uri
		self.timestamp = timestamp
	
	def __repr__(self):
		result = f"] {self.uri}"
		if self.title is not None:
			result += f"\n- title: {self.title}"
		if self.link is not None:
			result += f"\n- link: {self.link}"
		if self.description is not None:
			result += f"\n- description: {self.description}"
		result += "\n" + str(self.timestamp)
		return result


class DataSource(ABC):
	@abstractmethod
	def initialize(self):
		"""Initialize the data source."""
		pass

	@abstractmethod
	def get_data(self, time: TimeSpan) -> typing.List[DataItem]:
		"""Fetch data based on the provided TimeSpan."""
		pass

	def log(self, message: str):
		print(f"[DataSource Log] {message}")
	
	def log_timer(self, message: str):
		return SimpleTimer(message) # TODO: make this timer call self.log on exit instead in future