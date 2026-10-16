variable "region" {
  description = "AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for resources."
  type        = string
  default     = "slotsync"
}

variable "environment" {
  description = "Environment name, used in tags and names."
  type        = string
  default     = "demo"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "How many availability zones to spread subnets across (2 public + 2 private by default)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "EKS needs subnets in at least two availability zones; use 2 or 3."
  }
}

variable "single_nat_gateway" {
  description = "One shared NAT gateway (cheap, fine for a demo) instead of one per AZ (highly available)."
  type        = bool
  default     = true
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Keep it in standard support to avoid extended-support charges."
  type        = string
  default     = "1.35"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group."
  type        = list(string)
  default     = ["m7i-flex.large"]
}

variable "node_capacity_type" {
  description = "ON_DEMAND or SPOT."
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "node_capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  description = "Upper bound for the node group. 2 nodes x 2 vCPU fits a new account's 5 vCPU on-demand quota."
  type        = number
  default     = 2
}

variable "node_disk_size" {
  description = "Root EBS volume size (GiB) for each worker node."
  type        = number
  default     = 30
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public Kubernetes API endpoint. Narrow this to your own IP."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "admin_principal_arns" {
  description = "Extra IAM users/roles to grant cluster-admin through EKS access entries (the creator is always admin)."
  type        = list(string)
  default     = []
}
