output "ec2_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.images.bucket
}

output "ssh_command" {
  value = "ssh -i YOUR_KEY_PATH ubuntu@${aws_instance.app_server.public_ip}"
}
