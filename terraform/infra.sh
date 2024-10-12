#!/usr/bin/env bash

echo "----------------------------------------------------------------------------------"
echo "            Welcome to KedaApp Infra Provisioner !!!"
echo "          This will be deploy the Infra as EKS cluster."
echo "----------------------------------------------------------------------------------"

terraform init > /dev/null

terraform plan > /dev/null

echo "Please wait for 10 minutes as the infra gets provisioned."

terraform apply -auto-approve > /dev/null

echo " Your Infra is ready. Please proceed to deploy the dependencies and application

