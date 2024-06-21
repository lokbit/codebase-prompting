# Project: Codebase Traversal and Gemini AI Integration

This repository contains two Python scripts: `base_print.py` and `base_print_ai.py`.

## `base_print.py`

This script traverses a given directory, collects all text files (with certain extensions), and writes their content to an output file. It handles large files by skipping them and provides a continuation mechanism using a unique key.

### Features
- Traverses directories, ignoring specified folders and files.
- Collects text file contents up to specified limits.
- Generates a continuation key to resume processing.
- Outputs a directory tree with indicators for processed and skipped files.

### Usage
1. **Run the Script**:
    ```bash
    python base_print.py [directory] [continue_key]
    ```
    - `directory`: The directory to search (default is the current directory).
    - `continue_key`: The key to continue from where it left off (optional).

2. **Output**:
    - Generates `codebase_n.txt` with the collected contents and directory tree.
    - Prints the continuation key if the line limit is reached.

## `base_print_ai.py`

This script extends the functionality of `base_print.py` by integrating with the Google Gemini API. It uses the API to determine relevant files based on a user prompt and processes those files.

### Features
- Integrates with Google Gemini API for intelligent file selection.
- Processes files based on the relevance determined by the API.
- Outputs a directory tree with indicators for processed and skipped files.

### Usage
1. **Set Up API Key**:
    - Ensure you have set the `API_KEY` environment variable with your Google Gemini API key.

2. **Run the Script**:
    ```bash
    python base_print_ai.py [directory] [continue_key]
    ```
    - `directory`: The directory to search (default is the current directory).
    - `continue_key`: The key to continue from where it left off (optional).

3. **Output**:
    - Generates `prompt_n.txt` with the collected contents and directory tree.
    - Prompts the user for an input prompt to guide the file selection process.
