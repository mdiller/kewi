from mutagen.mp4 import MP4, MP4FreeForm
import json
import os
import kewi

# give this a path to a steelseries moments video file
ARG_video_file: kewi.args.FilePath = kewi.globals.Moments.EXAMPLE_FILE
kewi.args.init()

kewi.out.print("Target File: " + ARG_video_file.fullpath)

json_filename = kewi.cache.new(ARG_video_file.fullpath, "json")

def unicode_key(n):
	return (n + 1).to_bytes(4, byteorder='big').decode('latin1')

def read_video_json(video_path, just_get_lavf = False):
	video = MP4(video_path)
	jsontext = ""

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
	return json.loads(jsontext)

data = read_video_json(ARG_video_file.fullpath)

before_text = json.dumps(data, indent="\t")
# write this json to a file
with open(json_filename, "w+") as f:
	f.write(before_text)

kewi.out.print("Wrote json to: " + json_filename)
os.startfile(json_filename)
kewi.out.print("Now edit this file, and then press enter in console to save the changes to the video file")

input("Press Enter:")

after_text = None
with open(json_filename, "r") as f:
	after_text = f.read()

if before_text == after_text:
	kewi.out.print("JSON unchanged. Exiting.")
	exit(0)

data = None
try:
	data = json.loads(after_text)
except:
	kewi.out.print("ERROR loading new json. Exiting.")
	exit(0)

def write_video_json(video_path, json_data):
	video = MP4(video_path)
	text = json.dumps(json_data)

	# Split text into chunks of max 255 characters
	chunk_size = 255
	chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

	lavf = read_video_json(video_path, True)
	chunks.append(lavf)

	for i, chunk in enumerate(chunks):
		# print(f"chunk{i}", chunk)
		custom_tag_name = unicode_key(i)
		custom_tag_value = chunk

		# Note: MP4FreeForm expects bytes, so we convert the string to bytes
		# video[custom_tag_name] = [MP4FreeForm(custom_tag_value.encode('utf-8'))]
		video[custom_tag_name] = custom_tag_value

	# Save the changes back to the file
	video.save()

write_video_json(ARG_video_file.fullpath, data)
kewi.out.print("Saved!")

