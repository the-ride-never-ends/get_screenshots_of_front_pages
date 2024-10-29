import asyncio
from typing import NamedTuple


import aiohttp
import pandas as pd


from utils.shared.raise_value_error_if_absent import raise_value_error_if_absent
from logger.logger import Logger
logger = Logger(logger_name=__name__)


async def check_if_url_is_up(row: NamedTuple,
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

    # Initialize the output dictionary
    output_dict = {
        'gnis': row.gnis,
        'url': url,
        'place_name': row.place_name,
        'response_status': None,
        'filter_out': True,  # Default to filtered out unless we confirm it's good
        'error': 'NA'
    }

    try:
        # Get the status code from the URL.
        timeout_client = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(url, timeout=timeout_client) as session:
            async with session.get() as response:
                output_dict['response_status'] = response.status

                if response.status == 200:
                    output_dict['filter_out'] = False
                    print(f"{url} is up.")
                else:
                    logger.warning(f"{url} is down: {response.status}")
                    print("Recording then skipping...")

    # NOTE We don't raise these, since we want the 404s or any other errors to be recorded.
    except aiohttp.ClientError as e:
        mes = f"{e.__qualname__} for {url}: {e}"
    except asyncio.TimeoutError:
        mes = f"{e.__qualname__} for {url}"
    except Exception as e:
        mes = f"{e.__qualname__} for {url}: {e}"
    finally:
        if mes:
            logger.error(mes)
            output_dict['error'] = mes

    # Route the dictionary to the appropriate list.
    if output_dict['filter_out']:
        bad_response_list.append(output_dict)
    else:
        good_response_list.append(output_dict)
    return
