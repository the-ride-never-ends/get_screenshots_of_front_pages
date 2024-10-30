from typing import NamedTuple


import pandas as pd
from playwright.async_api import (
    PlaywrightContextManager as AsyncPlaywrightContextManager,
)


from web_scraper.base_class.AsyncPlaywrightScraper import AsyncPlaywrightScraper
from utils.shared.sanitize_filename import sanitize_filename
from utils.shared.raise_value_error_if_absent import raise_value_error_if_absent

from config.config import SCREENSHOT_FOLDER
from logger.logger import Logger
logger = Logger(logger_name=__name__)


async def get_screenshot_of_front_page_class_wrapper(row, 
                                pw_instance: AsyncPlaywrightContextManager=None, 
                                success_list: list=None, 
                                failure_list: list=None
                                ) -> None:
    """
    This is essentially a limiter-friendly context manager for the GetFrontPages class.
    """
    raise_value_error_if_absent(pw_instance, success_list, failure_list)

    scraper: GetScreenshotsOfFrontPages = await GetScreenshotsOfFrontPages(row.url, pw_instance).start(row.url, pw_instance)
    await scraper.get_screenshot_of_front_page(row, success_list, failure_list)
    await scraper.exit()
    return


class GetScreenshotsOfFrontPages(AsyncPlaywrightScraper):
    def __init__(self,
                domain: str,
                pw_instance: AsyncPlaywrightContextManager,
                *args,
                user_agent: str="*",
                **kwargs):
        super().__init__(domain, pw_instance, *args, user_agent=user_agent, **kwargs)
        self.output_dir = SCREENSHOT_FOLDER

    async def get_screenshot_of_front_page(self, 
                                           row: NamedTuple, 
                                           success_list: list=None, 
                                           failure_list: list=None,
                                           ) -> None:
        """
        Take a screenshot of a domain's front page and save it to the screenshot output folder.
        If successful, append the metadata to the success list. Else, append it to the failure list.

        Args:
            row (NamedTuple): A named tuple containing information about the domain.
            success_list (list, optional): A list to store metadata on successful screenshot attempts.
            failure_list (list, optional): A list to store metadata on failed screenshot attempts.

        Returns:
            success_list and failure_list are updated in-place as lists of dictionaries of screenshot metadata.
        """

        raise_value_error_if_absent(success_list, failure_list)

        # Define the screenshot filename.
        prefix = "front_page_"
        screenshot_postfix = sanitize_filename(f"{row.place_name}_{row.gnis}") + ".jpeg"

        output_dict = {
            "gnis": row.gnis,
            "url": row.url,
            "place_name": row.place_name,
            "screenshot_path": None,
        }

        try:
            # Open the page.
            # NOTE This function automatically opens up a new page and context
            logger.info(f"Going to {row.url}...")
            await self.navigate_to(row.url)

            # Take a screenshot of the page and save it.
            await self.take_screenshot(
                filename=screenshot_postfix,
                prefix=prefix,
            )

            # If we're successful, save to success_list
            logger.info(f"Screenshot successful. Saved to {self.screenshot_path}")
            output_dict['screenshot_path'] = self.screenshot_path
            success_list.append(output_dict)

        except:
            # If we're not successful, save it to failure_list.
            # NOTE: Error try-except loops for Playwright Classes are always implemented at the lowest function level
            # via the try_except or async_try_except decorators, unless otherwise specified.
            logger.error("Could not take screenshot. Appending to failure_list...")
            failure_list.append(output_dict)

        finally:
            # Close the page and context
            await self.close_current_page_and_context()
            return

