output "checks_bucket_name" {
  value = aws_s3_bucket.checks_data.bucket
}

output "model_bucket_name" {
  value = aws_s3_bucket.model_registry.bucket
}
