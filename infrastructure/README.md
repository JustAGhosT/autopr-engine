# Infrastructure as Code

This directory contains the Infrastructure as Code (IaC) for the AutoPR project, defining the necessary Azure resources to run the application in a production environment.

## Options

We provide two options for deploying the infrastructure:

1.  **Terraform:** Located in the `terraform` directory, this is the default and recommended option. Terraform is a cloud-agnostic tool that is widely used in the industry.
2.  **Bicep:** Located in the `bicep` directory, this is an alternative for users who prefer a native Azure IaC experience.

## Usage

### Terraform

To deploy the infrastructure using Terraform, navigate to the `terraform` directory and run the following commands:

```bash
terraform init
terraform plan
terraform apply
```

### Bicep

To deploy the infrastructure using Bicep, you will need the Azure CLI. Run the following command from the root of the repository:

```bash
az deployment sub create --location eastus --template-file infrastructure/bicep/main.bicep
```
