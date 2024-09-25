import json
import kewi

filename = kewi.cache.new("example:somedata:thing", "json")

data = {
	"soup": "blue",
	"bananas": [
		True,
		False
	]
}

with open(filename, "w+") as f:
	f.write(json.dumps(data))

