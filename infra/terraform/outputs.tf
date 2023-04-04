output "ip" {
  value = aws_eip.docker.*.public_ip
}

output "hosts" {
  value = aws_route53_record.docker.*.name
}
