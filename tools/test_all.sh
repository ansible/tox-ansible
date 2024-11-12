#!/bin/bash

# Exit on any error
set -e

# ARGUMENTS
COLLECTION_NAME=$1
MATRIX=$2

# Install pyenv if not present
if ! command -v pyenv > /dev/null; then
    echo "pyenv is not installed. Installing pyenv..."
    curl https://pyenv.run | bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
else
    echo "pyenv is installed. Moving forward..."
fi

# Set up Python 3.11
echo "Setting up Python 3.11"
pyenv install -s 3.11
pyenv global 3.11
python3 -m pip install --upgrade pip
python3 -m pip install ../.
python3 -m pip install --user ansible-creator

# Create a collection
mkdir example
cd example
ansible-creator init collection "$COLLECTION_NAME"
git add .

# Generate matrix with tox
if [[ -z "$MATRIX" ]]; then
    echo "Generating matrix..."
    MATRIX=$(python3 -m tox --ansible --gh-matrix --conf tox-ansible.ini)
fi

# Parse JSON to create arrays for entries
ENTRIES=($(echo "$MATRIX" | jq -r '.[] | .name'))
PYTHON_VERSIONS=($(echo "$MATRIX" | jq -r '.[] | .python'))

# Empty array to hold failed entries
FAILED_TESTS=()

# Loop through each entry and its corresponding Python version
for i in "${!ENTRIES[@]}"; do
    ENTRY=${ENTRIES[i]}
    PYTHON_VERSION=${PYTHON_VERSIONS[i]}

    echo "Setting up Python $PYTHON_VERSION for $ENTRY..."

    if command -v pyenv > /dev/null; then
        pyenv install -s "$PYTHON_VERSION"
        pyenv local "$PYTHON_VERSION"
    else
        echo "pyenv is not installed. Please install Python $PYTHON_VERSION manually"
        exit 1
    fi

    if [ "$PYTHON_VERSION" = "3.9" ]; then
        python3 -m pip install tox-ansible==24.2.0
    else
        python3 -m pip install ../../.
    fi

    echo "Running tests for $ENTRY with Python $PYTHON_VERSION..."
    if python3 -m tox --ansible -e "$ENTRY" --conf tox-ansible.ini; then
        echo "$ENTRY passed."
    else
        echo "$ENTRY failed"
        FAILED_TESTS+=("$ENTRY")
    fi

    # Reset Python version to system default for local environments
    if command -v pyenv > /dev/null; then
        pyenv local --unset
    fi
done

# Output summary of results
if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo "All tests passed successfully"
else
    echo "The following tests failed:"
    for FAILED in "${FAILED_TESTS[@]}"; do
        echo "- $FAILED"
    done
    exit 1
fi
