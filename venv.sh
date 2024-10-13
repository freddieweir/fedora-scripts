#!/bin/bash
# Get the project directory name
project_name=$(basename "$PWD")

# Create a new virtual environment named after the project
python3 -m venv "$project_name-env"

# Activate the environment (optional for automation)
source "$project_name-env/bin/activate"

# Output message
echo "Virtual environment '$project_name-env' created and activated."
