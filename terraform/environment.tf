provider "aws" {
  region = var.region
}

resource "aws_vpc" "workshop_tests" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "Workshop VPC"
  }
}

resource "aws_subnet" "workshop_tests" {
  vpc_id                  = aws_vpc.workshop_tests.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = local.availability_zone

  tags = {
    Name = "Workshop Subnet"
  }
}

resource "aws_internet_gateway" "workshop_tests" {
  vpc_id = aws_vpc.workshop_tests.id

  tags = {
    Name = "Workshop IGW"
  }
}

resource "aws_route_table" "workshop_tests" {
  vpc_id = aws_vpc.workshop_tests.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.workshop_tests.id
  }

  tags = {
    Name = "Workshop Route Table"
  }
}

resource "aws_route_table_association" "workshop_tests" {
  subnet_id      = aws_subnet.workshop_tests.id
  route_table_id = aws_route_table.workshop_tests.id
}

resource "aws_cloud9_environment_ec2" "workshop_tests" {
  name                        = var.cloud9_name
  description                 = "Cloud9 Environment for Workshop"
  instance_type               = var.cloud9_instance_type
  subnet_id                   = aws_subnet.workshop_tests.id
  image_id                    = var.cloud9_image
  automatic_stop_time_minutes = 240 # 4 hours

  connection_type = "CONNECT_SSM"
}

# Necessary because SSM commands on a Cloud9 instance don't have the permissions of the user until they open it, so we need to give additional permissions for
# the tests - https://docs.aws.amazon.com/cloud9/latest/user-guide/security-iam.html#temporary-managed-credentials-control
data "aws_instance" "cloud9_instance" {
  depends_on = [aws_cloud9_environment_ec2.workshop_tests]

  filter {
    name   = "subnet-id"
    values = [aws_subnet.workshop_tests.id]
  }
}

# Setup a new instance profile for cloud9
resource "aws_iam_instance_profile" "cloud9_instance_profile" {
  name = "workshop_cloud9_instance_profile"
  role = aws_iam_role.instance_role.name
}

data "aws_iam_policy_document" "instance_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance_role" {
  name               = "workshop_instance_role"
  assume_role_policy = data.aws_iam_policy_document.instance_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ec2_readonly_access" {
  role       = aws_iam_role.instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "cloud9_ssm_access" {
  role       = aws_iam_role.instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCloud9SSMInstanceProfile"
}

# Attach that instance profile to the running EC2 instance
resource "null_resource" "update_instance_profile" {
  triggers = {
    instance_id = data.aws_instance.cloud9_instance.id
  }

  depends_on = [aws_iam_instance_profile.cloud9_instance_profile, aws_cloud9_environment_ec2.workshop_tests]

  provisioner "local-exec" {
    command = <<EOF
      association_id="$(aws ec2 describe-iam-instance-profile-associations --filters "Name=instance-id,Values=${data.aws_instance.cloud9_instance.id}" --query "IamInstanceProfileAssociations[].AssociationId" --output text --region "${var.region}")"
      aws ec2 disassociate-iam-instance-profile --association-id "$association_id" --region "${var.region}"
      aws ec2 associate-iam-instance-profile --instance-id "${data.aws_instance.cloud9_instance.id}" --iam-instance-profile "Name=${aws_iam_instance_profile.cloud9_instance_profile.name}" --region "${var.region}"
    EOF
  }
}

locals {
  availability_zone = "${var.region}a"
}

resource "null_resource" "store_instance_id" {
  triggers = {
    environment_id = aws_cloud9_environment_ec2.workshop_tests.id
    instance_type  = aws_cloud9_environment_ec2.workshop_tests.instance_type
  }

  depends_on = [aws_cloud9_environment_ec2.workshop_tests]

  provisioner "local-exec" {
    command = <<EOF
      workshop_stack="$(aws cloudformation list-stacks --query "StackSummaries[?StackStatus != 'DELETE_COMPLETE' && starts_with(StackName, 'aws-cloud9-${var.cloud9_name}-')].[StackName]" --output text --region "${var.region}")"
      workshop_instance_id="$(aws cloudformation describe-stack-resources --stack-name "$workshop_stack" --query "StackResources[?ResourceType == 'AWS::EC2::Instance'].PhysicalResourceId" --output text --region "${var.region}")"
      echo "$workshop_instance_id" > "instance_id"
    EOF
  }
}

variable "cloud9_name" {
  description = "Name for the Cloud9 environment"
  type        = string
  default     = "Workshop"
}

variable "region" {
  description = "The region to create the test environment"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "The CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "cloud9_instance_type" {
  description = "The instance type for the Cloud9 environment"
  type        = string
  default     = "t3.xlarge"
}

variable "cloud9_image" {
  description = "The image to use for the Cloud9 environment"
  type        = string
  default     = "amazonlinux-2-x86_64"
}
