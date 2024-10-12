provider "aws" {
  region = var.region 
}

#IAM Role for EKS Cluster
resource "aws_iam_role" "eks_cluster" {
  name = var.cluster_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "eks.amazonaws.com",
        },
      },
    ],
  })
}

#IAM Policy Attachment for EKS Cluster
resource "aws_iam_role_policy_attachment" "eks_cluster_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_ebs_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  # policy_arn = "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_dynamodb_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_rds_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_acm_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess"
  role       = aws_iam_role.eks_cluster.name
}

#EKS Cluster
resource "aws_eks_cluster" "eks" {
  count     = var.create_eks_cluster ? 1 : 0
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version = 1.29
  vpc_config {
    subnet_ids = var.cluster_subnets
  }
  tags = {
    Name = "${var.project_name}-eks-cluster"
    Environment = var.env
    Project = var.project_name
  }
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_attachment]
}

#IAM Role for EKS Managed Node Group
resource "aws_iam_role" "eks_node_group" {
  name = var.worker_node_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com",
        },
      },
    ],
  })
}

#IAM Policy Attachment for EKS Managed Node Group
resource "aws_iam_role_policy_attachment" "nodes-AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonWAFFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AWSWAFFullAccess"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonEC2FullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonRDSFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
  role       = aws_iam_role.eks_node_group.name
}

resource "aws_iam_role_policy_attachment" "nodes-AmazonDynamoDBFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.eks_node_group.name
}


# EKS Managed Node Group
resource "aws_eks_node_group" "eks_node_group" {
  for_each = var.create_eks_cluster ? var.worker_node_counts : {}
  cluster_name   = var.cluster_name
  node_group_name = each.key
  version = 1.29
  subnet_ids      = var.node_group_subnet
  scaling_config {
    desired_size = each.value.desired
    min_size     = each.value.min
    max_size     = each.value.max
  }

  node_role_arn  = aws_iam_role.eks_node_group.arn
  disk_size      = var.disk_size
  instance_types = [each.value.instance_types]
  capacity_type  = var.capacity_type
  ami_type = var.ami_type

  tags = {
    Name = "${var.project_name}-eks-worker-node-${each.key}"
    Environment = var.env
    Project = var.project_name
  }

  lifecycle {
    ignore_changes = [
      scaling_config
  ]  
}

  depends_on = [ aws_eks_cluster.eks[0] ]
}

#IAM Instance Profile
resource "aws_iam_instance_profile" "eks_node_group_instance_profile" {
  name = "eks-node-group-instance-profile-00"
  role = aws_iam_role.eks_node_group.name
}
