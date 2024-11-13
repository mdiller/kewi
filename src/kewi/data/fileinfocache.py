import kewi
import orjson
import typing
import os

# a way to cache information about a set of files, and be able to tell when files have changed

class FileInfoCache:
	def __init__(self, uri: str):
		self.cache_uri = uri
		self.cache_file = kewi.cache.get_filename(self.cache_uri)
		print(f"CACHED: {self.cache_file}")
		if self.cache_file is None:
			self.cache_file = kewi.cache.new(self.cache_uri, "json")
			self.data = {
				"files": {}
			}
			self.save()
		else:
			self.load()
		
	def load(self):
		with open(self.cache_file, "rb") as f:
			self.data = orjson.loads(f.read())
	
	def save(self):
		text = orjson.dumps(self.data)
		with open(self.cache_file, "wb+") as f:
			f.write(text)
	
	@property
	def files(self):
		return self.data["files"]

	# gets the info from the cache
	def get(self, filename) -> typing.Dict:
		return self.files.get(filename).get("info")

	# adds the file to the cache
	def add_file(self, file: str):
		if not file in self.files:
			self.files[file] = {
				"info": None,
				"mtime": None
			}

 	# adds files to the ones we pay attention to. existing ones are ignored
	def add_files(self, files: typing.List[str]):
		for file in files:
			self.add_file(file)

	# returns an iterator to iterate through each key, info pair.
	def iterate(self) -> typing.Iterator[typing.Tuple[str, typing.Dict]]:
		for key, value in self.files.items():
			info = value.get("info")
			yield key, info 

	# reloads the info for each thing in the cache, using info_func to get the info for it, then saves the cache
	def refresh(self, info_func: typing.Callable[[str], typing.Dict]):
		for key in self.files:
			if os.path.isfile(key):
				last_mtime = self.files[key].get("mtime")
				mtime = os.path.getmtime(key)
				if last_mtime is None or last_mtime != mtime:
					# TODO: WRAP THIS IN A TRY/CATCH, AND SAVE THE CACHEFILE BEFORE RETHROWING
					info = info_func(key)
					self.files[key]["info"] = info
					self.files[key]["mtime"] = mtime
		self.save()

