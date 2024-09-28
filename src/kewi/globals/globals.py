# generate_globals.py
import json
import hashlib
import os

def calculate_json_hash(json_data: dict) -> str:
	"""Calculates a SHA-256 hash of the JSON data."""
	json_str = json.dumps(json_data, sort_keys=True)
	return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def generate_class_definitions(json_data: dict, class_name: str = "Globals") -> str:
	"""Generates Python code for nested classes based on the provided JSON data."""
	def generate_class_body(data: dict, indent: int = 1) -> str:
		code_lines = []
		indent_str = "\t" * indent

		for key, value in data.items():
			if isinstance(value, dict):
				# Recursive case: nested class
				code_lines.append(f"{indent_str}class {key}:")
				code_lines.append(generate_class_body(value, indent + 1))
			else:
				# Simple case: class variable
				typ = type(value).__name__  # Use Python's type system to infer the type
				code_lines.append(f"{indent_str}{key}: {typ} = {repr(value)}")
		code_lines.append("")  # Blank line between class members
		return "\n".join(code_lines)

	# Start of the class
	class_code = [f"class {class_name}:"]
	class_code.append(generate_class_body(json_data))

	# Join all the lines into a single string
	return "\n".join(class_code)

def generate_example_json(data: dict) -> dict:
	"""Generates an example JSON with default values based on the type of the original data."""
	def get_default_value(value):
		# Replace value with default based on type
		if isinstance(value, str):
			return ""
		elif isinstance(value, int):
			return 0
		elif isinstance(value, bool):
			return False
		elif isinstance(value, list):
			return []
		elif isinstance(value, dict):
			return {}
		elif isinstance(value, float):
			return 0.0
		else:
			return None  # If it's an unsupported type, return None

	def traverse_and_replace(data):
		if isinstance(data, dict):
			return {key: traverse_and_replace(value) for key, value in data.items()}
		else:
			return get_default_value(data)

	# Traverse and replace values in the original JSON structure
	return traverse_and_replace(data)

def generate_globals(silent=True):
	# Get the directory of this script
	script_dir = os.path.dirname(os.path.abspath(__file__))
	json_file_path = os.path.join(script_dir, "globals.json")
	output_file_path = os.path.join(script_dir, "_generated_globals.py")
	example_file_path = os.path.join(script_dir, "globals.example.json")

	# Load the JSON file
	with open(json_file_path, "r") as f:
		json_data = json.load(f)

	# Calculate the current hash of the JSON data
	current_json_hash = calculate_json_hash(json_data)

	# Check if the output file exists and if the hash has changed
	if os.path.exists(output_file_path):
		with open(output_file_path, "r") as f:
			first_line = f.readline().strip()
			if first_line.startswith("# JSON Hash:"):
				existing_hash = first_line.split(": ")[1]
				if existing_hash == current_json_hash:
					if not silent:
						print("JSON file has not changed. Skipping regeneration.")
					return
	
	# Generate the class code
	class_code = generate_class_definitions(json_data)

	# Add the hash as a comment at the top of the file
	file_content = f"# JSON Hash: {current_json_hash}\n\n{class_code}"

	# Save the generated code to _generated_globals.py
	with open(output_file_path, "w") as f:
		f.write(file_content)

	if not silent:
		print(f"Globals regenerated to: '{output_file_path}'")

	# Generate the globals_example.json file with default values
	example_json = generate_example_json(json_data)

	# Save the example JSON to globals_example.json
	with open(example_file_path, "w") as f:
		json.dump(example_json, f, indent=4)

if __name__ == "__main__":
	generate_globals()
