
# Program: get_screenshots_of_front_pages

1. Problem definition - TODO
2. High-level architecture - TODO
3. Data structures - TODO
4. Algorithms - TODO
5. Function/method signatures - TODO
6. Error handling - TODO
7. Testing strategy - TODO
8. Code organization - TODO
9. Naming conventions - TODO
10. External dependencies - TODO
11. Performance considerations - TODO
12. Scalability - TODO
13. Security considerations - TODO
14. Documentation needs - TODO


# 1. Problem Definition

- Objective: Get screenshots of front pages from a list of URLs.
- Languages: Python, 
- Inputs: 
   - A CSV of front page URLs and associated metadata.
- Input validation:
   - Ensure
Outputs: A folder of frontpage screenshots in jpeg format, along with 3 CSV records:
   - A CSV of front page URLs with screenshot paths.
   - A CSV of front page URLS that failed to produce a screenshot.
   - A CSV of front page URLs that failed to produce a 200 response.

## Constraints:

## Scope:

## Data Integrity and Verification:

## Scalability Plans

## Update Process:

## Use cases:

# 2. High-Level Architecture

1. **Error Handling and Logging System 'logger.py'**
   - Centralized error handling for all modules
   - Comprehensive logging for debugging and auditing
   - **COMPLETE**



# 3. Data Structures
## 1. In-Memory Data Structures:
   - Pandas DataFrames:
      - Primary structure for moving and manipulating data.
   - Python base types
      - Sets, Queues, Dictionaries, etc.
## 2. Database Structures
   - Input/out variables are defined here.
   - See Datbase Schema in SQLSCHEMA.md
## 3. File Structures
   - YAML config files, "config.yaml" and "private_config.yaml"
   - Log files: Structured plaintext files, with option to output JSON.
   - Screenshots: JPEG screenshots to validate web scraping.


# 4. Algorithms

# 5. Function/method signatures
   - Detailed documentation on functions and method signatures is provided within the source code and will be omitted here for brevity.
   - Sphinx documentation will be generated for the project on final release.

# 6. Error handling
   - Error handling will be handled by Python's built in exception handling mechanisms (try-except blocks, raising, checksums, etc.)
   - Detailed implementation is on a per-function basis and will be omitted here for brevity.

# 7. Testing strategy
   - Linear pipeline, where each module is tested sequentially before integration.
   - Progress is "saved" via uploading output data to the database or outputting to a file (CSV, screenshot, etc.).
   - 100% code coverage will be achieved through unit testing using the pytest library and running the program seqentially through each module.

# 8. Code organization
   - The project is organized based on the modules in 'High-Level Architecture'.
   - Each module has a main class and its own utility functions in the 'utils' directory.
   - Manual subprocesses that only have to be run once have their own directory 'manual'.

# 9. Naming conventions
   1. Python conforms to PEP8 naming conventions.
      - Variables and functions are named use lowercase with underscores.
      - Classes use CamelCase.
      - Constants and global variables use ALL_CAPS.
      - Private variables and methods are named using a single underscore prefix.
      - 3rd party libraries are imported using staandard naming conventions (e.g. import pandas as pd).
      - Utility file namings follow the same conventions as their primary function or class (e.g. AsyncPlaywrightScraper class is in AsyncPlaywrightScraper.py)
      - Critical orchestration files are one word, undercase (e.g. database.py)
      - **TODO: Standardization of formats**
   2. MySQL follows standard SQL naming conventions.
      - Tables and input and output variables are named using lowercase with underscores.
      - Commands are written in ALL CAPS.


# 10. External dependencies
   - This project makes extensive use of Pandas and Playwright.
   - See requirements.txt for all 3rd party libraries.
   - NOTE: Not all libraries are currently used, and will be culled on final release.


11. Performance considerations - TODO
12. Scalability - TODO
13. Security considerations - TODO
14. Documentation needs - TODO