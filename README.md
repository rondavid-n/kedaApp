# kedaApp
kedaApp

#Prerequisites
To work with this project, you'll need the following installed:

**Python 3.9+
Docker
Kubernetes (Minikube or any K8s cluster)
Helm
Jenkins
Git
Local Setup**

Clone the repository:

Create a Python virtual environment and install dependencies:

cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Run the app locally:

uvicorn app:app --reload
The app will be available at http://127.0.0.1:8000.

cd frontend
python3 -m http.server 8080  

**Deploying to Kubernetes with Helm**
**1. Build Docker Image**
Before deploying, make sure the Docker image is built and pushed to a container registry (Docker Hub, ECR, etc.).

docker build -t kedaapp/image:latest .
docker push kedappapp/image:latest

**2. Install Helm and Kubernetes Configuration**
Ensure you have a working Kubernetes cluster and Helm installed. Then package and deploy the app using Helm.

**Package the Helm chart:**
helm package kedaapp-helm

**Install the chart on Kubernetes:**

cd Backend/
helm install kedaapp ./charts
This will deploy the app to your Kubernetes cluster.

**CI/CD with Jenkins**
Jenkins Pipeline Overview
The Jenkinsfile automates the process of building, pushing the Docker image, and deploying the app to Kubernetes using Helm. It is designed to be modular, with various stages that handle:

Checkout: Clone the source code from Git.
Build Docker Image: Build the Docker image.
Push Docker Image: Push the image to Docker Hub (or any other registry).
Helm Lint: Check the Helm chart for any errors.
Deploy with Helm: Deploy the app to the Kubernetes cluster using Helm.
Jenkins Pipeline Execution
Set up Jenkins credentials:

Docker registry credentials (e.g., Docker Hub)
Kubernetes credentials (kubeconfig)
Trigger the pipeline manually or set it up to run on Git pushes or pull requests.

The pipeline will deploy the app to the Kubernetes cluster automatically after each successful build.

Helm Chart Details
The KedaApp-helm directory contains a Helm chart for deploying the application to Kubernetes.

Key Files:
deployment.yaml: Defines the Kubernetes deployment resource, which includes the number of replicas, the Docker image, and environment variables.
service.yaml: Defines the service resource to expose the application on a specified port.
values.yaml: Contains default values, such as replica count, image tags, and resource limits.
Helm Commands:
Lint the chart:

cd Backend/
helm lint ./charts
Install/Upgrade the app:

helm upgrade --install KedaApp ./charts --set image.tag=latest
Jenkins Pipeline Explanation
The Jenkinsfile is designed for continuous integration and deployment (CI/CD) of the myapp project.

Stages:
Checkout: Pulls the code from the Git repository.
Build Docker Image: Builds the Docker image using the provided Dockerfile.
Push Docker Image: Pushes the image to the Docker registry.
Helm Lint: Lints the Helm chart to ensure there are no issues.
Deploy with Helm: Deploys or upgrades the application on the Kubernetes cluster using Helm.
Post-Build Actions: Provides notifications or logs success/failure of the deployment.

**Overview of the Code**
This project consists of two main components:

Frontend (index.html): A user interface for managing AWS clusters, Kafka, KEDA deployments, and Kafka topics/consumer groups.
Backend (app.py): A Python-based FastAPI application that interacts with AWS, Kubernetes (EKS), Kafka, and KEDA to perform operations such as cluster management, Kafka deployment, and message production.
Additionally, the application leverages KEDA (Kubernetes Event-Driven Autoscaling) to automatically scale the deployed pods based on the number of Kafka messages in the topics. When a certain threshold is reached, KEDA triggers the autoscaling of pods to handle the increased load.

index.html - Frontend
The index.html file serves as the user interface for managing AWS clusters, Kafka, KEDA, and deploying applications. It includes various sections such as forms for registering clusters, buttons to install Kafka and KEDA, and forms for managing Kafka topics and consumer groups.

**Key Sections:
Cluster Registration: A form for registering AWS clusters with their credentials (AWS Access Key, Secret Key, Cluster Name, and Region).
Connected Clusters: Displays a list of registered clusters. Users can select a cluster to view namespaces, pods, and deployments.
Namespaces and Pods: Dropdowns and tables for selecting a namespace and viewing its pods, along with their status, CPU, and memory usage.
Kafka & KEDA Installation: Buttons to install Kafka and KEDA into the selected cluster.
Kafka Topic and Consumer Group Management: A form to create Kafka topics and consumer groups.
Deployment Management: A form for deploying applications with custom Docker images, resource limits, and Kafka integration (topics and consumer groups).
Kafka Message Producer: A section to produce messages to Kafka topics, where users can specify the number of messages and their content.**


