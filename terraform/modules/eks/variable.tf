variable "region" {
  type = string
}

variable "cluster_name" {
  description = "Name for the EKS cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EKS cluster will be created"
  type        = string
}

variable "project_name" {
  description = "project_name"
  type        = string  
}

variable "env" {
  type = string
}


variable "capacity_type" {
  type = string
}

variable "ami_type" {
  type = string
}

variable "worker_node_counts" {
  description = "Map of counts for EKS worker nodes"
  type        = map(object({
    desired = number
    min     = number
    max     = number
    instance_types = string
  }))
}

variable "cluster_subnets" {
  type = list(string)
}

variable "node_group_subnet" {
  type = list(string)
}

variable "disk_size" {
  type = string
}

variable "cluster_role_name" {
  type = string
}

variable "worker_node_role_name" {
  type = string
}

variable "lb_controller_role_name" {
  description = "LB controller name of the IAM role"
  type        = string
  # default     = "aws-load-balancer-controller"
}

variable "cluster_autoscaler_role" {
    description = "CA name of the IAM role"
  type        = string
}

variable "create_eks_cluster" {
  type = bool
}

variable "ca_policy_name" {
  type = string
}

variable "lb_controller_policy_name" {
  type = string
}