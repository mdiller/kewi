from mutagen.mp4 import MP4, MP4FreeForm
import json
import os
import kewi

# give this a path to a steelseries moments video file
ARG_video_file: kewi.args.FilePath = kewi.globals.Moments.EXAMPLE_FILE
kewi.args.init()

kewi.out.print("Target File: " + ARG_video_file.fullpath)

json_filename = kewi.cache.new(ARG_video_file.fullpath, "json")
# os.startfile(json_filename)

def unicode_key(n):
	return (n + 1).to_bytes(4, byteorder='big').decode('latin1')

def read_video_json(video_path, just_get_lavf = False):
	video = MP4(video_path)
	jsontext = ""

	print("METADATA:")
	for key in video.tags:
		value = video.tags[key]
		escaped_key = ''.join(f'\\x{ord(c):02x}' for c in key)
		value_shortened = str(value)
		if len(value_shortened) > 50:
			value_shortened = value_shortened[:50 - 3] + "..."
		print(escaped_key, type(value), value_shortened)

	print("")
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

# write this json to a file
with open(json_filename, "w+") as f:
	f.write(json.dumps(data, indent="\t"))


kewi.out.print("Wrote json to: " + json_filename)
os.startfile(json_filename)
