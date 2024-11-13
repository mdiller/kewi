#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from kewi.context import KewiContextConsole
from kewi.core.runner import Runner
import kewi

runner = Runner()

# Define a completer function for script names
# TODO: this autocomplete thing should list all the dirs and scripts in this directory, not the full paths to all of the scripts we have
def scriptname_completer(prefix, parsed_args, **kwargs):
	scripts = runner.list_scripts()
	names =  [script.name for script in scripts if script.name.startswith(prefix)]
	return names

def list_scripts(cmd_namespace):
	scripts = runner.list_scripts()
	for script in scripts:
		kewi.ctx.print(f"{script.name}")

def run_script(scriptname, cli_args):
	script = runner.get_script(scriptname)
	if script:
		ctx = KewiContextConsole(cli_args)
		runner.run_script(script, ctx)  # Pass the CLI arguments to the runner
	else:
		kewi.ctx.print(f"Couldn't find a script by that name")

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
	run_parser.add_argument(
		"script_args", 
		nargs=argparse.REMAINDER,  # Accept additional arguments as script arguments
		help="Arguments to pass to the script"
	)
	run_parser.set_defaults(func=lambda args: run_script(args.scriptname, args.script_args))

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
