provider "helm" {
  dynamic "kubernetes" {
    for_each = var.create_eks_cluster ? ["eks"] : []

    content {
      host                   = aws_eks_cluster.eks[0].endpoint
      cluster_ca_certificate = base64decode(aws_eks_cluster.eks[0].certificate_authority[0].data)
      
      exec {
        api_version = "client.authentication.k8s.io/v1beta1"
        args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.eks[0].id]
        command     = "aws"
      }
    }
  }
}

resource "helm_release" "aws-load-balancer-controller" {
  count = var.create_eks_cluster ? 1 : 0

  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.4.1"

  set {
    name  = "clusterName"
    value = aws_eks_cluster.eks[0].id
  }

  set {
    name  = "image.tag"
    value = "v2.4.2"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = var.create_eks_cluster ? aws_iam_role.aws_load_balancer_controller[0].arn : null
  }

  set {
    name  = "vpcId"
    value = var.create_eks_cluster ? var.vpc_id : null
  }
}

# Additional resources to handle depends_on
resource "null_resource" "eks_node_group_dependency" {
  count = var.create_eks_cluster ? 1 : 0
  depends_on = [aws_eks_node_group.eks_node_group]
}

resource "null_resource" "iam_policy_attachment_dependency" {
  count = var.create_eks_cluster ? 1 : 0
  depends_on = [aws_iam_role_policy_attachment.aws_load_balancer_controller_attach]
}