from typing import Any


from .get_config_files import get_config_files


def get_config(path:str, constant:str) -> Any | bool:
    """
    Get a key from a yaml file.

    Args:
        path (str): The path to the desired key, using dot notation for nested structures.
        constant (str): The specific key to retrieve.

    Returns:
        Union[Any, bool]: The value of the key if found, False otherwise.

    Examples:
        >>> config("SYSTEM", "CONCURRENCY_LIMIT")
        2
        >>> config("SYSTEM", "NONEXISTENT_KEY") or 3
        3
    """
    keys = path + "." + constant

    # Load private and public config.yaml files.
    data: dict = get_config_files()

    # Split the path into individual keys
    keys = path.split('.') + [constant]

    # Traverse the nested dictionary
    try:
        for key in keys:
            if key in data:
                data = data[key]
            else:
                print(f"Could not load config {constant}. Using default instead.")
                return False
        return data
    except:
        print(f"Could not load config {constant}. Using default instead.")
        return False