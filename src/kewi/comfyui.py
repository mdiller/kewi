import typing
from PIL import Image

import json
import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import os
from PIL import Image
import io
import kewi
from kewi.args import KewiArg
from mutagen.mp4 import MP4, MP4FreeForm

# MAYBE JUST GETS THE PROMPT? NMOT SURE
def read_file_metadata(filename):
	data = ""
	if filename.endswith("mp4"):
		video = MP4(filename)
		for value in video.tags.values():
			for item in value:
				if item.startswith('{"prompt"'):
					data = item
	else:
		img = Image.open(filename)
		data = img.info["prompt"]

	if data is None:
		raise Exception("Invalid input file, no prompt metadata")
	data = json.loads(data)
	return data


# TODO: do linking of inputs/outputs for this at some point
class ComfyUiNode:
	def __init__(self, json: dict):
		self.json = json
		self.id: int = self.json["id"]
		self.type: str = self.json["type"]
		self.order: int = self.json["order"]
		self.widgets_values: typing.List[str] = self.json.get("widgets_values", [])
		self.title: str = self.json.get("title", None)

class ComfyUiMetadata:
	def __init__(self, json: dict):
		self._json = json
		self.nodes: typing.List[ComfyUiNode] = []
		for node_json in self._json["nodes"]:
			self.nodes.append(ComfyUiNode(node_json))
		
	def find_nodes(self, type: str = None) -> typing.List[ComfyUiNode]:
		nodes = self.nodes
		if type:
			nodes = list(filter(lambda n: n.type == type, nodes))
		return nodes
	
	def save_json_file(self, fullpath):
		text = json.dumps(self._json)
		with open(fullpath, "w+", encoding="utf-8") as f:
			f.write(text)

	@classmethod
	def from_json_file(cls, fullpath):
		with open(fullpath, "r", encoding="utf-8") as f:
			data = json.loads(f.read())
		return ComfyUiMetadata(data)
	
	@classmethod
	def from_image_file(cls, fullpath):
		# try:
		img = Image.open(fullpath)
		if "workflow" in img.info:
			return ComfyUiMetadata(json.loads(img.info["workflow"]))
		return None
		# except Exception as e:
		# 	return None


INPUT_NAME = "INPUT"
OUTPUT_PREVIEW_NAME = "OUTPUT"

# TODO: MEBBE MAKE ENUM OUT OF THIS LATER
NODE_TYPE_PREVIEWIMG = "PreviewImage"
NODE_TYPE_IMAGELOAD = "Image Load"

class BadWorkflow(Exception):
	def __init__(self, message):
		message = f"INVALID WORKFLOW: {message}"
		super().__init__(message)
		self.message = message

class ComfyUiWorkflowNode:
	def __init__(self, workflow: 'ComfyUiWorkflow', id: str, data: dict):
		self.workflow = workflow
		self.id = id
		self.data = data
	
	@property
	def node_type(self):
		return self.data["class_type"]

	@property
	def title(self):
		return self.data.get("_meta", {}).get("title", None)
	
	@title.setter
	def title(self, value: str):
		if self.data.get("_meta", None) is None:
			self.data["_meta"] = {}
		self.data["_meta"]["title"] = value
	
	@property
	def input_ids(self):
		input_nodes = []
		for value in self.data.get("inputs", {}).values():
			if isinstance(value, list):
				if len(value) > 0 and isinstance(value[0], str):
					input_nodes.append(value[0])
		return input_nodes
	
	def get_output_nodes(self) -> typing.List['ComfyUiWorkflowNode']:
		nodes = []
		for node in self.workflow.nodes:
			if self.id in node.input_ids:
				nodes.append(node)
		return nodes
	
	def get_depth(self, ignored_node_ids: typing.List[str] = None) -> int:
		if ignored_node_ids is None:
			ignored_node_ids = []
		
		depth = 1
		for node_id in self.input_ids:
			if node_id in ignored_node_ids:
				continue
			ignored_node_ids.append(node_id)
			node = self.workflow.get_node(node_id)
			depth += node.get_depth(ignored_node_ids)
		
		return depth


