module "VPC" {
  source = "./modules/VPC"
  create_vpc = true
  cidr_block = "10.2.0.0/16"
  env = var.env
  project_name = var.project_name
  public_subnet_count = 2
  public_subnet_cidrs = ["10.2.1.0/24", "10.2.2.0/24"]
  private_subnet_count = 1
  private_subnet_cidrs = ["10.2.3.0/24"]
  region = var.region
  availability_zones = var.availability_zones
}

module "eks"{
  source = "./modules/eks"
  region = var.region
  worker_node_counts = var.worker_node_counts
  cluster_name = var.cluster_name
  vpc_id = module.VPC.vpc_id
  project_name = var.project_name
  env = var.env
  capacity_type = "ON_DEMAND"
  ami_type = "AL2_x86_64"
  disk_size = "50"
  node_group_subnet = module.VPC.public_subnet_ids
  cluster_subnets = module.VPC.public_subnet_ids
  lb_controller_role_name = "${var.lb_controller_role_name}-${var.cluster_name}"
  cluster_autoscaler_role = "${var.cluster_autoscaler_role}-${var.cluster_name}"
  create_eks_cluster = true
  worker_node_role_name = "${var.worker_node_role_name}-${var.cluster_name}"
  cluster_role_name = "${var.cluster_role_name}-${var.cluster_name}"
  lb_controller_policy_name = "${var.lb_controller_policy_name}-${var.cluster_name}"
  ca_policy_name = "${var.ca_policy_name}-${var.cluster_name}"
}

module "ACM" {
  source      = "./modules/ACM"
  domain_name = var.domain_name
  domain_name_fqdn = var.domain_name_fqdn
}
