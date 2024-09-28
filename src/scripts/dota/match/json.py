import kewi
import requests
import json
import os

ARG_match_id: int = kewi.globals.Dota.EXAMPLE_MATCH_ID
kewi.args.init()

url = f"https://api.opendota.com/api/matches/{ARG_match_id}"

uri = f"dota.matches.match_{ARG_match_id}"

filename = kewi.cache.get_filename(uri)

if filename is None:
	kewi.out.print("querying...")
	filename = kewi.cache.new(uri, "json")
	response = requests.get(url)
	data = response.json()
	with open(filename, "w+") as f:
		f.write(json.dumps(data, indent="\t"))


kewi.out.print(filename)
os.startfile(filename)

