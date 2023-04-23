import os

def print_tree(path, prefix):
    # Print the current directory name
    print(prefix + os.path.basename(path) + "/")

    # Add a pipe symbol to the prefix to create the subdirectory prefix
    prefix = prefix + "|   "

    # Recursively print all subdirectories and files
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and item_path not in ['images','labels','.git']:
            print_tree(item_path, prefix)
        else:
            print(prefix + item)

# Get the current working directory
cwd = os.getcwd()

# Print the current working directory
print(f"Current directory: {cwd}\n")

# Print the directory tree structure
print_tree(cwd, "")
