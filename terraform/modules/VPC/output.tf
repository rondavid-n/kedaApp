#---------------------------------------------------------------------------------#
#Outputs of VPC
#---------------------------------------------------------------------------------#
output "vpc_id" {
  value = var.create_vpc ? aws_vpc.vpc[0].id : null
}

output "igw_id" {
  value = var.create_vpc ? aws_internet_gateway.igw[0].id : null
}

output "nat_gateway_id" {
  value = var.create_vpc ? aws_nat_gateway.nat[0].id : null
}

output "public_subnet_ids" {
  value = var.create_vpc ? aws_subnet.public_subnet[*].id : []
}

output "private_subnet_ids" {
  value = var.create_vpc ? aws_subnet.private_subnet[*].id : []
}
