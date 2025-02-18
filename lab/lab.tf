provider "aws" {
  region = "us-east-1"
}

module "lab" {
  source = "../opentofu"

  instance_type = "t3.xlarge"
}

output "ssh_command" {
  value = module.lab.ssh_command
}
