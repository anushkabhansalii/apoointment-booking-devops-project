terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }

  # State is kept locally for this single-operator project and is git-ignored.
  # For a team, store it remotely with locking, e.g.:
  # backend "s3" {
  #   bucket       = "slotsync-tfstate-<account-id>"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}
