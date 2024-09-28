import os
import kewi
import datetime
import kewi.obsidian
import difflib
from colorama import Fore, Style
import colorama

# TODO: integrate colorama into kewi in general, and have a global setting for turning it on/off
colorama.init()

ARG_target_dir = "C:\\home\\Notes\\general\\high\\notes"
kewi.args.init()

# TODO: maybe make a more generic / copiable version of this script so i can do these batch-updates more easily

# List all files in the target directory with full paths
for filename in os.listdir(ARG_target_dir):
	full_path = os.path.join(ARG_target_dir, filename)
	file = kewi.obsidian.file(full_path)
	# print(full_path)
	date_obj = file.metadata["date"]
	DAILY_PATH = date_obj.strftime("%b-%Y/%d-%b %A")

	newline = f"[[daily_notes/{DAILY_PATH}|Daily Note]]"
	print(newline)

	file.content = newline + "\n" + file.content

	with open(full_path, "r", encoding="utf-8") as f:
		text1 = f.read()
	
	text2 = file._get_full_content()

	# TODO: integrate this diff thing into obsidian.py so we can check to see what the differences are before we write them
	diff = difflib.unified_diff(
		text1.splitlines(),
		text2.splitlines(), 
		fromfile='file_a', tofile='file_b', 
		lineterm=''
	)

	# print("\n".join(diff))

	for line in diff:
		if line.startswith('+') and not line.startswith('+++'):
			# Added lines in green
			print(Fore.GREEN + line + Style.RESET_ALL)
		elif line.startswith('-') and not line.startswith('---'):
			# Removed lines in red
			print(Fore.RED + line + Style.RESET_ALL)
		else:
			# Unchanged or file markers
			print(line)
	
	file.write()

