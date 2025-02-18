output "ssh_command" {
  value = "ssh -i ${local_file.private_key.filename} ubuntu@${aws_instance.lab.public_ip}"
}

output "lab_public_ip" {
  value = aws_instance.lab.public_ip
}
