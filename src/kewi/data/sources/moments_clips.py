# video_clips_data_source.py
import os
import kewi
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
import typing
from mutagen.mp4 import MP4, MP4FreeForm
import json
import os
from ...args import TimeSpan
from ..fileinfocache import FileInfoCache
from ..datasource import DataSource, DataItem
import pytz

def unicode_key(n):
	return (n + 1).to_bytes(4, byteorder='big').decode('latin1')

def read_video_json(video_path, just_get_lavf = False):
	print(f"LOADING: {video_path}")
	video = MP4(video_path)
	jsontext = ""
	for key in video.tags:
		value = video.tags[key]
		value_shortened = str(value)
		if len(value_shortened) > 50:
			value_shortened = value_shortened[:50 - 3] + "..."
	i = 0
	while True:
		key = unicode_key(i)
		if key not in video.tags:
			break
		value = video.tags[key]
		if isinstance(value, list):
			value = value[0]
		if value.startswith("Lavf"):
			if just_get_lavf:
				return value
			break
		
		jsontext += value
		i += 1
	
	if jsontext == "":
		return None # EMPTYYYYYY

	jsontext = jsontext.replace("\r", "")
	return json.loads(jsontext)

# Derived from DataItem
class VideoClip(DataItem):
	def __init__(self, file_path: str, info: dict):
		self.info = info
		date = dateutil_parser.parse(self.info["recording_timestamp"])
		start_date = date + timedelta(seconds=self.info["clip_start_point"])
		end_date = date + timedelta(seconds=self.info["clip_end_point"])
		date_ms = int(date.timestamp() * 1000)
		uri = f"data.clips.{date_ms}"
		super().__init__(uri, TimeSpan(start_date, end_date))
		self.link = file_path
		self.title = self.info["name"]
		seconds_length = self.info["clip_end_point"] - self.info["clip_start_point"]
		game_id = self.info["library_game_unique_id"]
		self.description = f"{int(seconds_length)} sec clip. Game ID: {game_id}"

	@classmethod
	def load(cls, file_path: str):
		info = read_video_json(file_path)
		if info is None:
			return None
		clip = VideoClip(file_path, info)
		return clip

# Derived from DataSource
class ClipsDataSource(DataSource):
	def __init__(self):
		self.clips: typing.List[VideoClip] = []
		self.root_dir = kewi.globals.Moments.ROOT_DIR
		self.initialize()

	def initialize(self):
		self.log("Initializing VideoClipsDataSource.")
		self.clips  = []
		
		infocache = FileInfoCache("filecache.clips_infos")

		with self.log_timer("Getting file list"):
			for filename in os.listdir(self.root_dir):
				file_path = os.path.join(self.root_dir, filename)

				if os.path.isfile(file_path) and file_path.endswith(".mp4"):
					infocache.add_file(file_path)
		
		with self.log_timer("Loading Clip Infos"):
			infocache.refresh(read_video_json)
		
		with self.log_timer("Loading as VideoClips"):
			for file_path, info in infocache.iterate():
				if info is not None:
					self.clips.append(VideoClip(file_path, info))

		self.log(f"Found {len(self.clips)} video clips.")
		return self.clips

	def get_data(self, time: TimeSpan) -> typing.List[VideoClip]:
		with self.log_timer("Searching VideoClips"):
			clips = list(filter(lambda c: time.intersects(c.timestamp), self.clips))
		return clips