class ComfyUiWorkflow:
	def __init__(self, data: dict, cleanup = True):
		self.nodes: typing.List[ComfyUiWorkflowNode] = []
		for node_id in data:
			node = ComfyUiWorkflowNode(self, node_id, data[node_id])
			self.nodes.append(node)
		if cleanup:
			self.cleanup()
	
	def get_node(self, node_id: str):
		for node in self.nodes:
			if node.id == node_id:
				return node
		return None

	# removes extra preview nodes and makes sure theres atleast one output, and correctly fixes input
	def cleanup(self, expect_input=True):
		preview_nodes = self.filter_nodes(type=NODE_TYPE_PREVIEWIMG)
		if len(preview_nodes) == 0:
			raise BadWorkflow("Must have at least 1 output node")
		output_nodes = self.filter_nodes(type=NODE_TYPE_PREVIEWIMG, title=OUTPUT_PREVIEW_NAME)
		if len(output_nodes) == 0:
			if len(preview_nodes) == 1:
				preview_nodes[0].title = OUTPUT_PREVIEW_NAME
			else:
				message = "Too many preview nodes, none labeled output. Preview Nodes:"
				for node in preview_nodes:
					message += f"\n- [{node.id}] depth: {node.get_depth()}"
				raise BadWorkflow(message)
		
		# REMOVE EXTRA PREVIEW NODES
		to_remove = []
		for node in self.filter_nodes(type=NODE_TYPE_PREVIEWIMG):
			if node.title != OUTPUT_PREVIEW_NAME:
				to_remove.append(node)
		for node in to_remove:
			self.nodes.remove(node)
		
		# CHECK INPUT NODES
		input_nodes = self.filter_nodes(title=INPUT_NAME)
		if expect_input and len(input_nodes) == 0:
			file_nodes = self.filter_nodes(type=NODE_TYPE_IMAGELOAD)
			if len(file_nodes) == 0:
				raise BadWorkflow("Missing INPUT node, and no file inputs present")
			elif len(file_nodes) == 1:
				file_nodes[0].title = INPUT_NAME
			else:
				message = "Too many file inputs to choose an INPUT. File Inputs:"
				for node in file_nodes:
					output_types = ", ".join(list(map(lambda n: n.class_type, node.get_output_nodes())))
					message += f"\n- [{node.id}] inputs to: ({output_types})"
				raise BadWorkflow(message)

	def to_json(self):
		data = {}
		for node in self.nodes:
			data[node.id] = node.data
		return data
	
	def get_input_params(self) -> typing.List[KewiArg]:
		# gets the input parameters needed for this from the stuff
		# can use this to make a thing out of any workflow, just based on the input arguments
		# TODO: IMPLEMENT THIS
		pass
	
	def set_input_path(self, input_image_path):
		input_nodes = self.filter_nodes(title=INPUT_NAME)
		if len(input_nodes) != 1:
			if len(input_nodes) == 0:
				raise BadWorkflow("no input nodes set!")
			raise BadWorkflow("not sure which input to set!")
		if "\\" in input_image_path and not "\\\\" in input_image_path:
			input_image_path = input_image_path.replace("\\", "\\\\")
		input_nodes[0].data["inputs"]["image_path"] = input_image_path

	def filter_nodes(self, title: str = None, type: str = None) -> typing.List[ComfyUiWorkflowNode]:
		nodes = []
		for node in self.nodes:
			if title is not None and node.title != title:
				continue
			if type is not None and node.node_type != type:
				continue
			nodes.append(node)
		return nodes
	
	def get_output_node_ids(self):
		return list(map(lambda n: n.id, self.filter_nodes(title=OUTPUT_PREVIEW_NAME)))

	@classmethod
	def from_file_metadata(cls, filename, cleanup = True):
		data = read_file_metadata(filename)
		return ComfyUiWorkflow(data["prompt"], cleanup)


SERVER_ADDRESS = kewi.globals.ComfyUI.SERVER_URL

