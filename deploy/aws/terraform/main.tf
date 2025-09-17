terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = var.region }

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter { name = "name"; values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"] }
}

resource "aws_security_group" "ai_starter" {
  name        = "ai-starter-sg"
  description = "Allow HTTP & custom ports"
  ingress { from_port = 22, to_port = 22, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 80, to_port = 80, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 3000, to_port = 3000, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 8000, to_port = 8000, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"] }
  egress  { from_port = 0, to_port = 0, protocol = "-1", cidr_blocks = ["0.0.0.0/0"] }
}

locals {
  user_data = <<-EOT
  #!/bin/bash
  set -euxo pipefail
  apt-get update
  apt-get install -y docker.io unzip curl git
  systemctl enable --now docker
  usermod -aG docker ubuntu || true

  cd /opt
  curl -L -o ai-app.zip "${var.zip_url}"
  unzip -o ai-app.zip
  cd ai-starter

  cat > .env <<'ENVV'
  ${var.env_contents}
  ENVV

  # Reverse proxy 80 -> frontend:3000 inside docker network
  mkdir -p deploy/aws/scripts
  cat > deploy/aws/scripts/nginx.conf <<'NGINX'
  events {}
  http {
    server {
      listen 80;
      location / {
        proxy_pass http://frontend:3000;
      }
    }
  }
  NGINX

  docker rm -f nginx || true
  docker compose up -d --build
  docker run -d --name nginx --network ${replace("ai-starter_default", "_", "\_")} -p 80:80 --restart unless-stopped -v $(pwd)/deploy/aws/scripts/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine || true
  EOT
}

resource "aws_instance" "ai_starter" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.ai_starter.id]
  associate_public_ip_address = true
  user_data                   = local.user_data
  tags = { Name = "ai-starter" }
}

output "public_ip" { value = aws_instance.ai_starter.public_ip }
output "urls" {
  value = {
    ui  = "http://${aws_instance.ai_starter.public_ip}"
    api = "http://${aws_instance.ai_starter.public_ip}:8000/docs"
  }
}
