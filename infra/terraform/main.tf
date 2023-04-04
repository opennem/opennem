provider "aws" {
  region = "us-west-2"
}

locals {
  container_image = "ghcr.io/opennem/opennem/opennem"
  container_port  = 80
}

resource "aws_ecs_cluster" "this" {
  name = "opennem-api-cluster"
}

resource "aws_ecs_task_definition" "this" {
  family                   = "opennem-api-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "opennem-api-container"
      image = local.container_image
      portMappings = [
        {
          containerPort = local.container_port
          hostPort      = local.container_port
          protocol      = "tcp"
        }
      ]
    }
  ])
}

resource "aws_security_group" "ecs_tasks_sg" {
  name        = "ecs-tasks-sg"
  description = "Allow inbound traffic to Fargate tasks"
}

resource "aws_security_group_rule" "ecs_tasks_sg_rule" {
  security_group_id = aws_security_group.ecs_tasks_sg.id

  type        = "ingress"
  from_port   = local.container_port
  to_port     = local.container_port
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "opennem-api-vpc"
  }
}

resource "aws_subnet" "this" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "opennem-api-subnet"
  }
}

resource "aws_ecs_service" "this" {
  name            = "opennem-api-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups = [aws_security_group.ecs_tasks_sg.id]
    subnets         = [aws_subnet.this.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "opennem-api-container"
    container_port   = local.container_port
  }
}

resource "aws_lb" "this" {
  name               = "opennem-api-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb_sg.id]
  subnets            = [aws_subnet.this.id]
}

resource "aws_security_group" "lb_sg" {
  name        = "lb-sg"
  description = "Allow inbound traffic to the load balancer"
}

resource "aws_security_group_rule" "lb_sg_rule" {
  security_group_id = aws_security_group.lb_sg.id

  type        = "ingress"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_lb_target_group" "this" {
  name     = "opennem-api-tg"
  port     = local.container_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.this.id

  health_check {
    enabled             = true
    interval            = 30
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    protocol            = "HTTP"
  }
}

resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_api_gateway_rest_api" "this" {
  name        = "opennem-api"
  description = "API Gateway for OpenNEM API"
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = "prod"
}

resource "aws_api_gateway_stage" "this" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.this.id
  deployment_id = aws_api_gateway_deployment.this.id
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.auth0.id
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "${aws_lb_listener.this.arn}/prod/{proxy}"
}

resource "aws_api_gateway_authorizer" "auth0" {
  name            = "auth0"
  rest_api_id     = aws_api_gateway_rest_api.this.id
  type            = "TOKEN"
  identity_source = "method.request.header.Authorization"
  provider_arns   = [var.auth0_issuer]

  authorizer_uri = "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.auth0_authorizer_lambda_arn}/invocations"
}

output "api_gateway_invoke_url" {
  value = "${aws_api_gateway_deployment.this.invoke_url}/prod"
}

variable "certificate_arn" {
  description = "The ARN of the SSL certificate for the load balancer"
}

variable "auth0_issuer" {
  description = "The Auth0 issuer URL"
}

variable "auth0_authorizer_lambda_arn" {
  description = "The ARN of the Auth0 Authorizer Lambda function"
}

variable "region" {
  description = "The AWS region to deploy resources in"
  default     = "us-west-2"
}

# old below

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "all" {
  vpc_id = data.aws_vpc.default.id
}


resource "aws_route53_zone" "opennem" {
  name = "opennem.org.au"
}

resource "aws_route53_zone" "prod" {
  name = "prod.opennem.org.au"

  tags = {
    Environment = "prod"
  }
}

resource "aws_route53_record" "prod-ns" {
  zone_id = aws_route53_zone.opennem.zone_id
  name    = "prod.opennem.org.au"
  type    = "NS"
  ttl     = "30"
  records = aws_route53_zone.prod.name_servers
}

resource "aws_route53_zone" "dev" {
  name = "dev.opennem.org.au"

  tags = {
    Environment = "dev"
  }
}


resource "aws_route53_record" "dev-ns" {
  zone_id = aws_route53_zone.opennem.zone_id
  name    = "dev.opennem.org.au"
  type    = "NS"
  ttl     = "30"
  records = aws_route53_zone.dev.name_servers
}

resource "aws_route53_record" "prod_wildcard" {
  count   = var.instances_number
  zone_id = aws_route53_zone.prod.zone_id
  name    = "*"
  type    = "A"
  ttl     = "60"
  records = [element(aws_eip.docker.*.public_ip, count.index)]
}


resource "aws_route53_record" "dev_wildcard" {
  count   = var.instances_number
  zone_id = aws_route53_zone.dev.zone_id
  name    = "*"
  type    = "CNAME"
  ttl     = "60"
  records = ["docker00.dev.opennem.org.au"]
}

# Existing Resources

# Root certificate

resource "aws_acm_certificate" "core" {
  provider                  = aws.acm_provider
  domain_name               = "opennem.org.au"
  subject_alternative_names = ["*.opennem.org.au"]
  validation_method         = "DNS"
}

resource "aws_acm_certificate_validation" "core_cert_validation" {
  provider                = aws.acm_provider
  certificate_arn         = aws_acm_certificate.core.arn
  validation_record_fqdns = [aws_route53_record.core_cert_validation.fqdn]
}

resource "aws_route53_record" "core_cert_validation" {
  name    = aws_acm_certificate.core.domain_validation_options.0.resource_record_name
  type    = aws_acm_certificate.core.domain_validation_options.0.resource_record_type
  zone_id = aws_route53_zone.opennem.zone_id
  records = [aws_acm_certificate.core.domain_validation_options.0.resource_record_value]
  ttl     = 60
}
