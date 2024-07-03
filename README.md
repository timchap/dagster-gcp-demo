# dagster-gcp-demo

This repository contains supporting resources to run a full end-to-end demo of the [terraform-google-managed-dagster](https://github.com/timchap/terraform-google-managed-dagster) 
module. This module defines a Dagster deployment which is nearly fully managed/serverless, with the exception of a
lightweight Compute Engine instance running the Dagster daemon and the Cloud SQL database.

# Prerequisites
- A Google Cloud Platform project with the following APIs enabled:
  - Cloud SQL
  - Cloud Storage
  - Cloud Run
  - Identity and Access Management (IAM)
  - Secret Manager
  - Compute Engine
- An existing Google Cloud Artifact Registry repository for Docker images
- A VPC and serverless VPC connector
- A Cloud SQL instance on the above VPC (database will be created by the module)
- Service-to-service private networking enabled for Cloud Run (see [documentation](https://cloud.google.com/run/docs/securing/private-networking#from-other-services))

# Steps to deploy the demo
1. Clone this repository
2. Build and push each of the following Docker images to your Artifact Registry repository:
   - `webserver_and_daemon`: This image contains core dagster dependencies (`dagster`, `dagster-webserver`, libraries, 
     etc.). It will be deployed as a Cloud Run webserver and a Compute Engine daemon.
   - `code_location_a`: This image contains the code for the first code server. It will be deployed as a Cloud Run 
     (services) code server, and a Cloud Run (jobs) run worker.
   - `code_location_b`: This image contains the code for the second code server. Notably, this image demonstrates how
     different code servers can run different Python environments.
3. Create a new terraform configuration repository. In your `main.tf`, define your Dagster deployment according to the
   following template:

```hcl
locals {
  gcr_region = "us"
  registry_project = "my-registry-project"
  repository_name = "dagster-gcp-demo"  # An existing Artifact Registry repository with the required images
}

module "main" {
  source = "../"

  code_locations = {
    a = {
      image = "${local.gcr_region}-docker.pkg.dev/${local.registry_project}/${local.repository_name}/dagster-code-location-a:latest"
      run_worker_resources_limits = {
        cpu    = "1"
        memory = "1Gi"
      }
      module_name = "definitions"
      port        = 3000
    }
    b = {
      image = "${local.gcr_region}-docker.pkg.dev/${local.registry_project}/${local.repository_name}/dagster-code-location-b:latest"
      run_worker_resources_limits = {
        cpu    = "1"
        memory = "1Gi"
      }
      module_name = "definitions"
      port        = 3000
    }
  }
  io_bucket       = "my-io-bucket"
  log_bucket      = "my-log-bucket"
  project         = "my-project"  # An existing GCP project
  region          = "us-west1"
  daemon_zone     = "us-west1-a"
  daemon_image    = "${local.gcr_region}-docker.pkg.dev/${local.registry_project}/${local.repository_name}/dagster-webserver-and-daemon"
  webserver_image = "${local.gcr_region}-docker.pkg.dev/${local.registry_project}/${local.repository_name}/dagster-webserver-and-daemon"
  webserver_ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  db_instance_name       = "my-db-instance"  # An existing Cloud SQL instance
  db_instance_private_ip = "10.12.34.56"

  network          = "projects/my-project/global/networks/my-vpc"
  subnetwork       = "projects/my-project/regions/us-west1/subnetworks/my-subnet"
  vpc_connector_id = "projects/my-project/locations/us-west1/connectors/my-vpc-connector"
}
```

4. Apply the terraform configuration.

# Final steps
At this point, the following components have been deployed:
- A Cloud Run webserver
- The dagster daemon running on a Compute Engine instance
- Two code servers running as Cloud Run services
- Two run workers ready as Cloud Run jobs
- A Cloud SQL database with the necessary schema (applied during the first startup of the webserver)
- Buckets for storage and logs

However, in the current state the webserver is deployed to the VPC and requires IAM-authenticated requests. To grant
access to authenticated users, you must [enable Identity-Aware Proxy (IAP) on the Cloud Run service](https://cloud.google.com/iap/docs/enabling-cloud-run#:~:text=To%20allow%20IAP%20to%20access,X%2DServerless%2DAuthorization%20header.).
Note that this can be partially terraformed, but requires some manual configuration via the console due to API 
limitations.

Alternatively, for a proof-of-concept or development environment, you may wish to expose the webserver to the public
internet. This can be done by:
- Changing the `webserver_ingress` parameter to `INGRESS_TRAFFIC_ALLOWED`
- Adding a `google_cloud_run_v2_service_iam_member` resource to grant the `roles/run.invoker` role to the `allUsers`
  group

# Notes
- The images defined by this repository currently define the `dagster-gcp` dependency based on [this fork](https://github.com/timchap/dagster/tree/feat/cloud-run-run-launcher/python_modules/libraries/dagster-gcp).
  This is because this deployment requires the CloudRunRunWorker, which is not yet merged into the Dagster trunk at 
  time of writing.
- Note that the two different code locations (`a` and `b`) define dummy assets which return the version of the 
  `requests` library. This is simply to demonstrate that different code servers can use different Python environments.
- The daemon image in particular requires an entrypoint wrapper before the `dagster-daemon run` command. This is 
  because Compute Engine (unlike Cloud Run) does not provide a way to inject secrets from Secret Manager. Instead, we
  explicitly fetch the secret on container startup.