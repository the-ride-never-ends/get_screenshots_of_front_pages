import asyncio
from typing import NamedTuple


import aiohttp
import pandas as pd


from utils.shared.raise_value_error_if_absent import raise_value_error_if_absent
from logger.logger import Logger
logger = Logger(logger_name=__name__)


async def check_if_url_is_up(idx, # Dummy argument for enumerate.
                            row: NamedTuple,
                            timeout: int = 10,
                            good_response_list: list=None,
                            bad_response_list: list=None,
                            ) -> dict:
    """
    Asynchronously checks if a URL is up and records the response status.
    NOTE This function doesn't raise exceptions for HTTP errors, but logs them instead.

    Args:
        row (NamedTuple): A Pandas named tuple containing url, gnis, and place_name.
        timeout (int, optional): The timeout for the HTTP request in seconds. Defaults to 10.
        good_response_list (list, optional): A list to store successful responses.
        bad_response_list (list, optional): A list to store failed responses.

    Returns:
        dict: A dictionary containing the response status and other information.

    Raises:
        ValueError: If either good_response_list or bad_response_list is not provided.

    """
    raise_value_error_if_absent(good_response_list, bad_response_list)
    # Intialize row.url alias.
    url = row.url
    logger.info(f"Processing row {idx} with URL '{url}'...")
    logger.debug(f"row: {row}")
    mes = None
    filter_out = True

    # Initialize the output dictionary
    output_dict = {
        'gnis': row.gnis,
        'url': url,
        'place_name': row.place_name,
        'response_status': None,
        'filter_out': filter_out,  # Default to filtered out unless we confirm it's good
        'error': 'NA'
    }

    try:
        # Get the status code from the URL.
        timeout_client = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_client) as session:
            async with session.get(url) as response:
                output_dict['response_status'] = response.status

                if response.status == 200:
                    output_dict['filter_out'] = filter_out = False
                    logger.info(f"{url} is up.")
                else:
                    logger.warning(f"{url} is down: {response.status}")
                    output_dict['filter_out'] = filter_out = True
                    print("Recording then skipping...")

    # NOTE We don't raise these, since we want the 404s or any other errors to be recorded.
    except aiohttp.ClientError as e:
        mes = f"ClientError for {url}: {e}"
    except asyncio.TimeoutError:
        mes = f"TimeoutError for {url}: {e}"
    except Exception as e:
        mes = f"Unknown Error for {url}: {e}"
    finally:
        if mes:
            logger.error(mes)
            output_dict['filter_out'] = filter_out = True
            output_dict['error'] = mes

    # Route the dictionary to the appropriate list.
    if filter_out:
        logger.debug(f"Adding row {idx} with URL '{url}' to bad_response_list")
        bad_response_list.append(output_dict)
    else:
        logger.debug(f"Adding row {idx} with URL '{url}' to good_response_list")
        good_response_list.append(output_dict)
    return
