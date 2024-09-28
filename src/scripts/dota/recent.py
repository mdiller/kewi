import kewi
import requests
from dotabase import dotabase_session, Hero

from kewi.out import TableAlign

ARG_player_id = kewi.globals.Dota.STEAM_ID
kewi.args.init()

url = f"https://api.opendota.com/api/players/{ARG_player_id}/matches?limit=20"

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
	"KDA"
]

kewi.out.print("Matches:")

table = []
for match in data:
	did_win = match["radiant_win"] == (match["player_slot"] < 127)
	kda = "-".join([
		str(match["kills"]),
		str(match["deaths"]),
		str(match["assists"])
	])
	table.append([
		match["match_id"],
		"Win" if did_win else "Loss",
		hero_lookup(match["hero_id"]),
		kda
	])

kewi.out.print_table(table, align=TableAlign.LEFT)
