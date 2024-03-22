# Jon Zeolla

## Getting setup

Developing against this project assumes that you have the docker daemon running, the docker cli properly configured, and a modern version of both
[`task`](https://taskfile.dev/) and [`pipenv`](https://pipenv.pypa.io/en/latest/) installed and configured.

Run `task init` to setup your local environment, `task build` to build the project, and `task test` to test it. You can run `task open` to open the root
`index.html` in your local browser.

If you only want to test a single lab, set the `LAB` environment variable; more on this in the [tests README](./tests/README.md#configuring-tests).

If you'd like to turn debug logging on, set your `LOG_LEVEL` environment variable to `DEBUG`.

To autobuild as files change, run `nohup task -w build >/dev/null 2>&1 &` and clean up the job with `pkill -f 'task -w build'`

## Warning

When running the tests, the contents of your clipboard is saved to a variable in an attempt to reinstate it after the tests complete (which use the clipboard to
most closely approximate a user following the lab). It is possible that this has unintended consequences, or is imperfect.

## Known issues

1. Unable to have a heredoc in a {code-block} console, because the non-prompt lines for the heredoc won't be copied by the copy button.

## TODO

Cleanup the `arn:aws:s3:::jonzeolla-labs` s3 bucket if it's not needed for deployments or tests.
