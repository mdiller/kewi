#!/bin/bash

# Get the directory where this script (register_kewi.sh) is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -W )"

# Reference to the cli_main.py file (assuming it's in the same directory)
CLI_PATH="$SCRIPT_DIR/cli_main.py"

# Create the alias for 'kewi' command
alias kewi="python \"$CLI_PATH\""

# eval "$(register-python-argcomplete kewi)"



# # Manually register the completion function for 'kewi'
# _kewi_autocomplete() {
#     # Call the Python script with autocomplete mode
#     # COMPREPLY=( $(COMP_LINE="$COMP_LINE" COMP_POINT="$COMP_POINT" _ARGCOMPLETE=1 python "$CLI_PATH") )
#     COMPREPLY=( $(COMP_LINE="$COMP_LINE" COMP_POINT="$COMP_POINT" _ARGCOMPLETE=1 python "$CLI_PATH") )
#     return 0
# }

# # Enable the completion for the kewi command
# complete -o nospace -F _kewi_autocomplete kewi


# FUCKING PYTHON ARGCOMPLETE IS A PIECE OF SHIT AND DOESNT WORK PROPERLY, SO LETS DO THIS MANUALLY
_my_completion_function() {
    # Get the current word being completed
    local cur="${COMP_WORDS[COMP_CWORD]}"

    # Call the Python script and capture its output
    local IFS=$'\n'
    local completions=($(COMP_WORD="$cur" python "$CLI_PATH" list | tr -d '\r'))

    # Filter the completions based on the current input
    COMPREPLY=( $(compgen -W "${completions[*]}" -- "$cur") )
}

# Register the completion function for a command
complete -F _my_completion_function kewi