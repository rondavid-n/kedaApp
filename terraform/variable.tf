variable "env" {
  description = "Name of environment"
  type = string  
}

variable "region" {
  description = "Region where the infra to be created"
  type = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string  
}


variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = []
}

#ACM value
variable "domain_name" {
  type = string
  # default = null
}
variable "domain_name_fqdn" {
  type = string
  # default = null
}

#EKS value
variable "cluster_name" {
  description = "Name for the EKS cluster"
  type        = string
  default = null
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

variable "cluster_role_name" {
  type = string
}

variable "worker_node_role_name" {
  type = string
}

variable "ca_policy_name" {
  type = string
}

variable "lb_controller_policy_name" {
  type = string
}

variable "cluster_autoscaler_role" {
  type = string
}

variable "lb_controller_role_name" {
  type = string
}

