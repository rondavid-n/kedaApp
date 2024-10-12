
output "private_subnet_ids" {
  value = module.VPC.private_subnet_ids
}

output "public_subnet_ids" {
  value = module.VPC.public_subnet_ids
}

output "vpc_id" {
  value = module.VPC.vpc_id
}