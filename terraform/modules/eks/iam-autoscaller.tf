#---------------------------------------------------------------------------------#
#EKS cluster role data retrival
#---------------------------------------------------------------------------------#
data "aws_iam_policy_document" "eks_cluster_autoscaler_assume_role_policy" {
  count = var.create_eks_cluster ? 1 : 0
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks[0].url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:cluster-autoscaler"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks[0].arn]
      type        = "Federated"
    }
  }
}

#---------------------------------------------------------------------------------#
#Creation of Cluster autoscaler role
#---------------------------------------------------------------------------------#
resource "aws_iam_role" "eks_cluster_autoscaler" {
  count             = var.create_eks_cluster ? 1 : 0
  name              = var.cluster_autoscaler_role
  assume_role_policy = data.aws_iam_policy_document.eks_cluster_autoscaler_assume_role_policy[0].json
}

#---------------------------------------------------------------------------------#
#Creation of Cluster autoscaler policy
#-------------------------autoscaler--------------------------------------------------------#
resource "aws_iam_policy" "eks_cluster_autoscaler_policy" {
  count   = var.create_eks_cluster ? 1 : 0
  name    = var.ca_policy_name
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "ec2:DescribeLaunchTemplateVersions"
        ],
        "Effect": "Allow",
        "Resource": "*"
      }
    ]
  })
}

#---------------------------------------------------------------------------------#
#Cluster Autoscaler policy attachment
#---------------------------------------------------------------------------------#
resource "aws_iam_policy_attachment" "eks_cluster_autoscaler_policy_attach" {
  count       = var.create_eks_cluster ? 1 : 0
  name = var.ca_policy_name
  roles       = [aws_iam_role.eks_cluster_autoscaler[0].name]
  policy_arn  = aws_iam_policy.eks_cluster_autoscaler_policy[0].arn

  depends_on = [
    aws_iam_role.eks_cluster_autoscaler, 
    aws_iam_policy.eks_cluster_autoscaler_policy
  ]
}

#---------------------------------------------------------------------------------#
#Cluster autoscaler role attachment
#---------------------------------------------------------------------------------#
resource "aws_iam_role_policy_attachment" "eks_cluster_autoscaler_attach" {
  count     = var.create_eks_cluster ? 1 : 0
  role      = aws_iam_role.eks_cluster_autoscaler[0].name
  policy_arn = aws_iam_policy.eks_cluster_autoscaler_policy[0].arn

  depends_on = [
    aws_iam_role.eks_cluster_autoscaler, 
    aws_iam_policy.eks_cluster_autoscaler_policy
  ]
}

output "eks_cluster_autoscaler_arn" {
  value = var.create_eks_cluster ? aws_iam_role.eks_cluster_autoscaler[0].arn : null
}