#---------------------------------------------------------------------------------#
#Variables for VPC creation
#---------------------------------------------------------------------------------#
variable "region" {
  type = string
}

variable "create_vpc" {
  description = "Flag to determine whether to create the VPC or not"
  type        = bool
}

variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "env" {
  description = "Environment for the project"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
}
