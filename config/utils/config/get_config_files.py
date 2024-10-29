import os


import yaml


def get_config_files() -> dict:
    """
    Load YAML configuration files and return their contents.
    
    ### Returns
    - Dictionary with the loaded configuration data.
    
    ### Raises
    - FileNotFoundError: If either config file is not found.
    - yaml.YAMLError: If there's an error parsing the YAML files.
    """
    
    # Get the filepaths of all the config files.
    top_level_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"top_level_dir: {top_level_dir}")
    #main_script_dir = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), "main.py")))


    config_path = os.path.join(top_level_dir, 'config.yaml')
    priv_config_path = os.path.join(top_level_dir, 'private_config.yaml')
    _priv_config_path = os.path.join(top_level_dir, '_private_config.yaml')
    config_dict = {}
    #print(f"config_path: {config_path}\n priv_config_path: {priv_config_path}\n_priv_config_path: {_priv_config_path}")

    # If private_config.yaml doesn't exist and _private_config.yaml does,
    # Set the path for _private_config.yaml as the private_config.yaml path
    if not os.path.exists(priv_config_path) and os.path.exists(_priv_config_path):
        priv_config_path = _priv_config_path

    try:
        with open(config_path, "r") as f:
            config:dict = yaml.safe_load(f)
            config_dict.update(config)
        with open(priv_config_path, "r") as f:
            priv_config = yaml.safe_load(f)
            config_dict.update(priv_config)
    except FileNotFoundError as e:
        print(f"Configuration file not found: {e.filename}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error loading configuration files: {e}")
        raise

    return config_dict