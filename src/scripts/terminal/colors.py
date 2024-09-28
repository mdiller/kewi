# color_table_updated.py
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init(autoreset=True)

print("Columns are Back.___")
print("Rows are Fore.___")
print()

# Foreground and Background labels, with default/reset added
foregrounds = ['RESET', 'BLACK', 'RED', 'GREEN', 'YELLOW', 
               'BLUE', 'MAGENTA', 'CYAN', 'WHITE']
backgrounds = ['RESET', 'BLACK', 'RED', 'GREEN', 'YELLOW', 
               'BLUE', 'MAGENTA', 'CYAN', 'WHITE']

# Foreground and Background colors
fg_colors = [Fore.RESET, Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, 
             Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
bg_colors = [Back.RESET, Back.BLACK, Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, 
             Back.MAGENTA, Back.CYAN, Back.WHITE]

# Define column width based on the longest background label
col_width = max(len(bg) for bg in backgrounds) + 2

# Print the table header (offset by 2 characters)
print(f"{'':<12}", end="  ")  # Empty cell with 2 character offset
for bg_label in backgrounds:
	print(f"{bg_label:<{col_width}}", end=" ")
print()  # Newline after headers
print()

# Print rows of colors, starting with the default/reset foreground
for fg_label, fg_color in zip(foregrounds, fg_colors):
	# Print the foreground label for the row
	print(f"{fg_label:<10}", end="  ")
	# Print each cell in the row with the corresponding background and text "HELLO THERE"
	for bg_color in bg_colors:
		print(f"{fg_color}{bg_color}{'  Hello':<{col_width}}", end=" ")
	print()  # Newline after each row

# Reset colorama on exit
colorama.deinit()
