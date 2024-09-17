import os
import sys
import fnmatch
import re

def read_patterns(filename):
    """Read patterns from a file, returning a list of strings."""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found. Using empty list.")
        return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def should_include(file_path, include_patterns):
    """Check if a file should be included based on the include patterns."""
    return any(fnmatch.fnmatch(os.path.basename(file_path), pattern) for pattern in include_patterns)

def should_exclude(file_path, exclude_patterns, base_folder):
    """Check if a file or directory should be excluded based on the exclude patterns."""
    relative_path = os.path.relpath(file_path, base_folder)
    for pattern in exclude_patterns:
        pattern = pattern.lstrip('/')
        if pattern.endswith('/*'):
            if relative_path.startswith(pattern[:-2]):
                return True
        elif fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(relative_path, f"**/{pattern}"):
            return True
    return False

def crawl_directory(folder, include_patterns, exclude_patterns):
    """Recursively crawl the directory and yield files that match the criteria."""
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_patterns, folder)]
        for file in files:
            file_path = os.path.join(root, file)
            if should_include(file_path, include_patterns) and not should_exclude(file_path, exclude_patterns, folder):
                yield file_path

def delete_file_if_exists(filename):
    """Delete the file if it exists."""
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Deleted existing {filename}")

def read_notes(filename):
    """Read the contents of the notes file if it exists."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"Warning: {filename} not found. Proceeding without notes.")
        return ""

def optimize_content(content, file_extension):
    """Optimize content by removing extra whitespace and comments."""
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()

    # Remove comments (you may want to keep some comments, adjust as needed)
    if file_extension in ['.js', '.ts', '.jsx', '.tsx', '.css']:
        content = re.sub(r'\/\/.*?$|\/\*.*?\*\/', '', content, flags=re.MULTILINE|re.DOTALL)
    elif file_extension in ['.py']:
        content = re.sub(r'#.*?$|\'\'\'.*?\'\'\'|""".*?"""', '', content, flags=re.MULTILINE|re.DOTALL)
    elif file_extension in ['.html', '.xml']:
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    return content

def main():
    if len(sys.argv) < 3 or sys.argv[1] != '--folder':
        print("Usage: python main.py --folder <folder_path> [--build]")
        sys.exit(1)

    folder = os.path.abspath(os.path.expanduser(sys.argv[2]))
    build_mode = '--build' in sys.argv

    include_patterns = read_patterns('include.txt')
    exclude_patterns = read_patterns('ignore.txt')

    matching_files = list(crawl_directory(folder, include_patterns, exclude_patterns))

    if build_mode:
        delete_file_if_exists('output.txt')
        notes = read_notes('notes.txt')
        
        with open('output.txt', 'w', encoding='utf-8') as outfile:
            if notes:
                outfile.write("NOTES: ")
                outfile.write(optimize_content(notes, '.txt'))
                outfile.write("\n")
            
            for file_path in matching_files:
                relative_path = os.path.relpath(file_path, folder)
                file_extension = os.path.splitext(file_path)[1]
                outfile.write(f"FILE: /{relative_path}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                    optimized_content = optimize_content(content, file_extension)
                    outfile.write(optimized_content)
                    outfile.write('\n')
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        print("Created optimized output.txt with aggregated file contents.")
    else:
        delete_file_if_exists('run-scope.txt')
        with open('run-scope.txt', 'w', encoding='utf-8') as scope_file:
            for file_path in matching_files:
                relative_path = os.path.relpath(file_path, folder)
                scope_file.write(f"/{relative_path}\n")
        print("Created run-scope.txt with the list of files that would be included.")

if __name__ == "__main__":
    main()