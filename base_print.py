import os
import argparse
from colorama import Fore, Style, init
import mimetypes
import hashlib

init()

text_file_extensions = {'.pug', '.js', '.jsx', '.txt', '.html', '.css', '.py', '.scss'}
ignore_dirs = {'.git', 'node_modules', '.vscode', 'dist'}
ignore_files = {'codebase.txt'}
max_lines = 2000
max_total_lines = 3000
left_off_indicator = "🛑"  # Emoji to indicate the last completed file

def get_directory_to_search():
    parser = argparse.ArgumentParser(description="Directory traversal script")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to search")
    parser.add_argument("continue_key", nargs="?", help="Key to continue from where it left off")
    args = parser.parse_args()
    return args.directory, args.continue_key

def write_content(file_path, output_file, total_lines):
    try:
        with open(file_path, 'r', errors='ignore') as f:
            contents = f.readlines()
            if len(contents) <= max_lines:
                new_total_lines = total_lines + len(contents) + 2  # including file path and blank line
                if new_total_lines > max_total_lines:
                    output_file.write(f"{file_path}\n\n{''.join(contents)}\n\n")
                    total_lines = new_total_lines
                    return False, total_lines, file_path  # Stopped due to line limit
                output_file.write(f"{file_path}\n\n{''.join(contents)}\n\n")
                total_lines = new_total_lines
                return True, total_lines, None
            else:
                print(f"{Fore.YELLOW}skipped -> {os.path.basename(file_path)} | too big{Style.RESET_ALL}")
                return True, total_lines, None
    except Exception as e:
        print(f"{Fore.RED}skipped -> {os.path.basename(file_path)} | unreadable type (not text){Style.RESET_ALL}")
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

def gen_code(directory, continue_key):
    skipped_files = []
    total_lines = 0
    files_to_process = []
    continue_found = continue_key is None

    for root, dirs, files in os.walk(directory):
        if any(ignore_dir in root for ignore_dir in ignore_dirs):
            continue

        for file in files:
            if file not in ignore_files:
                file_path = os.path.join(root, file)
                if is_text_file(file_path):
                    if not continue_found:
                        if hashlib.md5(file_path.encode()).hexdigest() == continue_key:
                            continue_found = True
                    if continue_found:
                        files_to_process.append(file_path)
                else:
                    skipped_files.append(file_path)
                    print(f"{Fore.YELLOW}skipped -> {os.path.basename(file_path)} | unreadable type (not text){Style.RESET_ALL}")

    i = 1
    while os.path.exists(f"codebase_{i}.txt"):
        i += 1

    codebase_filename = f"codebase_{i}.txt"
    with open(codebase_filename, "w", encoding='utf-8') as output_file:
        for file_path in files_to_process:
            success, total_lines, stop_file = write_content(file_path, output_file, total_lines)
            if not success:
                continue_key = hashlib.md5(stop_file.encode()).hexdigest()
                print(f"\n{Fore.RED}Continue key: {continue_key}{Style.RESET_ALL}")
                break
            if stop_file:
                skipped_files.append(stop_file)
    return skipped_files, codebase_filename, continue_key, stop_file

def generate_tree(directory, skipped_files, stop_file):
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
        for i, d in enumerate(dirs):
            connector = '├── ' if i < len(dirs) - 1 else '└── '
            tree_lines.append(f"{sub_indent}{connector}{d}/")
        for i, f in enumerate(files):
            connector = '├── ' if i < len(files) - 1 else '└── '
            file_indicator = ' ❌' if os.path.join(root, f) in skipped_files else ''
            file_stop_indicator = f"{file_indicator} {left_off_indicator}" if os.path.join(root, f) == stop_file else file_indicator
            tree_lines.append(f"{sub_indent}{connector}{f}{file_stop_indicator}")
    return '\n'.join(tree_lines)

def main():
    directory, continue_key = get_directory_to_search()
    
    print(f"\n{Fore.BLUE}Generating codebase.txt...{Style.RESET_ALL}")
    skipped_files, codebase_filename, continue_key, stop_file = gen_code(directory, continue_key)
    
    print(f"\n{Fore.BLUE}Generating directory tree...{Style.RESET_ALL}")
    tree = generate_tree(directory, skipped_files, stop_file)
    
    with open(codebase_filename, "a", encoding='utf-8') as output_file:
        output_file.write("\n[Directory Tree]\n")
        output_file.write(tree)
    
    print(f"\n{Fore.GREEN}Completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
