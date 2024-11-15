import kewi
import requests
from dotabase import dotabase_session, Hero
from datetime import datetime

from kewi.context import TableAlign

ARG_player_id: int = kewi.globals.Dota.STEAM_ID
kewi.ctx.init()

url = f"https://api.opendota.com/api/players/{ARG_player_id}/matches?limit=20&significant=0"

# TODO: replace this with some custom http getter that posts status updates and shit to console
# - we should have this custom http getter like update a line in console with the status and the status code when it finishes
# - should have like a white background or something would be nice
# - can do some reaaaaally nice advanced pretty logging like this. can also use it for cache retrieval stuff
response = requests.get(url)


# TODO: handle errors here

# TODO: mebbe print player name before printing the table

session = dotabase_session()

def hero_lookup(hero_id):
	hero: Hero = session.query(Hero).filter_by(id=hero_id).first()
	if hero is None:
		return "UNRECOGNIZED_HERO"
	return hero.localized_name

data = response.json()

header = [
	"ID",
	"Hero",
	"",
	"KDA",
	"Start Time"
]

kewi.ctx.print("Matches:")

# TODO: have a like kewi.openscratch or soemthing that saves the json and opens it in a cache json file for viewing

table = []
for match in data:
	did_win = match["radiant_win"] == (match["player_slot"] < 127)
	kda = "-".join([
		str(match["kills"]),
		str(match["deaths"]),
		str(match["assists"])
	])
	
	date = datetime.fromtimestamp(match["start_time"])
	# TODO: add a library thing to do the below date formatting in a more reliable and good way (proper spacing, remove leading zeroes)

	table.append([
		match["match_id"],
		"Win" if did_win else "Loss",
		hero_lookup(match["hero_id"]),
		kda,
		date.strftime("%I:%M%p, %b %d %Y")
	])

kewi.ctx.print_table(table, align=TableAlign.LEFT)
