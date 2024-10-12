
data "tls_certificate" "eks" {
  count = var.create_eks_cluster ? 1 : 0  
  url   = aws_eks_cluster.eks[0].identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  count            = var.create_eks_cluster ? 1 : 0  
  url              = aws_eks_cluster.eks[0].identity[0].oidc[0].issuer
  client_id_list   = ["sts.amazonaws.com"]
  thumbprint_list  = [data.tls_certificate.eks[0].certificates[0].sha1_fingerprint]
}