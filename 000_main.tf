provider "aws" {
  region = "eu-west-1"
}

terraform {
  required_version = "~> 0.11"

  backend "s3" {
    bucket               = "corp-terraform-state"
    dynamodb_table       = "terraform-lock"
    key                  = "create_product_jira_confluence.tfstate"
    workspace_key_prefix = ""
    region               = "eu-west-1"
    encrypt              = true
    kms_key_id           = "arn:aws:kms:eu-west-1:1234567890:key/6b7e1c45-e8be-470f-ad98-071234567890"
  }
}
