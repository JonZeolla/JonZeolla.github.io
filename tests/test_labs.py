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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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
    with open(lab_file) as file:
        options: Options = Options()
        options.headless = False  # TODO
        driver = webdriver.Chrome(options=options)
        driver.get(lab_file)

        # Find the codeblocks that have a copy button
        copy_buttons = driver.find_elements(
            By.CSS_SELECTOR, 'button[data-tooltip="Copy"]'
        )

        # Click the copy buttons and add the clipboard contents to the list of codeblocks to return
        code_blocks: list[str] = []
        for button in copy_buttons:
            button.click()
            time.sleep(0.5)
            clipboard_content = driver.execute_script(
                "return navigator.clipboard.readText();"
            )
            code_blocks.append(clipboard_content)
        #             attribute: str = button.get_attribute("data-clipboard-target")
        #             target = driver.find_element(By.CSS_SELECTOR, attribute)

        # discovered_codeblocks[lab] =
        # element = driver.find_element_by_xpath('//a[@href="/documentation/webdriver/"]')
        # element.click() # HTML click method; Does this work?  If not, use the next one which is the js click
        # driver.execute_script("arguments[0].click();", element)
        #         code = target  # TODO

        # TODO: to discovered_codeblocks, then run the copy button magic, add that
        # output to runner list, then iterate through all those commands in order and ensure success

        driver.quit()

    return code_blocks