app.py - Backend
The backend is built with FastAPI and integrates several components like AWS, Kubernetes (EKS), Kafka, and KEDA. It provides APIs to manage clusters, install Kafka and KEDA, create Kafka topics, and deploy applications on Kubernetes. Importantly, the backend integrates with KEDA to automatically scale deployed applications based on Kafka message load.

Key Features:
Cluster Registration:

Stores AWS cluster details (Access Key, Secret Key, Cluster Name, Region) in an SQLite database.
Generates a Kubernetes kubeconfig file to interact with the EKS cluster using the AWS SDK (Boto3).
Namespace and Pod Retrieval:

Lists namespaces and pods in a cluster using the Kubernetes Python client.
Fetches pod details like status, CPU, and memory usage.
Kafka & KEDA Installation:

Deploys Kafka and Zookeeper using Kubernetes YAML manifests.
Installs KEDA using Helm.
Kafka Topic Management:

Creates Kafka topics and consumer groups by running commands inside Kafka pods.
Stores Kafka topics and consumer groups in the SQLite database.
Deployment Management:

Deploys applications using Kubernetes with specified Docker images and resource limits (CPU, memory).
Sets up KEDA ScaledObjects for Kafka-based autoscaling.
Allows the deletion of deployments and their associated Kubernetes resources.
Kafka Message Production:

Sends Kafka messages to specified topics using a command executed within the Kafka pod.
KEDA Autoscaling:

KEDA automatically scales the deployed pods based on the number of messages produced in Kafka topics.
When the number of Kafka messages in the topic exceeds a defined threshold, KEDA triggers the autoscaling of the application pods.
As more messages are produced, the application pods scale up to handle the load. When the message count decreases, the number of pods scales back down.

API Endpoints
Cluster Management:

POST /register-cluster: Registers an AWS EKS cluster.
GET /clusters: Retrieves the list of registered clusters.
Kubernetes Operations:

GET /namespaces: Retrieves namespaces for the selected cluster.
GET /pods: Lists pods in a selected namespace.
Kafka & KEDA Installation:

POST /install-kafka/{cluster}: Installs Kafka in the selected cluster.
POST /install-keda/{cluster}: Installs KEDA in the selected cluster.
Kafka Topic & Consumer Group Management:

POST /create-kafka-topic/{cluster}: Creates a Kafka topic and consumer group.
GET /kafka-topics: Retrieves the list of Kafka topics and consumer groups.
Deployment Management:

POST /deploy/{cluster}: Deploys an application with Kafka integration and sets up KEDA autoscaling.
GET /deployments/{cluster}: Retrieves the list of deployments for a cluster.
DELETE /delete-deployment/{cluster_name}/{deployment_name}: Deletes a deployment and its resources.
Kafka Message Production:

POST /send-kafka-messages: Produces messages to a Kafka topic.
Deployment Monitoring:

GET /deployment-details/{cluster_name}/{deployment_name}: Retrieves detailed information about a deployment (e.g., running pods, CPU usage, memory usage, etc.).

KEDA Autoscaling Based on Kafka Messages
Once a deployment is made using the Kafka topic and consumer group specified in the deployment form, KEDA will monitor the Kafka topic. If the number of messages in the topic exceeds a certain threshold (e.g., 10 messages), KEDA will automatically scale the pods of the deployed application to handle the load.

**Scaling Trigger:**

KEDA uses a Kafka trigger to monitor the Kafka topic's message count. If the number of messages in the topic exceeds the lagThreshold, KEDA triggers autoscaling.
Autoscaling Behavior:

If the Kafka topic has more messages than the threshold, KEDA will increase the number of application pods to process the messages faster.
When the message load decreases, KEDA will scale down the pods to reduce resource consumption.
Deployment with KEDA:

When a deployment is created, KEDA's ScaledObject is set up to ensure that the deployment's scaling behavior is tied to Kafka topic activity.
Example: Producing Messages and Scaling Pods
Produce Messages to Kafka:

Using the Kafka message producer form, you can send a batch of messages to the specified Kafka topic.
Enter the topic name, message content, and the number of messages, then click "Send Messages."
KEDA Autoscaling:

As more messages are produced in Kafka, KEDA will detect the increasing load and scale the deployed pods to process the messages.
The pods will automatically scale up to handle the Kafka messages and scale down once the messages are processed.


The Alert mechanism is also inbuilt in the code, if the pod enters crashbackloopoff or in any state other than running or pending, it will alert in the frontend.
