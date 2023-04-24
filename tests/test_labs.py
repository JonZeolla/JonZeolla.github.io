#!/usr/bin/env python3
"""
Tests for my labs
"""

import logging
import sys
from pathlib import Path
from tkinter import Tk

import docker
from playwright.sync_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    sync_playwright,
)

LOG = logging.getLogger(__name__)


def test_lab_code_blocks() -> None:
    """
    Discover all of the labs and test the code blocks in them
    """
    cwd: Path = Path().absolute()
    labs_dir: Path = Path("build/labs/")
    labs: list[Path] = list(labs_dir.glob("**/[!index]*.html"))

    for lab in labs:
        lab_url: str = f"file://{cwd}/{lab}"
        all_code_blocks: list[str] = get_code_from_code_blocks(
            lab_url=lab_url,
        )
        cleanup_code_blocks: list[str] = get_cleanup_code_blocks(lab_url=lab_url)
        assert run_code_blocks(
            all_code_blocks=all_code_blocks, cleanup_code_blocks=cleanup_code_blocks
        )


def run_code_blocks(
    *, all_code_blocks: list[str], cleanup_code_blocks: list[str]
) -> bool:
    """
    Run the code in the provided code blocks
    """
    # Allow but warn on empty code blocks
    if not all_code_blocks:
        LOG.warning(
            "Passed an empty list of code blocks, allowing the build to pass, but this may not be expected"
        )
        return True

    # Setup a container to run the steps in
    client: docker.DockerClient = docker.from_env()
    docker_sock: Path = Path("/var/run/docker.sock")
    volumes: dict[Path, dict[str, str]] = {
        docker_sock: {"bind": str(docker_sock), "mode": "ro"}
    }

    container = client.containers.run(
        image="ubuntu:20.04",
        auto_remove=False,
        detach=True,
        network="workshop",
        tty=True,
        volumes=volumes,
    )

    # Run each code block in the container
    for code in all_code_blocks:
        command: str = f'/bin/bash -c """set -euo pipefail && {code}"""'
        print(command)
        exit_code, output = container.exec_run(cmd=command, tty=True)
        print(output)
        if exit_code != 0:
            LOG.error(f"Failed test when running '{command}'")
            LOG.error(output)
            for cleanup_code in cleanup_code_blocks:
                cleanup_command: str = (
                    f'/bin/bash -c """set -euo pipefail && {cleanup_code}"""'
                )
                exit_code, output = container.exec_run(cmd=cleanup_command, tty=True)
                if exit_code != 0:
                    LOG.error(f"Failed to run cleanup command '{cleanup_command}'")
                    LOG.error(output)
            container.kill()
            return False

    container.kill()
    return True


def get_code_from_code_blocks(*, lab_url: str, cleanup_only: bool = False) -> list[str]:
    """
    Get the code in the code blocks
    """
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(slow_mo=50, headless=False)
        context: BrowserContext = browser.new_context()
        page: Page = context.new_page()
        page.goto(lab_url)

        # Find all the dropdowns that are hidden and open them. If you don't do this first, the loop below for clicking
        # the copy buttons will sometimes double account for code blocks because it will expand a dropdown when it
        # thinks it's clicking a copy button, and it pulls the unchanged clipboard into the code_blocks list for a
        # second time
        toggle_divs: list[ElementHandle] = page.query_selector_all("div.toggle-hidden")

        for div in toggle_divs:
            div.click()

        if cleanup_only:
            cleanup_div: ElementHandle | None = page.query_selector(
                "div.highlight-cleanup"
            )
            if not cleanup_div:
                LOG.error(f"No cleanup block in {lab_url}")
                sys.exit(1)

            query_selector = cleanup_div.query_selector_all
        else:
            query_selector = page.query_selector_all

        copy_buttons = list[ElementHandle] = query_selector(
            'button[data-tooltip="Copy"]'
        )

        # Click the copy buttons and extract the code blocks, excluding the cleanup
        # TODO: Exclude the cleanup
        code_blocks: list[str] = []
        for button in copy_buttons:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accomodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the code_blocks list
            root: Tk = Tk()
            clipboard_content: str = root.clipboard_get()
            code_blocks.append(clipboard_content)

    return code_blocks


def get_cleanup_code_blocks(lab_url: str) -> list[str]:
    """
    Get the appropriate cleanup code blocks for the provided lab URL
    """
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(slow_mo=50, headless=False)
        context: BrowserContext = browser.new_context()
        page: Page = context.new_page()
        page.goto(lab_url)

        # Loop through each div and click it
        code_blocks: list[str] = []
        for button in cleanup_code_blocks:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accomodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the code_blocks list
            root: Tk = Tk()
            clipboard_content: str = root.clipboard_get()
            code_blocks.append(clipboard_content)
