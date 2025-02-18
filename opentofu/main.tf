provider "aws" {
  region = var.region
}

resource "aws_vpc" "workshop_tests" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "Workshop VPC - ${random_pet.lab.id}"
  }
}

resource "aws_subnet" "workshop_tests" {
  vpc_id                  = aws_vpc.workshop_tests.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}a"

  tags = {
    Name = "Workshop Subnet - ${random_pet.lab.id}"
  }
}

resource "aws_internet_gateway" "workshop_tests" {
  vpc_id = aws_vpc.workshop_tests.id

  tags = {
    Name = "Workshop IGW - ${random_pet.lab.id}"
  }
}

resource "aws_route_table" "workshop_tests" {
  vpc_id = aws_vpc.workshop_tests.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.workshop_tests.id
  }

  tags = {
    Name = "Workshop Route Table - ${random_pet.lab.id}"
  }
}

resource "aws_route_table_association" "workshop_tests" {
  subnet_id      = aws_subnet.workshop_tests.id
  route_table_id = aws_route_table.workshop_tests.id
}

data "http" "current_public_ip" {
  url = "http://checkip.amazonaws.com/"
}

locals {
  current_public_ip = format("%s/32", trimspace(data.http.current_public_ip.response_body))
}

resource "tls_private_key" "lab_keypair" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "random_pet" "lab" {
  length = 2
}

resource "aws_key_pair" "lab_keypair" {
  key_name   = "lab-key-${random_pet.lab.id}"
  public_key = tls_private_key.lab_keypair.public_key_openssh

  tags = {
    lifecycle = "transient"
  }
}

resource "local_file" "private_key" {
  content         = tls_private_key.lab_keypair.private_key_openssh
  filename        = "./zenable-${random_pet.lab.id}.key"
  file_permission = "0600"
}

resource "aws_security_group" "lab_sg" {
  name_prefix = "lab-sg-${random_pet.lab.id}"
  description = "Security group for the lab host"
  vpc_id      = aws_vpc.workshop_tests.id

  tags = {
    lifecycle = "transient"
  }
}

resource "aws_vpc_security_group_egress_rule" "lab_egress_allow_all" {
  security_group_id = aws_security_group.lab_sg.id

  description = "Allow all outbound traffic"
  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "lab_ingress_allow_only_ssh_from_deploy" {
  security_group_id = aws_security_group.lab_sg.id

  description = "Allow SSH access from current public IP"
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
  cidr_ipv4   = local.current_public_ip
}

data "aws_iam_policy_document" "lab_role_assume_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lab_role" {
  name               = "lab-role-${random_pet.lab.id}"
  assume_role_policy = data.aws_iam_policy_document.lab_role_assume_policy.json

  tags = {
    lifecycle = "transient"
  }
}

resource "aws_iam_role_policy_attachment" "lab_role_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  role       = aws_iam_role.lab_role.name
}

resource "aws_iam_instance_profile" "lab_instance_profile" {
  name = "lab-instance-profile-${random_pet.lab.id}"
  role = aws_iam_role.lab_role.name

  tags = {
    lifecycle = "transient"
  }
}

# Retrieve the latest Ubuntu 24.04 AMI from SSM Parameter Store
data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_instance" "lab" {
  ami                  = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type        = var.instance_type
  subnet_id            = aws_subnet.workshop_tests.id
  iam_instance_profile = aws_iam_instance_profile.lab_instance_profile.name

  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.lab_sg.id]
  key_name                    = aws_key_pair.lab_keypair.key_name
  user_data                   = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size = 40
    volume_type = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name      = "lab - ${random_pet.lab.id}"
    lifecycle = "transient"
  }
}

resource "null_resource" "wait_for_instance" {
  triggers = {
    instance_id = aws_instance.lab.id
  }

  depends_on = [aws_instance.lab]

  provisioner "local-exec" {
    command = <<EOF
      echo "Waiting for instance ${aws_instance.lab.id} to be in 'running' state..."
      aws ec2 wait instance-running --instance-ids "${aws_instance.lab.id}" --region "${var.region}"
      echo "Instance ${aws_instance.lab.id} is running."

      echo "Waiting for instance ${aws_instance.lab.id} to be ready for SSM..."
      while true; do
        ssm_status=$(aws ssm describe-instance-information --filters "Key=InstanceIds,Values=${aws_instance.lab.id}" --query "InstanceInformationList[*].PingStatus" --output text --region "${var.region}")
        if [ "$ssm_status" == "Online" ]; then
          echo "Instance ${aws_instance.lab.id} is ready for SSM."
          echo "${aws_instance.lab.id}" > instance_id
          break
        fi
        echo "Instance ${aws_instance.lab.id} is not ready for SSM yet. Retrying in 5 seconds..."
        sleep 5
      done
    EOF
  }
}

resource "null_resource" "wait_for_user_data" {
  triggers = {
    instance_ready = null_resource.wait_for_instance.id
  }

  depends_on = [null_resource.wait_for_instance]

  provisioner "local-exec" {
    command = <<EOF
      echo "Waiting for user_data script to complete on ${aws_instance.lab.id}..."

      while true; do
        command_id=$(aws ssm send-command \
          --document-name "AWS-RunShellScript" \
          --targets "Key=instanceids,Values=${aws_instance.lab.id}" \
          --parameters 'commands=["if [ -f /tmp/user_data_done ]; then echo DONE; else echo NOT_DONE; fi"]' \
          --query "Command.CommandId" \
          --output text --region "${var.region}")

        status=$(aws ssm list-command-invocations \
          --command-id "$command_id" \
          --instance-id "${aws_instance.lab.id}" \
          --query "CommandInvocations[0].Status" \
          --output text --region "${var.region}")

        if [ "$status" == "Success" ]; then
          result=$(aws ssm get-command-invocation \
            --command-id "$command_id" \
            --instance-id "${aws_instance.lab.id}" \
            --query "StandardOutputContent" \
            --output text --region "${var.region}")

          if [ "$result" == "DONE" ]; then
            echo "User data script has completed."
            break
          fi
        fi
        
        echo "User data script still running... Retrying in 5 seconds."
        sleep 5
      done
    EOF
  }
}