class ComfyUiApi:
	def __init__(self):
		self.client_id = client_id = str(uuid.uuid4())
		self.ws = websocket.WebSocket()
		self.ws.connect("ws://{}/ws?clientId={}".format(SERVER_ADDRESS, client_id))

	def queue_prompt(self, workflow: ComfyUiWorkflow):
		print("> queue_prompt()")
		p = {"prompt": workflow.to_json(), "client_id": self.client_id}
		data = json.dumps(p).encode('utf-8')
		req =  urllib.request.Request("http://{}/prompt".format(SERVER_ADDRESS), data=data)
		return json.loads(urllib.request.urlopen(req).read())

	def get_image(self, filename, subfolder, folder_type):
		print("> get_image()")
		data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
		url_values = urllib.parse.urlencode(data)
		with urllib.request.urlopen("http://{}/view?{}".format(SERVER_ADDRESS, url_values)) as response:
			return response.read()

	def get_history(self, prompt_id):
		print("> get_history()")
		with urllib.request.urlopen("http://{}/history/{}".format(SERVER_ADDRESS, prompt_id)) as response:
			return json.loads(response.read())

	# returns a ComfyUIPromptResult
	def run_workflow(self, workflow: ComfyUiWorkflow) -> 'ComfyUIPromptResult':
		prompt_id = self.queue_prompt(workflow)['prompt_id']

		prompt_result = ComfyUIPromptResult(prompt_id, workflow)
		while True:
			out = self.ws.recv()
			if isinstance(out, str):
				message = json.loads(out)
				prompt_result.ws_message(message)

				# print(f"WS TYPE: {message['type']}")
				# print(str(message))

				if prompt_result.is_done:
					break
			else:
				continue # previews? are binary data

		return prompt_result


class ComfyUIPromptResult:
	def __init__(self, prompt_id: str, workflow: ComfyUiWorkflow):
		self.prompt_id = prompt_id
		self.workflow = workflow
		self.output_ids = workflow.get_output_node_ids()
		self.output_images = {}
		self.ws_messages = []
		self.was_cached = False
		self.error = None

	@property
	def is_done(self):
		if self.error is not None:
			return True
		for node_id in self.output_ids:
			if node_id not in self.output_images:
				return False
		return True

	@property
	def output_image(self):
		images = list(self.output_images.values())
		if len(images) > 0:
			return images[0]
		return None

	def ws_message(self, message: dict):
		try:
			self.ws_messages.append(message)
			msg_type = message["type"]
			if msg_type == "execution_cached":
				for id in message["data"]["nodes"]:
					if id in self.output_ids and id not in self.output_images:
						self.was_cached = True
						self.output_images[id] = None
			if msg_type == "executed":
				node_id = message["data"].get("node", None)
				if node_id in self.output_ids:
					fileinfo = message["data"]["output"]["images"][0]
					filename = f"{fileinfo['type']}/{fileinfo['filename']}"
					filename = os.path.join(kewi.globals.ComfyUI.ROOT_DIR, "ComfyUI", filename)
					self.output_images[node_id] = filename
			if msg_type == "progress":
				data = message["data"]
				if data["prompt_id"] == self.prompt_id:
					progress_str = f"- progress: {data['value']} / {data['max']} [{data['node']}]"
					kewi.ctx.print(progress_str)
			if msg_type == "execution_error":
				err_data = message["data"]
				error_text = "COMFYUI: Execution Error:"
				error_text += f"\n- node_id: {err_data['node_id']}"
				error_text += f"\n- node_type: {err_data['node_type']}"
				error_text += f"\n- exception_type: {err_data['exception_type']}"
				error_text += f"\n- exception_message: {err_data['exception_message']}"
				self.error = error_text
				# error_text += f"\n- traceback: {err_data['traceback']}"
		except Exception as e:
			print("ComfyUIPromptResult.ws_message ERRORED ON THIS WS MESSAGE:")
			print(json.dumps(message))
			print("\n")
			raise
