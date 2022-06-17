locals {
  create_product_jira_confluence_name = "create_product_jira_confluence"
  create_product_jira_confluence_code = ".terraform/lambdas/create-product-jira-confluence/create-product-jira-confluence.zip"
}

module "lambda_create_product_jira_confluence" {
  source = "git::ssh://git@code.company.com/core/aws-lambda-function?ref=X.Y.Z"

  func_name        = "${local.create_product_jira_confluence_name}"
  func_description = "Create Product Jira Confluence"
  func_handler     = "create_product_jira_confluence.lambda_handler"
  filename         = "${data.archive_file.lambda_zip.output_path}"
  source_code_hash = "${base64sha256(file(data.archive_file.lambda_zip.output_path))}"
  env_runtime      = "python3.7"
  env_timeout      = 900
  role_arn         = "${aws_iam_role.create_product_jira_confluence.arn}"
  layers           = ["${data.aws_lambda_layer_version.requests_lambda_layer.arn}"]

  env_concurrency = 2

  tags = "${var.tags}"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "lambdas/create-product-jira-confluence"
  output_path = "${local.create_product_jira_confluence_code}"
}

### Permissions
resource "aws_iam_role" "create_product_jira_confluence" {
  name = "create_product_jira_confluence"
  path = "${local.path}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  tags = "${var.tags}"
}

resource "aws_iam_role_policy_attachment" "create_product_jira_confluence_basic" {
  role       = "${aws_iam_role.create_product_jira_confluence.name}"
  policy_arn = "${local.basic_lambda_policy}"
}

resource "aws_iam_role_policy_attachment" "create_product_jira_confluence_ssm_kms" {
  role       = "${aws_iam_role.create_product_jira_confluence.name}"
  policy_arn = "${local.ssm_kms_permissions_policy}"
}
