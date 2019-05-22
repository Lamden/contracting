variable "production" {
  type        = "string"
  description = "Whether or not the node is a production node"
  default     = false
}

#################################
## AWS provisioning parameters ##
#################################
variable "keyname" {
  type        = "string"
  description = "The name of the key as set inside AWS"
}

variable "private_key" {
  type        = "string"
  description = "The contents of the private key to use for deployment"
}

variable "size" {
  type        = "string"
  description = "The size of the node to launch"
  default     = "t2.small"
}

#######################
## Docker parameters ##
#######################
variable "docker_tag" {
  type        = "string"
  description = "The docker tag to use to launch the instance"
}

locals {
  nodename = "contracting-node"
  prefix   = "${var.keyname}-"
  image    = "lamden/seneca_base"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_ami" "cilantrobase" {
  owners      = ["self"]
  most_recent = true

  filter {
    name   = "name"
    values = ["cilantrobase-*"]
  }
}

# Define the security group
resource "aws_security_group" "contracting_firewall" {
  name        = "firewall-${local.prefix}${local.nodename}"
  description = "Allow specific ports necessary for contracting to work"

  ingress {
    from_port   = 443
    to_port     = 443
    description = "Allow HTTPS traffic through"
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    description = "Allow HTTP traffic through for cert validation"
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    description = "Port for Webserver if SSL is not enabled"
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    description = "Allow SSH connections to instance"
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    description = "Open up all ports for outbound traffic"
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "contracting-node" {
  key_name        = "${var.keyname}"
  ami             = "${data.aws_ami.cilantrobase.id}"
  instance_type   = "${var.size}"
  security_groups = ["${aws_security_group.contracting_firewall.name}"]

  tags = {
    Name       = "${local.prefix}-${local.nodename}"
    Touch      = "${timestamp()}"
    Production = "${var.production ? "True" : "False"}"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = "${var.private_key}"
  }

  depends_on = ["aws_security_group.contracting_firewall"]
}

resource "null_resource" "ssh-keys" {
  triggers {
    instance = "${aws_instance.contracting-node.public_ip}"
    conf     = "${file("./authorized_keys")}"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = "${var.private_key}"
    host        = "${aws_instance.contracting-node.public_ip}"
  }

  # Copy up our public keys to the nodes, leave existing file to keep existing keys
  provisioner "file" {
    source      = "./authorized_keys"
    destination = "/home/ubuntu/.ssh/authorized_keys.loc"
  }

  # Copy up authorized_keys to unique file, append into system authorized_keys, merge & deduplicate, move resulting file to system authorized_keys 
  provisioner "remote-exec" {
    inline = [
      "cat /home/ubuntu/.ssh/authorized_keys.loc >> /home/ubuntu/.ssh/authorized_keys",
      "sort /home/ubuntu/.ssh/authorized_keys | uniq > /home/ubuntu/.ssh/authorized_keys.loc",
      "mv /home/ubuntu/.ssh/authorized_keys.loc /home/ubuntu/.ssh/authorized_keys",
    ]
  }
}

# Swap out docker containers only if a new tag or image has been provided
resource "null_resource" "docker" {
  triggers {
    tag = "${var.docker_tag}"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = "${var.private_key}"
    host        = "${aws_instance.contracting-node.public_ip}"
  }

  # 1) Kill the 'cil' container
  # 2) Launch the new container
  provisioner "remote-exec" {
    inline = [
      "sudo docker rm -f cil",
      "sleep 30",
      "sudo docker run --name cil -dit -p 8080:8080 -p 443:443 -p 80:80 ${local.image}:${var.docker_tag}",
    ]
  }
}

output "public_ip" {
  value = "${aws_instance.contracting-node.public_ip}"
}
