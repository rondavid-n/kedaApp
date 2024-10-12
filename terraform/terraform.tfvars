#common values
region = "ap-south-1"
env = "dev"
project_name = "kedaapp"

#VPC values
availability_zones = ["ap-south-1a", "ap-south-1b"]

#EKS values
worker_node_counts = {
  "staging-worker-node" = {
    desired = 2
    min     = 2
    max     = 3
    instance_types = "t2.large"
  } 
}
cluster_name = "kedaapp-cluster-gw"
cluster_role_name = "kedaapp-cluster-gw-0"
worker_node_role_name = "kedaapp-cluster-gw-role-0"
ca_policy_name = "kedaapp-cluster-gw-cluster-autoscaler-0"
cluster_autoscaler_role = "kedaapp-cluster-gw-ca-role-0"
lb_controller_policy_name = "AWSLoadBalancerController-00"
lb_controller_role_name = "alb-controller-role-00"

#acm values
domain_name = "" # Provide the values, eg: *.testdomain.net
domain_name_fqdn = "" # Provide values, eg: test.testdomain.net