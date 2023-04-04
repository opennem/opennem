
variable "aws_region" {
  description = "AWS region to launch servers."
  default     = "ap-southeast-2"
}

variable "aws_access_key_id" {}

variable "aws_secret_access_key" {}

variable "aws_zones" {
  type        = list
  description = "List of availability zones to use"
  default     = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
}

variable "instances_number" {
  default = 1
}

variable "instance_size" {
  type = map
  default = {
    "docker" = "t2.micro"
  }
}

variable "public_key_path" {
  description = "ssh public key path"
  default     = "~/.ssh/opennem_prod"
}

variable "public_key_name" {
  description = "Desired name of AWS key pair"
  default     = "opennem_prod"
}

variable "public_key_public" {
  description = "ssh deployer public key content"
  default     = ""
}
