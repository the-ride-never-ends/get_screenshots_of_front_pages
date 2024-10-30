import os


import pandas as pd


from logger.logger import Logger
from config.config import CSV_OUTPUT_FOLDER


def save_list_of_dicts_to_csv_via_pandas(list_of_dicts: list[dict],
                                        filepath: str,
                                        index: bool = False,
                                        return_df: bool = False,
                                        logger: Logger = None,
                                        mode: str = 'a',
                                        ) -> None|pd.DataFrame:
    """
    Save a list of dictionaries to a CSV file using Pandas DataFrame.

    TODO Add in other options. Pandas has a LOT of them.

    Args:
        list_of_dicts (list[dict]): A list of dictionaries to be saved as CSV.
        filepath (str): The filepath of the output CSV file.
        index (bool, optional): Whether to write row index. Defaults to False.
        logger (Logger, optional): Logger object for logging messages. If None, an assertion error is raised.
        output_path (str, optional): Custom output path for the CSV file. If None, uses the default CSV_OUTPUT_FOLDER.
        return_df (bool, optional): Whether to also return the dataframe itself in addition to saving it.
    
    Return:
       None or pd.DataFrame: Returns None by default. If return_df is True, returns the created DataFrame that waas saved to the CSV file.

    Raises:
        ValueError: If the input is not a list of dictionaries.
        AssertionError: If no logger is provided.

    Example:
    >>> data = [{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}]
    >>> list_of_dicts_to_csv_via_pandas(data, 'output.csv', logger=my_logger)
    """
    logger.debug(f"list_of_dicts\n{list_of_dicts}",f=True)
    # Type checking.
    if not isinstance(list_of_dicts, list) or not isinstance(list_of_dicts[0], dict):
        error_message = f"list_of_dicts argument is not a list of dicts, but a {type(list_of_dicts)}"
        logger.error(error_message)
        raise ValueError(error_message)
    assert logger, "No logger provided."

    # Export list_of_dicts to a CSV file.
    df = pd.DataFrame().from_records(list_of_dicts)
    logger.info(f"DataFrame created with shape {df.shape}. Saving to {filepath}...")
    logger.debug(f"df.head\n{df.head()}",f=True, off=True)
    if os.path.exists(filepath) and mode == 'a':
        logger.warning(f"{filepath} already exists. Appending to prevent overwrites...")
    df.to_csv(filepath, index=index, mode=mode)
    logger.info(f"{os.path.basename(filepath)} saved to {filepath}.")

    return df if return_df else None

