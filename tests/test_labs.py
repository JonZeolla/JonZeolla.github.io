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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import boto3
import pyperclip
import pytest
from jinja2 import Environment, FileSystemLoader
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


@dataclass
class Lab:
    getting_started: list[str]
    lab_commands: list[str]
    config: dict[str, str]
    file: Path


def get_labs() -> list[Path]:
    """
    Discover and return a list of Path objects pointing to lab instructions
    """
    # Fix a race with generating the lab artifacts
    time.sleep(1)

    labs_dir: Path = Path("build/labs/").absolute()

    if "LAB" in os.environ:
        lab: Path = labs_dir.joinpath(f"{os.environ['LAB']}.html")

        if lab.exists():
            return [lab]

        LOG.error(f"Failed to find the lab {lab}")
        sys.exit(1)
    else:
        labs: list[Path] = list(labs_dir.glob("**/[!index]*.html"))
        return labs


def run_opentofu(*, lab: Lab, command: str) -> Tuple[str, dict[str, str]]:
    """
    Find and deploy the opentofu for the provided lab

    Only supports apply or destroy subcommands

    Returns the instance ID of the created EC2 instance and the final config used when rendering the opentofu
    """
    if command not in ["apply", "destroy"]:
        LOG.error(f"Unsupported tofu command {command}")
        sys.exit(1)

    # This creates the final config that was used for rendering, which has defaults added where needed
    render_config, opentofu_module = render_lab_opentofu(
        lab=lab, config_update=lab.config
    )

    # Run the opentofu command
    opentofu_commands = [
        ["tofu", "init"],
        ["tofu", command, "-auto-approve"],
    ]
    for opentofu_command in opentofu_commands:
        opentofu_command_string = " ".join(opentofu_command)
        try:
            LOG.info(f"{lab.file.stem}: Running {opentofu_command_string}...")
            subprocess.run(
                opentofu_command,
                capture_output=True,
                text=True,
                cwd=opentofu_module,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            LOG.error(
                f"{lab.file.stem}: Failed to run {opentofu_command_string} with the output of {e.stdout} and the error of {e.stderr}"
            )
            handle_failed_opentofu(lab=lab)
            sys.exit(1)

    # Return the instance ID
    instance_id = get_instance_id(lab=lab, opentofu_module=opentofu_module)
    return instance_id, render_config


def get_instance_id(*, lab: Lab, opentofu_module: Path) -> str:
    """
    Get the instance ID from the provided lab's generated opentofu module folder
    """
    instance_id_file = opentofu_module.joinpath("instance_id")
    try:
        instance_id = instance_id_file.read_text().rstrip("\n")
    except FileNotFoundError:
        LOG.error(f"{lab.file.stem}: Failed to find the file {instance_id_file}")
        sys.exit(1)
    except PermissionError:
        LOG.error(f"{lab.file.stem}: Failed to read the file {instance_id_file}")
        sys.exit(1)

    return instance_id


def sanitize_code_block(*, code_block: str) -> str:
    """
    Sanitize the provided code block
    """
    sanitized_code_block = code_block

    # Escape single quotes
    sanitized_code_block = sanitized_code_block.replace("'", "'\\''")

    # Special case: Code blocks that contain HEREDOC are excluded from further sanitization
    if "HEREDOC" in sanitized_code_block:
        LOG.debug(f"Sanitized {code_block} into {sanitized_code_block}")
        return sanitized_code_block

    # Reduce multiple newlines to a single newline
    while "\n\n" in sanitized_code_block:
        sanitized_code_block = sanitized_code_block.replace("\n\n", "\n")

    # Replace newlines with && chaining for the SSM command
    sanitized_code_block = sanitized_code_block.replace("\n", " && ")

    # Remove any leading or trailing whitespace and &&s
    sanitized_code_block = sanitized_code_block.strip()
    sanitized_code_block = sanitized_code_block.strip(" && ")

    LOG.debug(f"Sanitized {code_block} into {sanitized_code_block}")
    return sanitized_code_block


def run_commands(
    *,
    lab: Lab,
    type: str,
    commands: list[str],
    instance_id: str,
    render_config: dict[str, str],
) -> bool:
    """
    Run the commands on the EC2 instance via SSM

    Return True for success and False for a failure
    """
    LOG.info(
        f"Running the {type} code blocks for lab {lab.file.stem} on the EC2 {instance_id}..."
    )

    if not commands:
        LOG.error(f"{lab.file.stem}: Passed an empty list of commands to run")
        return False

    success: bool = False

    # Setup
    region = render_config["region"]
    ssm_client = boto3.client("ssm", region_name=region)

    # Run each code block in the EC2 instance
    for code_block in commands:
        # Commands are always run from the user's home directory; if another dir is needed, the code block should handle it
        get_user_command: str = "getent passwd 1000 | awk -F: '{print $1}'"
        sanitized_code_block = sanitize_code_block(code_block=code_block)
        # TODO: Add `set -u` back in once "/home/ec2-user/.rvm/scripts/functions/rvmrc_env: line 66: rvm_saved_env: unbound variable" is fixed in Amazon Linux
        # ~related to https://github.com/rvm/rvm/issues/4694
        command: str = (
            f"export user=$({get_user_command}) && su - ${{user}} --shell /bin/bash -c 'set -eo pipefail && cd && {sanitized_code_block}'"
        )
        LOG.debug(f"{lab.file.stem}: Running {command}")
        response = ssm_client.send_command(
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
            InstanceIds=[instance_id],
        )
        success = wait_for_completion(
            ssm_client=ssm_client,
            command_id=response["Command"]["CommandId"],
            instance_id=instance_id,
        )

        if not success:
            LOG.error(f"{lab.file.stem}: Failed running {command}")
            handle_failed_opentofu(lab=lab, instance_id=instance_id)
            return False

    return True


def wait_for_completion(
    *, ssm_client: boto3.client, command_id: str, instance_id: str
) -> bool:
    """
    Wait for the provided command to complete and return whether or not it was successful
    """
    LOG.debug(
        f"Waiting for the command {command_id} to complete on the EC2 {instance_id}..."
    )
    success: bool = False

    while True:
        response = ssm_client.list_commands(CommandId=command_id)
        status = response["Commands"][0]["Status"]
        if status == "Success":
            LOG.debug(
                f"The run-command {command_id} completed successfully on the EC2 {instance_id}..."
            )
            success = True
            break
        elif status == "Failed":
            ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )
            invocation_response = ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )
            stdout = invocation_response.get("StandardOutputContent")
            stderr = invocation_response.get("StandardErrorContent")
            LOG.error(f"stderr: {stderr}, stdout: {stdout}")
            LOG.error(
                f"The run-command {command_id} failed on the EC2 {instance_id}, see above for the stdout and stderr..."
            )

            success = False
            break
        else:
            LOG.debug(
                f"The run-command {command_id} is still running on the EC2 {instance_id}..."
            )
            time.sleep(2)

    return success


