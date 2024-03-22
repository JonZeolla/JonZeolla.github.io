# Tests

How it works:

1. Build the labs via a Taskfile.yml `test` dependency
1. Enumerate the labs by looking in build/labs/
1. Hold the host's clipboard off so it can be restored later
1. For each lab:
    1. Extract information from the rendered page using playwright:
        1. getting_started code blocks, which have a 2x parent div of class "getting-started"
        1. lab_commands code blocks, which are all non-getting_started code blocks
        1. config, which is an embedded JSON blob hidden in the lab for use when testing
    1. Render the tests/lab.tf.j2 Jinja2 template into a per-lab folder (which points to the terraform/environment.tf module)
    1. Run a `terraform init && terraform apply -auto-approve` in the lab module
        1. If this fails and (CI=true or an EC2 instance was never created), then run `terraform init && terraform destroy -auto-approve` and exit 1
        1. If the above is not true, keep the instance up but fail the tests, allowing follow-on troubleshooting.
    1. Run the getting_started code blocks in the Cloud9 EC2 instance
    1. Run the lab_commands code blocks in the Cloud9 EC2 instance
1. Restore the host clipboard

## Configuring tests

If you only want to run a specific test, set the variable `LAB` to the name of that tests (i.e. the base name of the lab file under `build/labs/`), i.e.:

```bash
LAB=container-security-101 task test
```

The same pattern exists for `task destroy`.

## Lessons Learned

The AWS cli is only setup upon opening the Cloud9 console, so we need to manually get and set the region for ansible's use

Cloud9 AMIs have curl but not jq, so you could use python instead like this (note the escaping):

```python
get_region_command: str = f'python3 -c "import urllib.request, json; print(json.load(urllib.request.urlopen(\\\"http://169.254.169.254/{metadata_version}/dynamic/instance-identity/document\\\"))[\\\"region\\\"])"'
```

The [AWS managed temporary credentials](https://docs.aws.amazon.com/cloud9/latest/user-guide/security-iam.html#temporary-managed-credentials-control) are
created on interactive use of the Cloud9 console (since they are tied to the AWS entity (i.e. user) using Cloud9). Because of this, running SSM commands before
interactive use causes `aws` commands to use the instance profile, which defaults to `AWSCloud9SSMAccessRole` and doesn't have enough access to read attributes
as expected by `amazon.aws.ec2_ami_info`.

To fix this, we create and attach a custom role as a part of the `terraform/envirnoment.tf`. If this doesn't happen, you'll get a permission denied issue,
currently starting with ec2:DescribeImages but this could change as the playbooks are updated.
