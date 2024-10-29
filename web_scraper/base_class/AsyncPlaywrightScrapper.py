from abc import ABC, abstractmethod
import asyncio
from functools import wraps
import os
from typing import Any, Coroutine
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlsplit


import aiohttp
import pandas as pd
# These are imported primarilty for typehinting.
from playwright.async_api import (
    PlaywrightContextManager as AsyncPlaywrightContextManager,
    BrowserContext as AsyncPlaywrightBroswerContext,
    Playwright as AsyncPlaywright,
    Page as AsyncPlaywrightPage,
    Browser as AsyncPlaywrightBrowser,
    Error as AsyncPlaywrightError,
    TimeoutError as AsyncPlaywrightTimeoutError,
)


from utils.shared.safe_format import safe_format
from utils.shared.sanitize_filename import sanitize_filename
from utils.shared.decorators.try_except import try_except, async_try_except
from utils.shared.make_id import make_id

from config.config import OUTPUT_FOLDER, PROJECT_ROOT
from logger.logger import Logger
logger = Logger(logger_name=__name__)


class AsyncPlaywrightScrapper:
    """
    A Playwright browser class.

    Parameters:
        domain (str): The domain to scrape.
        pw_instance (AsyncPlaywrightContextManager): The Playwright instance to use.
        user_agent (str, optional): The user agent string to use. Defaults to "*".
        **launch_kwargs: Additional keyword arguments to pass to the browser launch method.

    Notes:
        launch_kwargs (dict): Browser launch arguments.
        pw_instance (AsyncPlaywrightContextManager): The Playwright instance.
        domain (str): The domain being scraped.
        user_agent (str): The user agent string.
        sanitized_filename (str): A sanitized version of the domain for use in filenames.
        rp (RobotFileParser): The parsed robots.txt file for the domain.
        request_rate (float): The request rate specified in robots.txt.
        crawl_delay (int): The crawl delay specified in robots.txt.
        browser (AsyncPlaywrightBrowser): The Playwright browser instance (initialized as None).
        context (AsyncPlaywrightBroswerContext): The browser context (initialized as None).
        page (AsyncPlaywrightPage): The current page (initialized as None).
    """

    def __init__(self,
                 domain: str,
                 pw_instance: AsyncPlaywrightContextManager,
                 user_agent: str="*",
                 **launch_kwargs):

        self.launch_kwargs = launch_kwargs
        self.pw_instance: AsyncPlaywrightContextManager = pw_instance
        self.domain: str = domain
        self.user_agent: str = user_agent
        self.sanitized_filename = sanitize_filename(self.domain)
        self.output_dir = os.path.join(OUTPUT_FOLDER, self.sanitized_filename)

        # Create the output directory if it doesn't exist.
        if not os.path.exists(self.output_dir):
            os.mkdir(os.path.dirname(self.output_dir))

        # Get the robots.txt properties and assign them.
        self.rp: RobotFileParser = None
        self.request_rate: float = None
        self.crawl_delay: int = None

        self.browser: AsyncPlaywrightBrowser = None
        self.context: AsyncPlaywrightBroswerContext = None,
        self.page: AsyncPlaywrightPage = None
        self.screenshot_path = None

    # Define class enter and exit methods.

    async def _get_robot_rules(self) -> None:
        """
        Get the site's robots.txt file and read it asynchronously with a timeout.
        TODO Make a database of robots.txt files. This might be a good idea for scraping.
        """
        robots_url = urljoin(self.domain, 'robots.txt')

        # Check if we already got the robots.txt file for this website
        domain_name = self.domain.split('//')[1].split('/')[0].split('.')[0] # TODO Make this robust.
        robots_txt_filepath = os.path.join(PROJECT_ROOT, "scraper", "sites", domain_name, f"{domain_name}_robots.txt")
        e_tuple: tuple = None

        self.rp = RobotFileParser(robots_url)

        # If we already got the robots.txt file, load it in.
        if os.path.exists(robots_txt_filepath):
            logger.info(f"Using cached robots.txt file for '{self.domain}'...")
            with open(robots_txt_filepath, 'r') as f:
                content = f.read()
                self.rp.parse(content.splitlines())
    
        else: # Get the robots.txt file from the server if we don't have it.
            async with aiohttp.ClientSession() as session:
                try:
                    logger.info(f"Getting robots.txt from '{robots_url}'...")
                    async with session.get(robots_url, timeout=10) as response:  # 10 seconds timeout
                        if response.status == 200:
                            logger.info("robots.txt response ok")
                            content = await response.text()
                            self.rp.parse(content.splitlines())
                        else:
                            logger.warning(f"Failed to fetch robots.txt: HTTP {response.status}")
                            return None
                except asyncio.TimeoutError as e:
                    e_tuple = (e.__qualname__, e)
                except aiohttp.ClientError as e:
                    e_tuple = (e.__qualname__, e)
                finally:
                    if e_tuple:
                        mes = f"{e_tuple[0]} while fetching robots.txt from '{robots_url}': {e_tuple[1]}"
                        logger.warning(mes)
                        return None
                    else:
                        logger.info(f"Got robots.txt for {self.domain}")
                        logger.debug(f"content:\n{content}",f=True)

            # Save the robots.txt file to disk.
            if not os.path.exists(robots_txt_filepath):
                with open(robots_txt_filepath, 'w') as f:
                    f.write(content)

        # Set the request rate and crawl delay from the robots.txt file.
        self.request_rate: float = self.rp.request_rate(self.user_agent) or 0
        logger.info(f"request_rate set to {self.request_rate}")
        self.crawl_delay: int = int(self.rp.crawl_delay(self.user_agent))
        logger.info(f"crawl_delay set to {self.crawl_delay}")

        return

    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def _load_browser(self) -> None:
        """
        Launch a chromium browser instance.
        """
        logger.debug("Launching Playwright Chromium instance...")
        self.browser = await self.pw_instance.chromium.launch(**self.launch_kwargs)
        logger.debug(f"Playwright Chromium brwoser instance launched successfully.\nkwargs:{self.launch_kwargs}",f=True)
        return


    # Define the context manager methods
    @classmethod
    async def start(cls, domain, pw_instance, *args, **kwargs) -> 'AsyncPlaywrightScrapper':
        """
        Factory method to start the scraper.
        """
        logger.debug("Starting AsyncPlaywrightScrapper via factory method...")
        instance = cls(domain, pw_instance, *args, **kwargs)
        await instance._get_robot_rules()
        await instance._load_browser()
        return instance


    @try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def exit(self) -> None:
        """
        Close any remaining page, context, and browser instances before exit.
        """
        self.close_current_page_and_context()
        if self.browser:
            await self.close_browser()
        return


    async def __aenter__(self) -> 'AsyncPlaywrightScrapper':
        await self._get_robot_rules()
        return await self._load_browser()


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return await self.exit()


    # NOTE We make these individual function's so that we can orchestrate them more granularly
    # in within larger functions within the class. 
    async def open_new_context(self, **kwargs) -> AsyncPlaywrightBroswerContext:
        """
        Open a new browser context.
        """
        if self.browser:
            self.context = await self.browser.new_context(**kwargs)
            logger.debug("Browser context created successfully.")
            return
        else:
            raise AttributeError("'browser' attribute is missing or not initialized.")


    async def close_browser(self) -> None:
        """
        Close a browser instance.
        """
        if self.browser:
            await self.browser.close()
            logger.debug("Browser closed successfully.")
            return


    async def open_new_page(self, **kwargs: dict) -> AsyncPlaywrightPage:
        """
        Create a new brower page instance.
        """
        if self.context:
            if self.page:
                logger.info("self.page already assigned. Overwriting...")
                # raise AttributeError("'page' attribute is already initialized.")
            self.page = await self.context.new_page(**kwargs)
            logger.debug("Page instance created successfully.")
            return
        else:
            raise AttributeError("'context' attribute is missing or not initialized.")


    async def close_context(self) -> None:
        """
        Close a browser context.
        """
        await self.context.close()
        logger.debug("Browser context closed successfully.")
        return


    async def close_page(self) -> None:
        """
        Close a browser page instance.
        """
        await self.page.close()
        logger.debug("Page instance closed successfully")
        return


    async def close_current_page_and_context(self) -> None:
        if self.page:
            await self.close_page()
        if self.context:
            await self.close_context()
        return

    @try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def wait_till_idle(self) -> Coroutine[Any, Any, None]:
        """
        Wait for a page to fully finish loading.
        """
        return await self.page.wait_for_load_state("networkidle")

    # Orchestrated functions.
    # These function's put all the small bits together.

    # NOTE THIS FUNCTION WORKS
    @try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError])
    async def navigate_to(self, url: str, idx: int=None, **kwargs) -> Coroutine:
        """
        Open a specified webpage and wait for any dynamic elements to load.
        This method respects robots.txt rules (e.g. not scrape disallowed URLs, respects crawl delays).
        A new browser context and page are created for each navigation to ensure a clean state.

        Args:
            url (str): The URL of the webpage to navigate to.
            **kwargs: Additional keyword arguments to pass to the page.goto() method.

        Returns:
            Coroutine: A coroutine that resolves when the page has finished loading.

        Raises:
            AsyncPlaywrightTimeoutError: If the page fails to load within the specified timeout.
            AsyncPlaywrightError: If any other Playwright-related error occurs during navigation.
        """
        # See if we're allowed to get the URL, as well as get the specified delay from robots.txt
        if not self.rp.can_fetch(self.user_agent, url):
            logger.warning(f"Cannot scrape URL '{url}' as it's disallowed in robots.txt")
            return

        # Wait per the robots.txt crawl delay.
        if self.crawl_delay > 0:
            if idx > 1:
                logger.info(f"Sleeping for {self.crawl_delay} seconds to respect robots.txt crawl delay")
                await asyncio.sleep(self.crawl_delay)

        # Open a new context and page.
        await self.open_new_context()
        await self.open_new_page()

        # Go to the URL and wait for it to fully load.
        await self.page.goto(url, **kwargs)
        return await self.wait_till_idle()


    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def move_mouse_cursor_to_hover_over(self, selector: str, *args, **kwargs) -> Coroutine[Any, Any, None]:
        """
        Move a "mouse" cursor over a specified element.
        """
        return await self.page.locator(selector, *args, **kwargs).hover()


    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def click_on(self, selector: str, *args, **kwargs) -> Coroutine[Any, Any, None]:
        """
        Click on a specified element.
        """
        return await self.page.locator(selector, *args, **kwargs).click()


    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError])
    async def save_page_html_content_to_output_dir(self, filename: str) -> str:
        """
        Save a page's current HTML content to the output directory.
        """
        path = os.path.join(self.output_dir, filename)
        page_html = await self.page.content()
        with open(path, "w", encoding="utf-8") as file:
            file.write(page_html)
            logger.debug(f"HTML content has been saved to '{filename}'")


    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError])
    async def take_screenshot(self,
                              filename: str,
                              full_page: bool=False,
                              prefix: str=None,
                              element: str=None,
                              open_image_after_save: bool=False,
                              locator_kwargs: dict=None,
                              **kwargs) -> Coroutine[Any, Any, None]:
        """
        Take a screenshot of the current page or a specific element.

        The filename will be automatically corrected to .jpg if an unsupported image type is provided.\n
        The screenshot will be saved in a subdirectory of OUTPUT_FOLDER, named after the sanitized domain.\n
        If the specified directory doesn't exist, it will be created.\n
        NOTE: Opening the image after saving only works in Windows Subsystem for Linux (WSL).
        TODO Fix open_image_after_save. It's busted, even for linux.

        Args:
            filename (str): The name of the file to save the screenshot as.
            full_page (bool, optional): Whether to capture the full page or just the visible area. Defaults to False.
            element (str, optional): CSS selector of a specific element to capture. If None, captures the entire page. Defaults to None.
            open_image_after_save (bool, optional): Whether to open the image after saving (only works in WSL). Defaults to False. Currently broken.
            locator_kwargs (dict, optional): Additional keyword arguments for the locator if an element is specified.
            **kwargs: Additional keyword arguments to pass to the screenshot method.

        Returns:
            Coroutine[Any, Any, None]: A coroutine that performs the screenshot operation.

        Raises:
            AsyncPlaywrightTimeoutError: If the specified element cannot be found within the default timeout.
            AsyncPlaywrightError: Any unknown Playwright error occurs.
        """
        # Coerce the filename to jpg if it's an unsupported image type.
        # NOTE This will also work with URLs, since it feeds the filename into the santize_filename function.
        if not filename.lower().endswith(('.png', '.jpeg')):
            logger.debug(f"filename argument: {filename}")

            if filename.lower().startswith(('http://', 'https://')):
                logger.warning(f"'take_screenshot' method was given a URL as a filename. Coercing to valid filename...")
                # Extract the filename from the URL
                filename = f"{urlsplit(filename).path.split('/')[-1]}.jpeg"
            else:
                logger.warning(f"'take_screenshot' method was given an invalid picture type. Coercing to jpeg...")
                #Split off the extension and add .jpg
                filename = f"{os.path.splitext(filename)[0]}.jpeg"
            
        if prefix:
            filename = f"{prefix}_{filename}"
            logger.info(f"Filename prefix '{prefix}' added to '{filename}'")

        logger.debug(f"filename: {filename}")
        self.screenshot_path = self._make_filepath_dir_for_domain(filename)

        # Take the screenshot.
        if element:
            await self.page.locator(element, **locator_kwargs).screenshot(path=self.screenshot_path, type="jpeg", full_page=full_page, **kwargs)
        else:
            await self.page.screenshot(path=self.screenshot_path, type="jpeg", full_page=full_page, **kwargs)

        # Open the image using IrfanView 64 after it's saved if requested.
        # NOTE this will only work for WSL, since IrfanView 64 is a Windows-only application.
        # TODO This doesn't work! Fix it eventually!
        # if open_image_after_save: # Normal usage: i_view64.exe image.png
        #     subprocess.call(["'/mnt/c/Program Files/IrfanView/i_view64.exe' ", filepath], shell=True)
        return


    def _make_filepath_dir_for_domain(self, filename: str=None) -> str:
        """
        Define and return a filepath for a given domain in the output folder.
        If the directory doesn't exist, make it.
        """
        assert self.output_dir and self.domain, "OUTPUT_FOLDER and self.domain must be defined."
        # If we aren't given a filename, just sanitize the domain with a UUID at the end.
        filename = filename or sanitize_filename(self.domain, make_id())

        # Define the filepath.
        filepath = os.path.join(self.output_dir, filename)

        # Create the output folder if it doesn't exist.
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        return filepath


    @async_try_except(exception=[AsyncPlaywrightTimeoutError, AsyncPlaywrightError], raise_exception=True)
    async def evaluate_js(self, javascript: str, js_kwargs: dict) -> Coroutine:
        """
        Evaluate JavaScript code in a Playwright Page instance.

        Example:
        >>> # Note the {} formating in the javascript string.
        >>> javascript = '() => document.querySelector({button})')'
        >>> js_kwargs = {"button": "span.text-xs.text-muted"}
        >>> search_results = await evaluate_js(javascript, js_kwargs=js_kwargs)
        >>> for result in search_results:
        >>>     logger.debug(f"Link: {result['href']}, Text: {result['text']}")
        """
        formatted_javascript = safe_format(javascript, **js_kwargs)
        return await self.page.evaluate(formatted_javascript)


    def trace_async_playwright_debug(self, context: AsyncPlaywrightBroswerContext):
        """
        Decorator to start a trace for a given context and page.
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                self.open_new_context()
                await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
                await self.context.tracing.start_chunk()
                await self.open_new_page()
                try:
                    result = await func(*args, **kwargs)
                finally:
                    await context.tracing.stop_chunk(path=os.path.join(OUTPUT_FOLDER, sanitize_filename(self.page.url) ,f"{func.__name__}_trace.zip"))
                    await context.close()
                    return result
            return wrapper
        return decorator
