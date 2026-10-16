locals {
  name = "${var.project}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

# VPC with public and private subnets in each AZ.
#   public  10.20.0.0/20, 10.20.16.0/20   -> internet-facing load balancers, NAT gateway
#   private 10.20.64.0/18, 10.20.128.0/18 -> EKS worker nodes and pods (large: VPC CNI gives every pod a VPC IP)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.7"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  public_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  private_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 2, i + 1)]

  enable_nat_gateway   = true
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  map_public_ip_on_launch = true

  # These tags tell Kubernetes / the AWS load balancer integration where to
  # place internet-facing and internal load balancers.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = {
    "kubernetes.io/cluster/${local.name}" = "shared"
  }
}
