#!/usr/bin/env python3
"""
Tests for my labs
"""

import os
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def test_codeblocks() -> None:
    """
    Ensure all the the code in the codeblocks are runnable, in order
    """
    cwd: str = str(Path().absolute())
    labs_dir: Path = Path("build/labs/")
    labs: list[Path] = list(labs_dir.glob("**/[!index]*.html"))
    discovered_codeblocks: dict[Path, list[str]] = {}

    for lab in labs:
        discovered_codeblocks[lab] = []
        with open(lab) as file:
            options = Options()
            options.headless = False  # TODO
            driver = webdriver.Chrome(options=options)
            lab_file: str = f"file://{cwd}/{lab}"

            if os.environ.get("CI") != "true":
                sys.exit(0)

            # TODO: extract the code blocks, add to discovered_codeblocks, then run the copy button magic, add that
            # output to runner list, then iterate through all those commands in order and ensure success
            assert False
