import argparse
import argcomplete

import os
if "_ARGCOMPLETE" in os.environ:
    print("Argcomplete triggered")
else:
	print("not")

def simple_completer(prefix, parsed_args, **kwargs):
	print("potato")
	"""Simple completer function returning hardcoded options."""
	return ["test_script1.py", "test_script2.py", "example_script.py"]

def main():
	# Create a basic parser
	parser = argparse.ArgumentParser(description="Test CLI for argcomplete")
	
	# Add 'run' command with autocompletion
	subparsers = parser.add_subparsers(dest="command")
	run_parser = subparsers.add_parser("run", help="Run a script by name")
	
	# Add scriptname argument with completer
	run_parser.add_argument("scriptname", help="Script to run").completer = simple_completer
	
	# Enable autocomplete
	print("shiny")
	argcomplete.autocomplete(parser)
	
	# Parse the arguments
	args = parser.parse_args()

	if args.command == "run":
		print(f"Running script: {args.scriptname}")
	else:
		parser.print_help()

if __name__ == "__main__":
	main()
