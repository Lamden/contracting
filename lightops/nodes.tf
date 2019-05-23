variable "keyname" {
  type        = "string"
  description = "The name of the key to create"
}

variable "docker_tag" {
  type        = "string"
  description = "The docker tag to run"
}

variable "aws_profile" {
  type        = "string"
  description = "The aws profile to use"
  default     = "default"
}

provider "aws" {
  region  = "us-west-1"
  profile = "${var.aws_profile}"
}

# N. California
provider "aws" {
  region  = "us-west-1"
  alias   = "us-west-1"
  profile = "${var.aws_profile}"
}

resource "tls_private_key" "provisioner" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "us-west-1" {
  key_name   = "${var.keyname}"
  public_key = "${tls_private_key.provisioner.public_key_openssh}"
  provider   = "aws.us-west-1"
}

module "contracting-node" {
  source = "./modules/contracting_node"

  providers = {
    aws = "aws.us-west-1"
  }

  production = false

  keyname     = "${var.keyname}"
  private_key = "${tls_private_key.provisioner.private_key_pem}"
  docker_tag  = "${var.docker_tag}"
}

output "contracting-ssh" {
  value = "ssh ubuntu@${module.contracting-node.public_ip}"
}
