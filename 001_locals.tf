locals {
  path = "/create_product_jira_confluence/"

  path_lambdas = "${format("%s/lambdas", path.module)}"

  path_policies = "${format("%s/policies", path.module)}"

  basic_lambda_policy        = "${aws_iam_policy.lambda_basic.arn}"
  ssm_kms_permissions_policy = "${aws_iam_policy.ssm_kms_permissions.arn}"
}

resource "aws_iam_policy" "lambda_basic" {
  name   = "${format("%s-basic-lambda", var.tags["project"])}"
  path   = "${local.path}"
  policy = "${data.template_file.basic_lambda_policy.rendered}"
}

data "template_file" "basic_lambda_policy" {
  template = "${file(format("%s/basic_lambda.json", local.path_policies))}"
}

resource "aws_iam_policy" "ssm_kms_permissions" {
  name   = "${format("%s-ssm_kms_permissions", var.tags["project"])}"
  path   = "${local.path}"
  policy = "${data.template_file.ssm_kms_permissions_policy.rendered}"
}

data "template_file" "ssm_kms_permissions_policy" {
  template = "${file(format("%s/ssm_kms_permissions.json", local.path_policies))}"
}

data "aws_lambda_layer_version" "requests_lambda_layer" {
  layer_name = "requests"
}
