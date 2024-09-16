import os
import sys
import fnmatch

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
        # Remove excluded directories
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

def main():
    # Parse command-line arguments
    if len(sys.argv) < 3 or sys.argv[1] != '--folder':
        print("Usage: python main.py --folder <folder_path> [--build]")
        sys.exit(1)

    folder = os.path.abspath(os.path.expanduser(sys.argv[2]))
    build_mode = '--build' in sys.argv

    # Read include and exclude patterns
    include_patterns = read_patterns('include.txt')
    exclude_patterns = read_patterns('ignore.txt')

    # Crawl the directory
    matching_files = list(crawl_directory(folder, include_patterns, exclude_patterns))

    if build_mode:
        # Delete existing output.txt if it exists
        delete_file_if_exists('output.txt')
        
        # Read notes
        notes = read_notes('notes.txt')
        
        # Build the aggregated file
        with open('output.txt', 'w', encoding='utf-8') as outfile:
            # Write notes at the beginning
            if notes:
                outfile.write("// Contents of notes.txt\n\n")
                outfile.write(notes)
                outfile.write("\n\n// End of notes.txt\n\n")
            
            # Write contents of other files
            for file_path in matching_files:
                outfile.write(f"// Contents of file: {file_path}\n\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write('\n\n')
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        print("Created output.txt with aggregated file contents.")
    else:
        # Delete existing run-scope.txt if it exists
        delete_file_if_exists('run-scope.txt')
        
        # Create run-scope.txt with the list of files (relative paths)
        with open('run-scope.txt', 'w', encoding='utf-8') as scope_file:
            for file_path in matching_files:
                relative_path = os.path.relpath(file_path, folder)
                scope_file.write(f"/{relative_path}\n")
        print("Created run-scope.txt with the list of files that would be included.")

if __name__ == "__main__":
    main()