def handle_failed_opentofu(*, lab: Lab, instance_id: str = "") -> None:
    """
    Handle cleanup after a failed opentofu run
    """
    if os.environ.get("CI") == "true" or not instance_id:
        run_opentofu(lab=lab, command="destroy")
    else:
        LOG.warning(f"Leaving the EC2 {instance_id} up for troubleshooting...")


def get_code_from_commands(*, lab_path: Path) -> Lab:
    """
    Get the code in the code blocks of the provided lab URL

    Returns a Lab object
    """
    lab_url: str = f"file://{lab_path}"
    LOG.debug(f"Getting the code blocks for the {lab_path.stem} lab from {lab_url}...")

    with sync_playwright() as playwright:
        # TODO: change to True
        browser: Browser = playwright.chromium.launch(slow_mo=50, headless=False)
        context: BrowserContext = browser.new_context()
        page: Page = context.new_page()
        page.goto(lab_url)

        # Find all the dropdowns that are hidden and open them. If you don't do this first, the loop below for clicking
        # the copy buttons will sometimes double account for code blocks because it will expand a dropdown when it
        # thinks it's clicking a copy button, and it pulls the unchanged clipboard into the commands list for a
        # second time
        toggle_divs: list[ElementHandle] = page.query_selector_all("div.toggle-hidden")

        # Extract the testing config
        config: dict = json.loads(page.inner_text(".testConfig"))

        # Identify if there's a getting started override for testing
        getting_started: list[str] = []
        getting_started_override: bool = (
            page.locator(".overrideGettingStarted").count() > 0
        )
        if getting_started_override:
            LOG.debug("Detected a getting started override, using it...")
            getting_started.append(page.inner_text(".overrideGettingStarted"))

        # Click the dropdowns to expand them
        for div in toggle_divs:
            div.click()

        # Click the copy buttons and extract the code blocks
        copy_buttons: list[ElementHandle] = page.query_selector_all(
            'button[data-tooltip="Copy"]'
        )
        lab_commands: list[str] = []
        for button in copy_buttons:
            # The force is because the copy button from sphinx-copybutton often isn't visible, and pywright will wait
            # until it times out without additional adjustments to accommodate. Hover doesn't work in headless mode, etc.
            button.click(force=True)

            # Pull the clipboard content into the commands list
            clipboard_content: str = pyperclip.paste()

            # Get the parent's parent element
            parent_element = button.evaluate_handle(
                "button => button.parentElement"
            ).evaluate_handle("el => el.parentElement")
            classes = parent_element.get_attribute("class").split()

            # Skip the code blocks that have a class of skip-tests
            if "skip-tests" in classes:
                LOG.warning(
                    f"Skipping a code block in {lab_path.stem} because it has a class of skip-tests..."
                )
                continue

            if getting_started_override:
                # If there was an getting started override, add everything that isn't getting-started as a lab command
                if "getting-started" not in classes:
                    lab_commands.append(clipboard_content)
            else:
                # Check if the parent element has a class of getting-started
                if "getting-started" in classes:
                    getting_started.append(clipboard_content)
                else:
                    lab_commands.append(clipboard_content)

    lab = Lab(
        getting_started=getting_started,
        lab_commands=lab_commands,
        config=config,
        file=lab_path,
    )
    return lab


