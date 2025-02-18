variable "region" {
  description = "The region to create the environment"
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

variable "instance_type" {
  description = "The instance type for the lab host"
  type        = string
  default     = "t3.micro"
}
