
import pandas as pd

from .load_from_csv import load_from_csv

def load_csv_as_pandas_dataframe(path_dict: dict[str]) -> pd.DataFrame:
    """
    Load CSV file and return as a pandas DataFrame.

    Args:
        path_dict (dict[str]): Dictionary containing the CSV file path.

    Returns:
        pd.DataFrame: DataFrame containing the loaded CSV data.
    """
    return pd.DataFrame().from_dict(load_from_csv(path_dict))
