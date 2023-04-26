#!/usr/bin/env python3
"""
Tests for my labs
"""

import logging
import re
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
LOG.setLevel('NOTSET')

std_err= logging.StreamHandler(sys.stderr)
std_err.setLevel('ERROR')

std_out = logging.StreamHandler(sys.stdout)
std_out.setLevel('DEBUG')
std_out.addFilter(lambda x : x.levelno < logging.ERROR)

LOG.addHandler(std_err)
LOG.addHandler(std_out)


def test_lab_code_blocks() -> None:
    """
    Discover all of the labs and test the code blocks in them
    """
    cwd: Path = Path().absolute()
    labs_dir: Path = Path("build/labs/")
    labs: list[Path] = list(labs_dir.glob("**/[!index]*.html"))
    tk: Tk = Tk()
    # Hold the original clipboard contents to reinstate later
    original_clipboard_content: str = tk.clipboard_get()

    for lab in labs:
        success: bool = False
        lab_url: str = f"file://{cwd}/{lab}"
        LOG.debug(f"Getting the code blocks for lab {lab} from {lab_url}...")
        all_code_blocks, cleanup_code_blocks = get_code_from_code_blocks(
            lab_url=lab_url,
            tk=tk,
        )
        LOG.debug(f"Running the code blocks for lab {lab}...")
        success: bool = run_code_blocks(
            all_code_blocks=all_code_blocks, cleanup_code_blocks=cleanup_code_blocks
        )
        if not success:
            break

        assert success

    # Reinstate the original clipboard contents
    tk.clipboard_clear()
    tk.clipboard_append(original_clipboard_content)

    assert success


def run_code_blocks(
    *,
    all_code_blocks: list[str],
    cleanup_code_blocks: list[str],
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

    image: str = "ubuntu:20.04"
    container = client.containers.run(
        image=image,
        auto_remove=False,
        detach=True,
        tty=True,
        volumes=volumes,
    )
    LOG.info(f"Created a container from image {image} called {container.name}")

    # Run each code block in the container
    for code in all_code_blocks:
        command: str = f'/bin/bash -c """set -euo pipefail && {code}"""'
        LOG.info(f"Running '{command}'")
        try:
            exit_code, output = container.exec_run(cmd=command, tty=True)
        except:
            LOG.error(f"container.exec_run failed to run '{command}'")
            container.kill()
            return False

        if exit_code == 0:
            LOG.debug(f"Successfully ran '{command}'")
            continue

        LOG.error(f"Failed test when running '{command}' with the output '{output}'")
        # Attempt to run the cleanup
        for cleanup_code in cleanup_code_blocks:
            base_cleanup_command: str = (
                f'/bin/bash -c """set -euo pipefail && {cleanup_code}"""'
            ).replace("\n", " || true\n")

            # If the last line doesn't have a newline, ensure it ends with || true as well
            if not base_cleanup_command.endswith(' || true"""'):
                cleanup_command: str = re.sub('"""$', ' || true"""', base_cleanup_command)
            else:
                cleanup_command: str = base_cleanup_command

            LOG.info(f"Running the cleanup command '{cleanup_command}'")
            try:
                exit_code, output = container.exec_run(cmd=cleanup_command, tty=True)
            except:
                LOG.error(f"container.exec_run failed to run '{cleanup_command}'")
                container.kill()
                return False

            if exit_code != 0:
                LOG.error(
                    f"Failed to run cleanup command '{cleanup_command}' with the output '{output}'"
                )
                container.kill()
                return False

            LOG.info(f"Received the following output from the cleanup commands '{output}'")

        container.kill()
        return False

    container.kill()
    return True


def get_code_from_code_blocks(*, lab_url: str, tk: Tk) -> tuple[list[str], list[str]]:
    """
    Get the code in the code blocks and return a tuple of:
    - All of the code blocks
    - The code blocks specifically for cleanup
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

        cleanup_div: ElementHandle | None = page.query_selector("div.highlight-cleanup")
        if not cleanup_div:
            LOG.error(f"No cleanup block in {lab_url}")
            sys.exit(1)

        # Click the copy buttons and extract the cleanup code block(s)
        cleanup_copy_buttons: list[ElementHandle] = cleanup_div.query_selector_all(
            'button[data-tooltip="Copy"]'
        )
        cleanup_code_blocks: list[str] = []
        for button in cleanup_copy_buttons:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accomodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the code_blocks list
            clipboard_content: str = tk.clipboard_get()
            cleanup_code_blocks.append(clipboard_content)

        # Click the copy buttons and extract all the code blocks
        all_copy_buttons: list[ElementHandle] = page.query_selector_all(
            'button[data-tooltip="Copy"]'
        )
        all_code_blocks: list[str] = []
        for button in all_copy_buttons:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accomodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the code_blocks list
            clipboard_content: str = tk.clipboard_get()
            all_code_blocks.append(clipboard_content)

    return all_code_blocks, cleanup_code_blocks
