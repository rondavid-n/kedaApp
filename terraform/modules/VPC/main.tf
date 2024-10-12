#---------------------------------------------------------------------------------#
# Creation of VPC 
#---------------------------------------------------------------------------------#
resource "aws_vpc" "vpc" {
  count = var.create_vpc ? 1 : 0

  cidr_block             = var.cidr_block
  enable_dns_support     = true
  enable_dns_hostnames   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Environment = var.env
    Project     = var.project_name
  }
}

#---------------------------------------------------------------------------------#
# Creation of Internet Gateway 
#---------------------------------------------------------------------------------#
resource "aws_internet_gateway" "igw" {
  count = var.create_vpc ? 1 : 0

  vpc_id = var.create_vpc ? aws_vpc.vpc[0].id : null

  tags = {
    Name        = "${var.project_name}-igw"
    Environment = var.env
    Project     = var.project_name
  }
}

#---------------------------------------------------------------------------------#
# Creation of Elastic IP for NAT Gateway
#---------------------------------------------------------------------------------#
resource "aws_eip" "nat_ip" {
  count = var.create_vpc ? 1 : 0

  tags = {
    Name        = "${var.project_name}-eip"
    Environment = var.env
    Project     = var.project_name
  }
}

#---------------------------------------------------------------------------------#
# Creation of NAT Gateway 
#---------------------------------------------------------------------------------#
resource "aws_nat_gateway" "nat" {
  count         = var.create_vpc ? 1 : 0
  allocation_id = var.create_vpc ? aws_eip.nat_ip[0].id : null
  subnet_id     = var.create_vpc ? aws_subnet.public_subnet[0].id : null
  depends_on    = [aws_internet_gateway.igw]
  
  tags = {
    Name        = "${var.project_name}-natgw"
    Environment = var.env
    Project     = var.project_name
  }
}

#---------------------------------------------------------------------------------#
# Routing Table creation for public subnets
#---------------------------------------------------------------------------------#
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0

  vpc_id = var.create_vpc ? aws_vpc.vpc[0].id : null

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = var.create_vpc ? aws_internet_gateway.igw[0].id : null
  }

  tags = {
    Name        = "${var.project_name}-publicsubnet-rt"
    Environment = var.env
    Project     = var.project_name
  }
}

#---------------------------------------------------------------------------------#
# Creation of Public Subnets
#---------------------------------------------------------------------------------#
resource "aws_subnet" "public_subnet" {
  count = var.create_vpc ? var.public_subnet_count : 0

  vpc_id                  = var.create_vpc ? aws_vpc.vpc[0].id : null
  cidr_block              = element(var.public_subnet_cidrs, count.index)
  availability_zone       = element(var.availability_zones, count.index % length(var.availability_zones))
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-publicsubnet${count.index + 1}"
    Environment = var.env
    Project     = var.project_name
    "kubernetes.io/role/elb" = "1"
  }
  lifecycle {
    ignore_changes = [
      tags,
    ]
  }
}

#---------------------------------------------------------------------------------#
# Routing Table Association for Public Subnets
#---------------------------------------------------------------------------------#
resource "aws_route_table_association" "public_association" {
  count = var.create_vpc ? var.public_subnet_count : 0

  subnet_id      = var.create_vpc ? aws_subnet.public_subnet[count.index].id : null
  route_table_id = var.create_vpc ? aws_route_table.public[0].id : null
}

#---------------------------------------------------------------------------------#
# Routing Table creation for Private Subnets
#---------------------------------------------------------------------------------#
resource "aws_route_table" "private" {
  count = var.create_vpc ? 1 : 0

  vpc_id = var.create_vpc ? aws_vpc.vpc[0].id : null

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = var.create_vpc ? aws_nat_gateway.nat[0].id : null
  }

  tags = {
    Name        = "${var.project_name}-privatesubnet-rt"
    Environment = var.env
    Project     = var.project_name
  }

  lifecycle {
    ignore_changes = [route]
  }
}

#---------------------------------------------------------------------------------#
# Creation of Private Subnets 
#---------------------------------------------------------------------------------#
resource "aws_subnet" "private_subnet" {
  count = var.create_vpc ? var.private_subnet_count : 0
  # count = length(var.public_subnet_cidrs)

  vpc_id                  = var.create_vpc ? aws_vpc.vpc[0].id : null
  cidr_block              = element(var.private_subnet_cidrs, count.index)
  availability_zone       = element(var.availability_zones, count.index % length(var.availability_zones))

  tags = {
    Name        = "${var.project_name}-privatesubnet${count.index + 1}"
    Environment = var.env
    Project     = var.project_name
  }
  lifecycle {
    ignore_changes = [
      tags,
    ]
  }
}

#---------------------------------------------------------------------------------#
# Routing Table Association for Private Subnets
#---------------------------------------------------------------------------------#
resource "aws_route_table_association" "private_association" {
  count = var.create_vpc ? var.private_subnet_count : 0

  subnet_id      = var.create_vpc ? aws_subnet.private_subnet[count.index].id : null
  route_table_id = var.create_vpc ? aws_route_table.private[0].id : null
}