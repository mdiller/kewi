import datetime
import uuid
from io import BytesIO
import orjson
import os
import typing
import re

from .utils import RESOURCE_PATH

# currently set to 1 week timeout for cache files
CACHE_FILE_TIMEOUT_MS = 1000 * 60 * 60 * 24 * 7

def get_timestamp(date=None):
	if date is None:
		date = datetime.datetime.now()
	return int(datetime.datetime.timestamp(date) * 1000)

class CacheItem(dict):
	filename: str
	timestamp: int
	permanent: bool
	def __init__(self, json_data={}): # only to be used internally
		for key in json_data:
			self[key] = json_data[key]
		
	@classmethod
	def create(cls, filename, permanent=False):
		item = CacheItem()
		item["permanent"] = permanent
		item["filename"] = filename
		item.update_timestamp()
		return item
	
	@property
	def permanent(self):
		return self.get("permanent")
		
	@property
	def filename(self):
		return self["filename"]

	@property
	def timestamp(self):
		return self["timestamp"]

	def update_timestamp(self):
		self["timestamp"] = get_timestamp()
	
	def is_expired(self, timestamp_threshold):
		return (not self.permanent) and (self.timestamp < timestamp_threshold)


class Cache:
	cache_data: typing.Dict[str, CacheItem]
	def __init__(self):
		self.cache_dir = RESOURCE_PATH("private/cache/")
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir)
		self.cache_data = {}
		self.cache_index_filename = os.path.join(self.cache_dir, "_cache_index.json")
		if os.path.exists(self.cache_index_filename):
			with open(self.cache_index_filename, "rb") as f:
				json_dict = orjson.loads(f.read())
				for uri, item in json_dict.items():
					self.cache_data[uri] = CacheItem(item)
	
	def _save_to_disk(self):
		with open(self.cache_index_filename, "wb+") as f:
			f.write(orjson.dumps(self.cache_data))
	
	@property
	def size(self):
		return len(self.cache_data)
	
	# Cleans up any old files and flushes the cache to disk
	def cleanup_and_flush(self):
		threshold = get_timestamp() - CACHE_FILE_TIMEOUT_MS
		removed_count = 0
		for uri, item in list(self.cache_data.items()):
			if item.is_expired(threshold):
				filename = os.path.join(self.cache_dir, item.filename)
				if os.path.isfile(filename):
					os.remove(filename)
				removed_count += 1
				del self.cache_data[uri]
		self._save_to_disk()

	# Returns the filename of the cached url if it exists, otherwise None
	def get_filename(self, uri):
		item = self.cache_data.get(uri)
		if item is None:
			return None
		item.update_timestamp()
		filename = os.path.join(self.cache_dir, item.filename)
		if not os.path.isfile(filename):
			return None
		return filename

	# Returns the file if it exists, otherwise None
	def get(self, uri, return_type):
		filename = self.get_filename(uri)
		if not filename:
			return None
		if return_type == "json":
			with open(filename, "r") as f:
				return orjson.loads(filename)
		elif return_type == "text":
			with open(filename, "r") as f:
				return f.read()
		elif return_type == "bytes":
			with open(filename, "rb") as f:
				return BytesIO(f.read())
		elif return_type == "filename":
			return filename
		else:
			raise ValueError(f"Invalid return type '{return_type}'")

	#creates a new entry in the cache and returns the filename of the new entry
	def new(self, uri, extension=None, permanent=False):
		item = self.cache_data.get(uri)
		if item is not None:
			filename = os.path.join(self.cache_dir, item.filename)
			if os.path.isfile(filename):
				return filename
		
		dirchars_pattern = "^[:a-zA-Z0-9_-]+$"
		if re.match(dirchars_pattern, uri):
			parts = uri.split(":")
			parts = [item for item in parts if item != ".."]
			filename = "/".join(parts)
		else:
			filename = str(uuid.uuid4())
		if extension:
			filename = f"{filename}.{extension}"
		
		# make sure the dir exists
		full_path = os.path.join(self.cache_dir, filename)
		thedir = os.path.dirname(full_path)
		if not os.path.exists(thedir):
			os.makedirs(thedir)

		self.cache_data[uri] = CacheItem.create(filename, permanent=permanent)
		self._save_to_disk()
		return full_path


	def remove(self, uri):
		item = self.cache_data.get(uri)
		if item is not None:
			filename = os.path.join(self.cache_dir, item.filename)
			if os.path.isfile(filename):
				os.remove(filename)
			del self.cache_data[uri]