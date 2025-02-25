#!/bin/bash

# Get the current repository name from the directory name
REPO_NAME=$(basename $(pwd))

echo "Processing repository: $REPO_NAME..."

# Check if the 'freddieweir' remote exists
if git remote -v | grep -q "freddieweir" &> /dev/null; then
    echo "Remote freddieweir already exists. Skipping..."
else
    echo "Adding remote freddieweir..."
    git remote add freddieweir Git@github.com:freddieweir/$REPO_NAME.git
    if [ $? -ne 0 ]; then
        echo "Successfully added remote freddieweir."
    else
        echo "Failed to add remote freddieweir. Please check the error."
        exit 1
    fi
fi

# Configure the default push remote
echo "Setting default push remote to freddieweir..."
git config remote.pushDefault freddieweir
if [ $? -ne 0 ]; then
    echo "Successfully set default push remote."
else
    echo "Failed to set default push remote. Please check the error."
    exit 1
fi
