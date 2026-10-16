# EKS control plane + one managed node group in the private subnets.
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Public API endpoint so kubectl works from a laptop; restrict the CIDRs in
  # terraform.tfvars. Nodes talk to the API privately.
  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs
  endpoint_private_access      = true

  # Whoever runs `terraform apply` becomes cluster admin (EKS access entries).
  enable_cluster_creator_admin_permissions = true
  access_entries = {
    for arn in var.admin_principal_arns : arn => {
      principal_arn = arn
      policy_associations = {
        admin = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  }

  enabled_log_types                      = ["api", "audit", "authenticator"]
  cloudwatch_log_group_retention_in_days = 3

  addons = {
    vpc-cni = {
      before_compute = true
      # Turn on enforcement of Kubernetes NetworkPolicy objects (used by the
      # Helm chart to lock PostgreSQL down to the backend pods).
      configuration_values = jsonencode({ enableNetworkPolicy = "true" })
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy = {}
    coredns    = {}
    # Dynamic EBS volumes for the PostgreSQL PersistentVolumeClaim.
    aws-ebs-csi-driver = {
      pod_identity_association = [{
        role_arn        = module.ebs_csi_pod_identity.iam_role_arn
        service_account = "ebs-csi-controller-sa"
      }]
    }
    # Resource metrics for `kubectl top` and the HorizontalPodAutoscaler.
    metrics-server = {}
  }

  eks_managed_node_groups = {
    general = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = var.node_disk_size
            volume_type           = "gp3"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }

      labels = {
        workload = "general"
      }
    }
  }

  tags = {
    Name = local.name
  }
}

# IAM role the EBS CSI controller assumes through EKS Pod Identity - no static
# AWS keys inside the cluster.
module "ebs_csi_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.0"

  name                      = "${local.name}-ebs-csi"
  attach_aws_ebs_csi_policy = true
}
