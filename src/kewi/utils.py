import os
import datetime

def REPO_PATH(sub_path):
	# Get the directory where this script (and your library) is located
	base_dir = os.path.dirname(os.path.abspath(__file__))

	# Construct the full path to 'resources/private/cache' by navigating up and down the directory structure
	resource_dir = os.path.join(base_dir, '..', '..', sub_path)
	return os.path.abspath(resource_dir)  # Return the absolute path


def RESOURCE_PATH(sub_path):
	return REPO_PATH(os.path.join("resources", sub_path))



class SimpleTimer():
	def __init__(self, message=None):
		self.message = message
		self.start = datetime.datetime.now()
		self.end = None
	
	def __enter__(self):
		self.start = datetime.datetime.now()
		return self

	def __exit__(self, type, value, traceback):
		self.stop()
		if self.message:
			print(self.message + f": {self.miliseconds} ms")

	def stop(self):
		self.end = datetime.datetime.now()

	@property
	def seconds(self):
		if self.end is None:
			self.stop()
		return int((self.end - self.start).total_seconds())
	
	@property
	def miliseconds(self):
		if self.end is None:
			self.stop()
		return int((self.end - self.start).total_seconds() * 1000.0)

	def __str__(self):
		s = self.seconds % 60
		m = self.seconds // 60
		text = f"{s} second{'s' if s != 1 else ''}"
		if m > 0:
			text = f"{m} minute{'s' if m != 1 else ''} and " + text
		return text

	def __repr__(self):
		return self.__str__()


