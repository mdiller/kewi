import kewi
import requests
import json
import os

# THIS IS HOW WE'RE GONNA MAKE THE match_id THING BELOW BE AN INPUT FROM THE USER
# OK SO WE DEFINETLY WANNA IMPLEMNET IT LIKE THIS, BUT WE ARENT SURE ON THE NAMING
# this will inherit from a class in kewi
class KewiScript():
	match_id: int
# scriptstuff = KewiScript.load()


# TODO: make this an input argument
match_id = 7957318100

url = f"https://api.opendota.com/api/matches/{match_id}"

uri = f"dota:matches:match_{match_id}"

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

