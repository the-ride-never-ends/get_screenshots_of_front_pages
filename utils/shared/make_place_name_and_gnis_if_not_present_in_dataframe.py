import pandas as pd


from logger.logger import Logger
from .make_sha256_hash import make_sha256_hash


def make_place_name_and_gnis_if_not_present_in_dataframe(df: pd.DataFrame, logger: Logger=None) -> pd.DataFrame:
    """
    If we're not working with data from the 'locations' table, create the gnis and place_name columns.
    """
    if not logger:
        raise ValueError("Logger cannot be none.")

    if not df['place_name']:
        logger.info("'place_name' column not present. Creating from url...")
        df['place_name'] = df['url'].apply(lambda x: x.split('/')[2])

    if not df['gnis']:
        logger.info("'gnis' column not present. Creating from url and place_name...\nNOTE: url THEN place_name.")
        df['gnis'] = make_sha256_hash(df['url'], df['place_name'] )

    return df
