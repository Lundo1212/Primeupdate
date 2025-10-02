import os

IGNORE_DIRS = {"venv", "__pycache__", ".git", ".idea", ".vscode"}

def print_tree(startpath, prefix=""):
    try:
        items = sorted(os.listdir(startpath))
    except PermissionError:
        return

    for i, item in enumerate(items):
        if item in IGNORE_DIRS or item.startswith("."):
            continue

        path = os.path.join(startpath, item)
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + item)

        if os.path.isdir(path):
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    print("Project Tree:\n")
    print_tree(".")
