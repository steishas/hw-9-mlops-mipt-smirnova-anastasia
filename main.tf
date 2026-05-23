terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "minioadmin"
  secret_key                  = "minioadmin"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true          # ← обязательно для MinIO
  endpoints {
    s3 = "http://localhost:9000"
  }
}

resource "aws_s3_bucket" "checks_data" {
  bucket        = "retail-checks-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket" "model_registry" {
  bucket        = "ml-model-registry-${var.environment}"
  force_destroy = true
}
