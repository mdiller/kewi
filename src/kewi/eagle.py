
# 

# look thru the "widgets_values" of nodes

# ok lets just like DO it like lets make a class to handle eagle/comfyui stuff
import typing
from PIL import Image

import json
import requests
import os
import kewi
from .comfyui import ComfyUiMetadata, ComfyUiNode


class EagleImage:
	def __init__(self, eagle_id, filename, library_dir, json):
		self.filename = filename
		self.eagle_id = eagle_id
		self.library_dir = library_dir
		self.json = json
		self._comfyui_metadata = -1 # none has other meaning, so -1 will mean hasnt been loaded
	
	@property
	def fullpath(self):
		path_parts = [
			self.library_dir,
			"images",
			f"{self.eagle_id}.info",
			self.filename
		]
		return os.path.join(*path_parts)

	@property
	def comfy_metadata(self) -> ComfyUiMetadata:
		if self._comfyui_metadata == -1:
			cache_file = kewi.cache.new(f"eagle.images.metadata.{self.eagle_id}_metadata", "json")
			if os.path.exists(cache_file):
				self._comfyui_metadata = ComfyUiMetadata.from_json_file(cache_file)
			else:
				self._comfyui_metadata = ComfyUiMetadata.from_image_file(self.fullpath)
			if self._comfyui_metadata is not None:
				self._comfyui_metadata.save_json_file(cache_file)
		return self._comfyui_metadata

	@classmethod
	def from_json(cls, item_data: dict, library_dir: str):
		return EagleImage(
			item_data["id"],
			item_data["name"] + "." + item_data["ext"],
			library_dir,
			item_data
		)

	@classmethod
	def from_path(cls, fullpath):
		pass # parse this correctly from a path like C:\dev\projects\eagle\Example123.library\images\LXV0WY3ZYSOJG.info\view 1024×1024.png


class EagleApi:
	def __init__(self):
		pass

	def get_library_dir(self):
		url = f"{kewi.globals.Eagle.API_URL_BASE}/api/library/info"
		response = requests.get(url)
		data = response.json()
		return data["data"]["library"]["path"]

	def get_items(self, folders=[]) -> typing.List[EagleImage]:
		library_dir = self.get_library_dir()
		items_list = []
		offset = 0
		limit_per_page = 200
		print("querying...")
		while True:
			print(f"page {offset}")
			url = f"{kewi.globals.Eagle.API_URL_BASE}/api/item/list?offset={offset}&limit={limit_per_page}"
			if folders:
				url += f'&folders={",".join(folders)}'
			response = requests.get(url)
			data = response.json()
			items_list.extend(data["data"])
			if len(data["data"]) < limit_per_page:
				break
			offset += 1

		images = []
		for item_data in items_list:
			if item_data["ext"] in ["png", "jpg", "jpeg", "gif"]:
				image = EagleImage.from_json(item_data, library_dir)
				images.append(image)
		return images

	def add_file(self, file_path, description = None, link = None):
		url = f"{kewi.globals.Eagle.API_URL_BASE}/api/item/addFromPath"
		data = {
			"path": file_path,
			"name": os.path.basename(file_path),
			"tags": ["FROM_SCRIPT"]
		} # https://api.eagle.cool/item/add-from-path (could do a "website" tag too for future)
		if description:
			data["annotation"] = description
		if link:
			data["website"] = link
		response = requests.post(url, json=data)
		if response.status_code == 200:
			data = response.json()
			return data["data"]
		else:
			raise Exception(f"Error Uploading: {response.status_code}")