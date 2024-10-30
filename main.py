
import asyncio
import os
import sys


import pandas as pd
from playwright.async_api import (
    async_playwright
)


from web_scraper.child_classes.generic.GetScreenshotsOfFrontPages import get_screenshot_of_front_page_class_wrapper
from web_scraper.child_classes.generic.generic_utils.check_if_url_is_up import check_if_url_is_up

from utils.shared.limiter_utils.Limiter import Limiter
from utils.shared.next_step import next_step
from utils.shared.save_list_of_dicts_to_csv_via_pandas import save_list_of_dicts_to_csv_via_pandas
from utils.shared.load_csv_as_pandas_dataframe import load_csv_as_pandas_dataframe
from utils.shared.make_place_name_and_gnis_if_not_present_in_dataframe import make_place_name_and_gnis_if_not_present_in_dataframe

from config.config import INPUT_FOLDER, CSV_OUTPUT_FOLDER, SCREENSHOT_SEMAPHORE, CHECK_IF_URL_IS_UP_SEMAPHORE
from logger.logger import Logger
logger = Logger(logger_name=__name__)


async def main() -> None:
    """
    Problem Definition: Get screenshots of front pages
    Input: A CSV of front page URLs and associated metadata.
    Output: A folder of frontpage screenshots, along with 4 CSV records:
        - A CSV of front page URLs with screenshot paths.
        - A CSV of front page URLS that failed to produce a screenshot.
        - A CSV of front page URLS that produced a 200 response.
        - A CSV of front page URLs that failed to produce a 200 response.
    """
    # Define CSV file names, then construct their paths.
    next_step("Step 1. Define CSV names and their paths.")
    filenames = [
        'input_urls',
        'output_urls',
        'good_response_urls',
        'bad_response_urls',
        'screenshot_failed_urls',
    ]
    path_dict ={}
    for name in filenames:
        folderpath = INPUT_FOLDER if name == "input_urls" else CSV_OUTPUT_FOLDER
        path_dict[name] = os.path.join(folderpath, name + ".csv")
        logger.debug(f"{name}.csv path: {path_dict[name]}")


    next_step("Step 2. Load front page URLs from the CSV.")
    input_urls_df = load_csv_as_pandas_dataframe(path_dict['input_urls'])
    input_urls_df = make_place_name_and_gnis_if_not_present_in_dataframe(input_urls_df, logger=logger)


    next_step("Step 3. Filter out front pages where we already got screenshots")
    # Load in the output URLs if the exist.
    if os.path.exists(path_dict['output_urls']):
        output_urls_df = load_csv_as_pandas_dataframe(path_dict['output_urls'])

        # Filter the input URLs that are in the output URLs.
            # NOTE: The CSV has a column called "url" that contains the URLs, 
            # and 'gnis', a unique ID variable from the MySQL database.
        input_urls_df = input_urls_df[~input_urls_df['gnis'].isin(output_urls_df['gnis'])]

    else:
        logger.info("output_urls_df not found. Skipping...")
    assert len(input_urls_df.index) != 0, "No URLs to process."
    logger.debug(f"Step 3: input_urls_df.head()\n{input_urls_df.head()}",f=True)


    next_step("Step 4. Filter out front pages that gave bad responses.")
    # Load the bad responses from the CSV.
    if os.path.exists(path_dict['output_urls']):
        bad_response_urls_df = load_csv_as_pandas_dataframe(path_dict['bad_response_urls'])

        input_urls_df = input_urls_df[~input_urls_df['gnis'].isin(bad_response_urls_df['gnis'])]
    else:
        logger.info("bad_response_urls_df not found. Skipping...")
    logger.debug(f"Step 4: input_urls_df.head()\n{input_urls_df.head()}",f=True)


    next_step("Step 5. Check if the URLs are up. If they aren't, note that and filter them out.", stop=True)
    # Instantiate limiter class
    limiter = Limiter(semaphore=CHECK_IF_URL_IS_UP_SEMAPHORE, progress_bar=True, )
    good_response_list = [] # NOTE Apprently good_response_list = bad_response_list = [] makes them the same object, rather than the same type of object.
    bad_response_list = []

    # Check if the URLs are up and separate them.
    await limiter.run_async_many(
        inputs=input_urls_df, 
        func=check_if_url_is_up,
        good_response_list=good_response_list,
        bad_response_list=bad_response_list,
    ) # -> list[dict], list[dict]

    # Save the good and bad response lists to CSVs.
    # Good responses are the URLs that return 200 and will go on to processing.
    # Bad responses are URLs that return anything else, and will be saved to a CSV for manual review.
    good_urls_df = save_list_of_dicts_to_csv_via_pandas(good_response_list, 
                                                        path_dict['good_response_urls'],
                                                        logger=logger,
                                                        return_df=True,)
    save_list_of_dicts_to_csv_via_pandas(bad_response_list, path_dict['bad_response_urls'], logger=logger)


    next_step("Step 6. Take screenshots of the the URLs and save them as jpegs to the output folder.", stop=True)
    success_list = []
    failure_list = []
    async with async_playwright() as pw_instance:

        # Instantiate the limiter class
        limiter = Limiter(semaphore=SCREENSHOT_SEMAPHORE, progress_bar=True)

        # Take screenshots of all the URLs
        await limiter.run_async_many(
            inputs=good_urls_df, 
            func=get_screenshot_of_front_page_class_wrapper,
            pw_instance=pw_instance,
            success_list=success_list,
            failure_list=failure_list
        ) # -> list[dict], list[dict]


    next_step("Step 7. Save the processed URLs to CSV files in the output folder.", stop=True)
    save_list_of_dicts_to_csv_via_pandas(success_list, path_dict['output_urls'], logger=logger)
    save_list_of_dicts_to_csv_via_pandas(failure_list, path_dict['screenshot_failed_urls'], logger=logger)


    logger.info("Program executed successfully. Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    import os
    base_name = os.path.basename(__file__) 
    # If the name of this file is main.py, assume that the program name is its directory name.
    # Else, assume the program's name is the same as the file's name.
    program_name = os.path.split(os.path.split(__file__)[0])[1] if base_name != "__main__.py" else os.path.splitext(base_name)[0] 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"'{program_name}' program stopped.")

