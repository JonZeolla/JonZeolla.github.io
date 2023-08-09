```{admonition} Environment Setup
---
class: important environment-setup
---
This lab expects that you are running on a fresh Ubuntu 20.04 x86 system.

To provision a fresh EC2 instance and minimal accompanying resources, follow these steps:

% See https://github.com/executablebooks/MyST-Parser/issues/760 for why the stackName below doesn't work

1. [Login to the AWS console](https://console.aws.amazon.com/console/home)
1. [Ensure you have an EC2
   keypair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/create-key-pairs.html#having-ec2-create-your-key-pair)
1. [Deploy this cloudformation
   template](https://console.aws.amazon.com/cloudformation/home#/stacks/quickcreate?templateURL=https://jonzeolla-labs.s3.amazonaws.com/cloudformation_ubuntu20.04.yml&stackName=Ubuntu%2020.04%20Workshop).

If you need more help, see [AWS's CloudFormation stacks
documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-using-console.html).

After provisioning is complete, see the "Outputs" to get the information needed to connect into your system.
```
