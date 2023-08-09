#!/usr/bin/env python3
"""
Tests for my labs
"""

import logging
import os
import sys
from pathlib import Path
from tkinter import Tk

import boto3
import paramiko
from playwright.sync_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    sync_playwright,
)

LOG = logging.getLogger(__name__)
LOG.setLevel("NOTSET")

std_err = logging.StreamHandler(sys.stderr)
std_err.setLevel("ERROR")

std_out = logging.StreamHandler(sys.stdout)
std_out.setLevel("DEBUG")
std_out.addFilter(lambda x: x.levelno < logging.ERROR)

LOG.addHandler(std_err)
LOG.addHandler(std_out)


#########################################################################
# These tests are all WIP and are likely not even directionally correct #
#########################################################################
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
        ip: str = deploy_cloudformation(lab=lab)
        lab_url: str = f"file://{cwd}/{lab}"
        LOG.debug(f"Getting the code blocks for lab {lab} from {lab_url}...")
        code_blocks: list[str] = get_code_from_code_blocks(
            lab_url=lab_url,
            tk=tk,
        )
        LOG.debug(f"Running the code blocks for lab {lab} on the server at {ip}...")
        success: bool = run_code_blocks(code_blocks=code_blocks, ip=ip)
        if not success:
            if os.environment.get("CI") == "true":
                LOG.error("Something failed; deleting the cloudformation stack")
                if not delete_cloudformation(lab=lab):
                    LOG.error(
                        f"Unable to delete the cloudformation stack for lab {lab}"
                    )
            else:
                LOG.warning(
                    "Leaving the EC2 up for troubleshooting; don't forget to clean it up"
                )
            break

        # This should always assert True
        assert success

    # Reinstate the original clipboard contents
    tk.clipboard_clear()
    tk.clipboard_append(original_clipboard_content)

    assert success


def get_cloudformation_template_url(*, lab: Path) -> str:
    """
    Retrieve the cloudformation template from the provided and return its contents
    """
    # Each lab has an accompanying JSON file stored in s3 for testing
    s3 = boto3.client("s3")
    s3.download_file("jonzeolla-labs", lab.name, lab.name)

    cloudformation_template_path: Path = Path("TODO")
    cloudformation_template: str = cloudformation_template_path.read_text()
    # TODO: Either we need to read the file as yml to start, or we can try somethign like with open
    # (cloudformation_template, "r") as stream: and see if it will just handle it as a string.  Then we can
    # yaml.safe_load(stream) and extract info like the stack name, etc.

    # TODO
    return cloudformation_template


def delete_cloudformation(*, lab: Path) -> bool:
    """
    Find and delete the cloudformation stack
    Returns False when unsuccessful
    """
    cloudformation_template: str = get_cloudformation_template_url(lab=lab)
    cloudformation = boto3.client("cloudformation")
    cloudformation.delete_stack(StackName="Workshop")


def deploy_cloudformation(*, lab: Path, ssh_public_key: Path) -> str:
    """
    Find and deploy the cloudformation stack inside a download class of the environment-setup div

    Returns the IP address
    """
    cloudformation_template: str = get_cloudformation_template_url(lab=lab)

    # TODO: Incomplete
    parameters: list[dict[str, str | bool]] = [
        {"ParameterKey": "SSHAccessKey", "ParameterValue": "Workshop"}
    ]

    # Then, we deploy the cloudformation template that we just downloaded
    cloudformation = boto3.client("cloudformation")
    response_create_stack: dict = cloudformation.create_stack(
        StackName="Workshop",
        TemplateBody=cloudformation_template,
        Parameters=parameters,
    )
    stack_id: str = response_create_stack["StackId"]
    response_describe_stacks: dict = cloudformation.describe_stacks(StackName=stack_id)
    outputs: list[dict[str, str]] = response_describe_stacks["Stacks"][0]["Outputs"]
    for output in outputs:
        if output["OutputKey"] == "IPAddress":
            ip: str = output["OutputValue"]
            break
    else:
        LOG.error(
            "Unable to determine the IP address of the deployed cloudformation template in lab {lab}"
        )
        sys.exit(1)

    return ip


def run_code_blocks(
    *,
    code_blocks: list[str],
    ip: str,
) -> bool:
    """
    Run the code in the provided code blocks on the server provided via ip
    """
    # Allow but warn on empty code blocks
    if not code_blocks:
        LOG.warning(
            "Passed an empty list of code blocks, allowing the build to pass, but this may not be expected"
        )
        return True

    # Setup ssh
    private_key_path: Path = Path("~/.ssh/workshop.pem")
    ssh: paramiko.SSHClient = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key: paramiko.RSAKey = paramiko.RSAKey.from_private_key_file(
        str(private_key_path)
    )
    ssh.connect(hostname=ip, username="ubuntu", pkey=private_key)

    # Run each code block in the EC2 instance
    for code in code_blocks:
        # TODO: do we need to adjust the set -euo pipefail?
        command: str = f'/bin/bash -c """set -euo pipefail && {code}"""'
        LOG.info(f"Running '{command}'")
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
        except:
            LOG.error(f"container.exec_run failed to run '{command}'")
            return False

        exit_code: int = stdout.channel.recv_exit_status()
        if exit_code == 0:
            LOG.debug(f"Successfully ran '{command}'")
            continue

        LOG.error(
            f"Failed test when running '{command}' with the stdout '{stdout}' and stderr of '{stderr}'"
        )

        return False

    return True


def get_code_from_code_blocks(*, lab_url: str, tk: Tk) -> list[str]:
    """
    Get the code in the code blocks of the provided lab URL

    Returns all of the code blocks as a list of strings (one element per code block in the instructions)
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

        # Click the copy buttons and extract the code blocks
        copy_buttons: list[ElementHandle] = page.query_selector_all(
            'button[data-tooltip="Copy"]'
        )
        code_blocks: list[str] = []
        for button in copy_buttons:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accomodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the code_blocks list
            clipboard_content: str = tk.clipboard_get()
            code_blocks.append(clipboard_content)

    return code_blocks
