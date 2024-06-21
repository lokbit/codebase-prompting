import os
import argparse
import google.generativeai as genai
from colorama import Fore, Style, init
import mimetypes

init()

# Configure Google Gemini API
genai.configure(api_key=os.environ['API_KEY'])

text_file_extensions = {'.pug', '.js', '.jsx', '.txt', '.html', '.css', '.py', '.scss'}
ignore_dirs = {'.git', 'node_modules', '.vscode', 'dist'}
ignore_files = {'codebase.txt'}
max_lines = 2000
max_total_lines = 3000
checkmark_indicator = "✅"  # Emoji to indicate successfully processed files
cross_indicator = "❌"  # Emoji to indicate skipped files


def find_file(directory, file_name):
    for root, dirs, files in os.walk(directory):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def get_directory_to_search():
    parser = argparse.ArgumentParser(description="Directory traversal script")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to search")
    parser.add_argument("continue_key", nargs="?", help="Key to continue from where it left off")
    args = parser.parse_args()
    return args.directory, args.continue_key

def get_user_prompt():
    prompt = input("Please enter your prompt: ")
    return prompt

def call_gemini_api(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def write_content(file_path, output_file, total_lines):
    try:
        with open(file_path, 'r', errors='ignore') as f:
            contents = f.readlines()
            if len(contents) <= max_lines:
                new_total_lines = total_lines + len(contents) + 2  # including file path and blank line
                if new_total_lines > max_total_lines:
                    output_file.write(f"{os.path.basename(file_path)} {checkmark_indicator}\n\n{''.join(contents)}\n\n")
                    total_lines = new_total_lines
                    return False, total_lines, file_path  # Stopped due to line limit
                output_file.write(f"{os.path.basename(file_path)} {checkmark_indicator}\n\n{''.join(contents)}\n\n")
                total_lines = new_total_lines
                return True, total_lines, None
            else:
                print(f"{Fore.YELLOW}skipped -> {os.path.basename(file_path)} | too big {cross_indicator}{Style.RESET_ALL}")
                return True, total_lines, None
    except Exception as e:
        print(f"{Fore.RED}skipped -> {os.path.basename(file_path)} | unreadable type (not text) {cross_indicator}{Style.RESET_ALL}")
        print(e)
        return True, total_lines, None

def is_text_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    ext = os.path.splitext(file_path)[1]
    if mime_type:
        if mime_type.startswith('text'):
            return True
        elif mime_type in ['application/json', 'application/javascript']:
            return True
    return ext in text_file_extensions

def generate_file_tree(directory):
    tree_lines = []
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * (level)
        if os.path.basename(root) in ignore_dirs:
            tree_lines.append(f"{indent}{os.path.basename(root)}/ [skipped]")
            dirs[:] = []
            continue
        tree_lines.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for d in dirs:
            tree_lines.append(f"{sub_indent}├── {d}/")
        for f in files:
            tree_lines.append(f"{sub_indent}└── {f}")
    return '\n'.join(tree_lines)

def clean_file_paths(file_list):
    cleaned_files = []
    for file in file_list.split('\n'):
        if file.strip():
            cleaned_file = os.path.basename(file.strip().split(' ', 1)[-1])
            cleaned_files.append(cleaned_file)
    return cleaned_files

def gen_code(directory, file_list):
    skipped_files = []
    processed_files = []
    encountered_files = []
    total_lines = 0
    cleaned_files = clean_file_paths(file_list)
    
    print("\n--- Files to Process ---\n")
    print(cleaned_files)

    i = 1
    while os.path.exists(f"prompt_{i}.txt"):
        i += 1

    prompt_filename = f"prompt_{i}.txt"
    with open(prompt_filename, "w", encoding='utf-8') as output_file:
        for file_name in cleaned_files:
            file_path = find_file(directory, file_name)
            if file_path:
                encountered_files.append(file_path)
                if is_text_file(file_path):
                    success, total_lines, stop_file = write_content(file_path, output_file, total_lines)
                    if success:
                        processed_files.append(file_path)
                        print(f"{Fore.GREEN}processed -> {file_name} {checkmark_indicator}{Style.RESET_ALL}")
                    if not success:
                        break
                else:
                    skipped_files.append(file_path)
                    print(f"{Fore.YELLOW}skipped -> {file_name} | unreadable type (not text) {cross_indicator}{Style.RESET_ALL}")
            else:
                skipped_files.append(os.path.join(directory, file_name))
                print(f"{Fore.YELLOW}skipped -> {file_name} | file not found {cross_indicator}{Style.RESET_ALL}")

    return skipped_files, prompt_filename, processed_files, encountered_files

def generate_tree_with_exclusions(directory, skipped_files, processed_files):
    tree_lines = []
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * (level)
        if any(ignore_dir in root for ignore_dir in ignore_dirs):
            tree_lines.append(f"{indent}{os.path.basename(root)}/ [skipped]")
            dirs[:] = []  # Do not process any subdirectories
            continue
        tree_lines.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for d in dirs:
            tree_lines.append(f"{sub_indent}├── {d}/")
        for f in files:
            connector = '├── ' if files.index(f) < len(files) - 1 else '└── '
            file_path = os.path.join(root, f)
            if file_path in processed_files:
                file_indicator = f' {checkmark_indicator}'
            elif file_path in skipped_files:
                file_indicator = f' {cross_indicator}'
            else:
                file_indicator = f' {cross_indicator}'  # Add X for files that weren't processed
            tree_lines.append(f"{sub_indent}{connector}{f}{file_indicator}")
    return '\n'.join(tree_lines)

def main():
    directory, continue_key = get_directory_to_search()
    user_prompt = get_user_prompt()
    
    print(f"\n{Fore.BLUE}Generating file tree...{Style.RESET_ALL}")
    file_tree = generate_file_tree(directory)
    
    print(f"\n{Fore.BLUE}Calling Google Gemini API...{Style.RESET_ALL}")
    modified_prompt = (
        f"Act as if you are EXTREMELY good at being able to identify what project files do what. "
        f"Now, if you were given the prompt \"{user_prompt}\" and given these project files: {file_tree}, "
        "what files do you believe you would need to see in order to answer the prompt correctly. "
        "Give me the names of the files in this order:\n"
        "1. file_name\n"
        "2. file_name\n"
        "3. file_name\n\n"
        "Make sure that you do not add any extra context (like explaining anything). I ONLY want the file names you think would be appropriate for solving this prompt."
    )
    print("\n--- AI Prompt ---\n")
    print(modified_prompt)
    relevant_files = call_gemini_api(modified_prompt)
    print("\n--- AI Response ---\n")
    print(relevant_files)
    
    print(f"\n{Fore.BLUE}Generating prompt file...{Style.RESET_ALL}")
    skipped_files, prompt_filename, processed_files, encountered_files = gen_code(directory, relevant_files)
    
    print(f"\n{Fore.BLUE}Generating directory tree...{Style.RESET_ALL}")
    tree = generate_tree_with_exclusions(directory, skipped_files, processed_files)
    
    with open(prompt_filename, "a", encoding='utf-8') as output_file:
        output_file.write("\n[Directory Tree]\n")
        output_file.write(tree)
    
    print(f"\n{Fore.GREEN}Completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
