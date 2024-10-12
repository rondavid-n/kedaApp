
data "aws_iam_policy_document" "aws_load_balancer_controller_assume_role_policy" {
  count = var.create_eks_cluster ? 1 : 0
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks[0].url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks[0].arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "aws_load_balancer_controller" {
  count             = var.create_eks_cluster ? 1 : 0
  assume_role_policy = data.aws_iam_policy_document.aws_load_balancer_controller_assume_role_policy[0].json
  name              = var.lb_controller_role_name
}

resource "aws_iam_policy" "aws_load_balancer_controller" {
  count = var.create_eks_cluster ? 1 : 0
  policy = file("${path.module}/AWSLoadBalancerController.json")
  name   = var.lb_controller_policy_name
}

resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller_attach" {
  count     = var.create_eks_cluster ? 1 : 0
  role      = aws_iam_role.aws_load_balancer_controller[0].name
  policy_arn = aws_iam_policy.aws_load_balancer_controller[0].arn
}

output "aws_load_balancer_controller_role_arn" {
  value = var.create_eks_cluster ? aws_iam_role.aws_load_balancer_controller[0].arn : null
}

