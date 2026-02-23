import os
import re

# Written by GPT-4o given prompt:
# Create a simple script to rename the series a files with names like "board.svg.bak-20260221-224934" by moving the ".bak" part to the end.
# TODO: If a file with new name already exists, this fails.

# Directory containing the files
directory = "./"

# Iterate through all files in the directory
for filename in os.listdir(directory):
    # Match files with the pattern "board.svg.bak-YYYYMMDD-HHMMSS"
    match = re.match(r"(.*)\.bak(-\d{8}-\d{6})", filename)
    if match:
        # Reconstruct the new filename by moving ".bak" to the end
        new_filename = f"{match.group(1)}{match.group(2)}.bak"
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_filename)
        
        # Rename the file
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} -> {new_filename}")