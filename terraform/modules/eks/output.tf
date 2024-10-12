output "cluster_endpoint" {
  value = [for cluster in aws_eks_cluster.eks : cluster.endpoint]
}

output "cluster_name" {
  value = [for cluster in aws_eks_cluster.eks : cluster.name]
}