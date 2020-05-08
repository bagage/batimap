#!/bin/bash

modified_files=$(git diff --relative --name-only origin/master . | grep 'src/app/.*\.ts$' | head -c -1 | tr '\n' ',' | sed 's/,/ --files /g')

if [ ! -z "$modified_files" ]; then
	echo "Checking lint for $modified_files"
	output="$(npm run lint -- --files $modified_files)"
	result=$?
	if grep -E 'Fixed [0-9]+ error' <<< "$output"; then
		echo "Some lint errors were fixed. Please check and commit:"
		echo "$output"
		exit 1
	elif [ $result != 0 ]; then
		echo "Lint failed. Please check and fix:"
		echo "$output"
		exit 1
	fi
else
	echo "No files to lint, skipping"
fi
