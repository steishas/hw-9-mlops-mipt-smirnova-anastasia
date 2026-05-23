terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "fake"
  secret_key                  = "fake"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  endpoints {
    s3  = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "checks_data" {
  bucket        = "retail-checks-${var.environment}"
  force_destroy = true   # чтобы terraform destroy удалял даже непустые бакеты
}

resource "aws_s3_bucket" "model_registry" {
  bucket        = "ml-model-registry-${var.environment}"
  force_destroy = true
}

resource "aws_iam_user" "airflow_user" {
  name = "airflow-ml-user-${var.environment}"
}

resource "aws_iam_policy" "s3_access" {
  name = "airflow-s3-access-${var.environment}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.checks_data.arn,
          "${aws_s3_bucket.checks_data.arn}/*",
          aws_s3_bucket.model_registry.arn,
          "${aws_s3_bucket.model_registry.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_s3" {
  user       = aws_iam_user.airflow_user.name
  policy_arn = aws_iam_policy.s3_access.arn
}
