output "domain_name" {
  description = "The name of the Domain"
  value = var.domain_name
}

output "acm_certificate_arn" {
  description = "The ARN of the ACM certificate"
  value       = aws_acm_certificate.acm_certificate.arn
}