def render_lab_opentofu(
    *, lab: Lab, config_update: dict[str, str]
) -> Tuple[dict[str, str], Path]:
    """
    Render the lab-specific opentofu live

    Returns the final configuration used when rendering, as well as a Path to the rendered opentofu module
    """
    opentofu_template = Path("tests/lab.tf.j2")
    opentofu_module = Path("tests").joinpath(lab.file.stem)
    opentofu_module.mkdir(exist_ok=True)
    LOG.debug(f"Using the opentofu module {opentofu_module}...")
    opentofu_live = opentofu_module.joinpath(lab.file.stem).with_suffix(".tf")

    # Set a default config, and then update it with the provided config
    render_config = {
        "lab_name": lab.file.stem,
        "lab_instance_type": "t3.xlarge",
        "region": "us-east-1",
    }
    render_config.update(config_update)

    render_jinja2(
        template_file=opentofu_template,
        config=render_config,
        output_file=opentofu_live,
    )

    return render_config, opentofu_module


def render_jinja2(
    *,
    template_file: Path,
    config: dict,
    output_file: Path,
    output_mode: Optional[int] = None,
) -> None:
    """
    Render the provided template file
    """
    folder = str(template_file.parent)
    file = str(template_file.name)
    LOG.info(f"Rendering {template_file} into {output_file}...")
    LOG.debug(f"Using config {config}...")
    template = Environment(loader=FileSystemLoader(folder)).get_template(file)
    out = template.render(config)
    output_file.write_text(out)
    if output_mode is not None:
        output_file.chmod(output_mode)


# Typically this would be a session fixture, but since we plan to parallelize with pytest-xdist we parameterize the test and call this like a normal function
def lab_setup() -> list[Lab]:
    """
    Setup all of the labs and return a list of Lab objects
    """
    # Hold the original clipboard contents to reinstate later
    original_clipboard_content: str = pyperclip.paste()

    lab_paths: list[Path] = get_labs()

    labs: list[Lab] = []
    for lab_path in lab_paths:
        # The returned config here is only what is in the lab's testConfig, and doesn't include defaults
        # It's important to do this step synchronously, because the clipboard is used to get the code blocks from the lab instructions
        lab = get_code_from_commands(
            lab_path=lab_path,
        )
        lab.file = lab_path
        labs.append(lab)

    # Reinstate the original clipboard contents
    pyperclip.copy(original_clipboard_content)

    return labs


@pytest.mark.parametrize("lab", lab_setup())
def test_lab(lab: Lab) -> None:
    """
    Test the code blocks in the provided lab
    """
    # This updates the config that was passed in with the final config that was used for rendering, which has defaults added where needed
    instance_id, render_config = run_opentofu(lab=lab, command="apply")

    if lab.getting_started:
        assert run_commands(
            lab=lab,
            type="getting started",
            commands=lab.getting_started,
            instance_id=instance_id,
            render_config=render_config,
        )
    else:
        LOG.error(f"No getting started code blocks for lab {lab} detected...")
        assert False

    assert run_commands(
        lab=lab,
        type="lab commands",
        commands=lab.lab_commands,
        instance_id=instance_id,
        render_config=render_config,
    )
