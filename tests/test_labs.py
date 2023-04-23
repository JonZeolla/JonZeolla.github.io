#!/usr/bin/env python3
"""
Tests for my labs
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from tkinter import Tk

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOG_FORMAT = json.dumps(
    {
        "timestamp": "%(asctime)s",
        "namespace": "%(name)s",
        "loglevel": "%(levelname)s",
        "message": "%(message)s",
    }
)
LOG = logging.getLogger(__name__)


def test_lab_codeblocks() -> None:
    """
    Discover all of the labs and test the codeblocks in them
    """
    cwd: Path = Path().absolute()
    labs_dir: Path = Path("build/labs/")
    labs: list[Path] = list(labs_dir.glob("**/[!index]*.html"))

    for lab in labs:
        code_blocks: list[str] = get_code_from_codeblocks(lab=lab, cwd=cwd)
        print(code_blocks)
        if os.environ.get("CI") == "true":
            run_code_blocks(code_blocks=code_blocks)


def run_code_blocks(*, code_blocks: list[str]) -> None:
    """
    Run the code in the provided codeblocks
    """
    for code in code_blocks:
        try:
            subprocess.run(
                code,
                capture_output=True,
                check=True,
                shell=True,
            )
        except subprocess.CalledProcessError as error:
            LOG.error(
                f"stdout: {error.stdout.decode('UTF-8')}, stderr: {error.stderr.decode('UTF-8')}"
            )
            sys.exit(1)


def get_code_from_codeblocks(*, cwd: Path, lab: Path) -> list[str]:
    """
    Get the code in the codeblocks
    """
    lab_file: str = f"file://{cwd}/{lab}"
    options: Options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    prefs: dict[str, int] = {"profile.default_content_setting_values.notifications": 1}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    # Needed to avoid selenium.common.exceptions.ElementNotInteractableException errors
    wait = WebDriverWait(driver, 15)
    copy_buttons = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'button[data-tooltip="Copy"]')
        )
    )
    #
    #     wait = WebDriverWait(driver, 15)
    #     copy_buttons = wait.until(
    #         EC.visibility_of_all_elements_located(
    #             (By.CSS_SELECTOR, 'button[data-tooltip="Copy"]')
    #         )
    #     )
    driver.get(lab_file)

    # Find the codeblocks that have a copy button
    copy_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-tooltip="Copy"]')

    # Click the copy buttons and add the clipboard contents to the list of codeblocks to return
    code_blocks: list[str] = []
    for button in copy_buttons:
        button.click()
        time.sleep(0.5)
        root: Tk = Tk()
        clipboard_content: str = root.clipboard_get()
        code_blocks.append(clipboard_content)

    driver.quit()

    return code_blocks
