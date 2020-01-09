# This is an example Terraform script to deploy a GCP service account, create a service account access key,
# and store the service account access key in AWS Secretsmanager.
#
# The service account access key can be rotated by issuing the commands:
#  1. `terraform destroy -target=null_resource.gcp-service-account-key`
#  2. `terraform apply -target=null_resource.gcp-service-account-key`

data "google_project" "project" {}


resource "google_service_account" "deployer" {
  display_name =  var.GCP_SERVICE_ACCOUNT_NAME
  account_id =  var.GCP_SERVICE_ACCOUNT_NAME
}

# Useful command to discover role names (Guessing based on console titles is difficult):
# `gcloud iam list-grantable-roles //cloudresourcemanager.googleapis.com/projects/{project-id}`

resource "google_project_iam_member" "viewer" {
  project =  data.google_project.project.project_id
  role = "roles/viewer"
  member = "serviceAccount:${google_service_account.deployer.email}"
}

resource "aws_secretsmanager_secret" "gcp-service-account-key" {
  name =  var.GCP_SERVICE_ACCOUNT_KEY_SECRET_ID
  tags = {
    project = "dcp"
    env =  var.FUS_DEPLOYMENT_STAGE
    owner =  var.FUS_OWNER_TAG
    service = "fusillade"
    Name =  var.GCP_SERVICE_ACCOUNT_KEY_SECRET_ID
    managedBy = "Terraform"
  }
}

resource "null_resource" "gcp-service-account-key" {
  provisioner "local-exec" {
    command = "gcloud iam service-accounts keys create --iam-account=${google_service_account.deployer.email} ${path.cwd}/gcp-credentials.json"
  }
  provisioner "local-exec" {
    command = "aws secretsmanager put-secret-value --secret-id ${aws_secretsmanager_secret.gcp-service-account-key.name} --secret-string file://${path.cwd}/gcp-credentials.json"
  }
  provisioner "local-exec" {
    when = "destroy"
    command = "gcloud iam service-accounts keys delete --iam-account=${google_service_account.deployer.email} $(aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.gcp-service-account-key.name} | jq -r .SecretString | jq -r .private_key_id)"
  }
}

output "service_account" {
  value =  var.GCP_SERVICE_ACCOUNT_NAME
}