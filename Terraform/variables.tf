variable "aws_region" {
  default = "eu-west-2"
}

variable "project_name" {
  default = "image-processing-portal"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  default = "10.0.1.0/24" 
}

variable "allowed_ssh_ip" {
  description = "Your public IP address for SSH access"
}

variable "instance_type" {
  default = "t2.micro"
}

variable "key_name" {
  description = "Name of your existing EC2 key pair"
}

variable "ami_id" {
  description = "Ubuntu AMI ID for your region"
}