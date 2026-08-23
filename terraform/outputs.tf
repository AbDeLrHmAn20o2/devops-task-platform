output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.devops.id
}

output "ec2_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.devops.public_ip
}