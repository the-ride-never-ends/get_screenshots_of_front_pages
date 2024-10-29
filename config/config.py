
import os


from .utils.config.get_config import get_config as config
from logger.logger import Logger
logger = Logger(logger_name=__name__)


# Define hard-coded constants
script_dir = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(script_dir)
DEBUG_FILEPATH: str = os.path.join(PROJECT_ROOT, "debug_logs")


# Get YAML config variables
try:
    path = "SYSTEM"
    SCREENSHOT_SEMAPHORE: int = config(path, 'SCREENSHOT_SEMAPHORE') or 10
    CHECK_IF_URL_IS_UP_SEMAPHORE: int = config(path, 'CHECK_IF_URL_IS_UP_SEMAPHORE') or 5


    path = "PLAYWRIGHT"
    HEADLESS: bool = config(path, 'HEADLESS') or True
    SLOW_MO: int = config(path, 'SLOW_MO') or 0


    path = "PRIVATE_FOLDER_PATHS"
    OUTPUT_FOLDER: str = config(path, 'OUTPUT_FOLDER') or os.path.join(PROJECT_ROOT, "output")
    INPUT_FOLDER: str = config(path, 'INPUT_FOLDER') or os.path.join(PROJECT_ROOT, "input")

    # Create output subfolders if they don't exist.
    SCREENSHOT_FOLDER = os.path.join(OUTPUT_FOLDER, "screenshots")
    CSV_OUTPUT_FOLDER = os.path.join(OUTPUT_FOLDER, "csv")
    ouput_folder_list = [SCREENSHOT_FOLDER, CSV_OUTPUT_FOLDER]
    for folder in ouput_folder_list:
        if not os.path.exists(folder):
            print(f"Creating output subfolder '{folder}'...")
            os.mkdir(folder)
            logger.info(f"{folder} created.")

    logger.info("YAML configs loaded.")

except KeyError as e:
    logger.exception(f"Missing configuration item: {e}")

except Exception as e:
    logger.exception(f"Could not load configs: {e}")
    raise e

