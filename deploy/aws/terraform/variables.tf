variable "region" { default = "us-east-1" }
variable "instance_type" { default = "t3.large" }
variable "key_name" { description = "Existing EC2 key pair name" }
variable "zip_url" { description = "Public URL to your project zip (e.g., S3 presigned URL)" }
variable "env_contents" { description = "Contents of your .env file", sensitive = true }
