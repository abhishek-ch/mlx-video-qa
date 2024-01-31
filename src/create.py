from pathlib import Path


def find_project_root(markers=['.git', 'requirements.txt']):
    """
    Traverse up from current_path to find the project root.
    The project root is identified by the presence of any of the specified markers.
    """

    current_file_path = Path(__file__).parent
    # Convert to Path object if current_path is a string
    current_path = Path(current_file_path)

    # Traverse up the directory tree
    for parent in current_path.parents:
        # Check if any of the markers exist in this directory
        if any((parent / marker).exists() for marker in markers):
            # Get one level above the project root
            return parent
    raise FileNotFoundError("Project root could not be found.")


def find_level_above_project_root():
    return find_project_root().parent
