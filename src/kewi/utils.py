import os

def RESOURCE_PATH(sub_path):
	# Get the directory where this script (and your library) is located
	base_dir = os.path.dirname(os.path.abspath(__file__))

	# Construct the full path to 'resources/private/cache' by navigating up and down the directory structure
	resource_dir = os.path.join(base_dir, '..', '..', 'resources', sub_path)
	return os.path.abspath(resource_dir)  # Return the absolute path

