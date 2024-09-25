#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from argcomplete.completers import ChoicesCompleter

from kewi.core.runner import Runner
import kewi

runner = Runner()

# TODO: update autocomplete to be smarter and support my custom arguments for my scripts. also see if we can make it support the discord autocomplete too.

# Define a completer function for script names
def scriptname_completer(prefix, parsed_args, **kwargs):
	scripts = runner.list_scripts()
	names =  [script.name for script in scripts if script.name.startswith(prefix)]
	return names

def list_scripts(cmd_namespace):
	scripts = runner.list_scripts()
	for script in scripts:
		# TODO: print a table with name, description in future here.
		kewi.out.print(f"{script.name}")

def run_script(scriptname):
	script = runner.get_script(scriptname)
	if script:
		runner.run_script(script)
	else:
		kewi.out.print(f"Couldn't find a script by that name")

def main():
	# Create the argument parser
	parser = argparse.ArgumentParser(description="Kewi CLI for running scripts.")
	subparsers = parser.add_subparsers(dest="command")

	list_parser = subparsers.add_parser("list", help="List available scripts")
	list_parser.set_defaults(func=list_scripts)

	run_parser = subparsers.add_parser("run", help="Run a script by name")
	run_parser.add_argument(
		"scriptname",
		help="The name of the script to run"
	).completer = scriptname_completer
	run_parser.set_defaults(func=lambda args: run_script(args.scriptname))

	help_parser = subparsers.add_parser("help", help="Show help information")
	help_parser.set_defaults(func=lambda args: parser.print_help())

	# Enable tab completion
	argcomplete.autocomplete(parser)

	# Parse the arguments
	args = parser.parse_args()

	# If no command is provided, show help
	if args.command:
		args.func(args)
	else:
		parser.print_help()

if __name__ == "__main__":
	main()
