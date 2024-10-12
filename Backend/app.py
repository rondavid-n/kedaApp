# import os
# import yaml
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import sqlite3
# import boto3
# from kubernetes import client, config

# app = FastAPI()

# # Enable CORS to allow requests from different origins (like localhost:8080 for frontend)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins (for development)
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all methods
#     allow_headers=["*"],  # Allow all headers
# )

# # Ensure the database and table are created when the application starts
# def init_db():
#     conn = sqlite3.connect('clusters.db')
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS clusters (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             access_key TEXT NOT NULL,
#             secret_key TEXT NOT NULL,
#             cluster_name TEXT NOT NULL UNIQUE,
#             region TEXT NOT NULL
#         )
#     """)
#     conn.commit()
#     conn.close()

# # Call the init_db function to create the table if it doesn't exist
# init_db()

# # SQLite database connection function
# def get_db_connection():
#     conn = sqlite3.connect('clusters.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # AWS Credentials model for accepting input data
# class ClusterData(BaseModel):
#     access_key: str
#     secret_key: str
#     cluster_name: str
#     region: str

# def create_eks_kubeconfig(cluster_name: str, region: str, access_key: str, secret_key: str) -> str:
#     """Generate a kubeconfig file for the given AWS EKS cluster and save it locally."""
    
#     session = boto3.Session(
#         aws_access_key_id=access_key,
#         aws_secret_access_key=secret_key,
#         region_name=region
#     )
    
#     eks_client = session.client('eks')
    
#     # Retrieve the cluster information
#     cluster_info = eks_client.describe_cluster(name=cluster_name)['cluster']
    
#     # Prepare API server and certificate
#     api_server = cluster_info['endpoint']
#     certificate = cluster_info['certificateAuthority']['data']
    
#     # Generate kubeconfig content
#     kubeconfig = {
#         "apiVersion": "v1",
#         "kind": "Config",
#         "clusters": [
#             {
#                 "name": "kubernetes",
#                 "cluster": {
#                     "certificate-authority-data": certificate,
#                     "server": api_server
#                 }
#             }
#         ],
#         "users": [
#             {
#                 "name": "aws",
#                 "user": {
#                     "exec": {
#                         "apiVersion": "client.authentication.k8s.io/v1beta1",
#                         "command": "aws",
#                         "args": [
#                             "eks",
#                             "get-token",
#                             "--cluster-name",
#                             cluster_name,
#                             "--region",
#                             region
#                         ]
#                     }
#                 }
#             }
#         ],
#         "contexts": [
#             {
#                 "name": "aws",
#                 "context": {
#                     "cluster": "kubernetes",
#                     "user": "aws"
#                 }
#             }
#         ],
#         "current-context": "aws"
#     }

#     # Define the path to save the kubeconfig file
#     kubeconfig_file = f"./{cluster_name}-kubeconfig.yaml"

#     # Save the kubeconfig file locally
#     with open(kubeconfig_file, "w") as f:
#         yaml.dump(kubeconfig, f)
    
#     print(f"Kubeconfig for cluster {cluster_name} saved as {kubeconfig_file}")
#     return kubeconfig_file

# # API to register a cluster
# @app.post('/register-cluster')
# async def register_cluster(data: ClusterData):
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Store credentials and cluster info in the database
#     try:
#         cursor.execute(
#             "INSERT INTO clusters (access_key, secret_key, cluster_name, region) VALUES (?, ?, ?, ?)", 
#             (data.access_key, data.secret_key, data.cluster_name, data.region)
#         )
#         conn.commit()
#     except sqlite3.IntegrityError:
#         return {"error": "Cluster already registered"}
#     finally:
#         conn.close()

#     return {"message": "Cluster registered successfully"}

# # API to fetch registered clusters
# @app.get('/clusters')
# async def get_clusters():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Fetch cluster names from the database
#     clusters = cursor.execute("SELECT cluster_name FROM clusters").fetchall()
#     conn.close()
    
#     return [row['cluster_name'] for row in clusters]

# # API to get namespaces in a cluster using kubeconfig from file
# @app.get('/namespaces')
# async def get_namespaces(cluster: str):
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Fetch the cluster credentials and region from the database
#     cluster_data = cursor.execute(
#         "SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)
#     ).fetchone()
#     conn.close()

#     if not cluster_data:
#         return {"error": "Cluster not found"}

#     # Create kubeconfig and save it to file
#     kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])

#     # Load the kubeconfig from file
#     config.load_kube_config(config_file=kubeconfig_file)

#     # Use Kubernetes client to list namespaces
#     v1 = client.CoreV1Api()
#     namespaces = v1.list_namespace().items

#     namespace_list = [ns.metadata.name for ns in namespaces]
#     return {"namespaces": namespace_list}

# # API to get pods in a cluster
# @app.get('/pods')
# async def get_pods(cluster: str, namespace: str = "all"):
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Fetch the cluster credentials and region from the database
#     cluster_data = cursor.execute(
#         "SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)
#     ).fetchone()
#     conn.close()

#     if not cluster_data:
#         return {"error": "Cluster not found"}

#     # Create kubeconfig and save it to file
#     kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])

#     # Load the kubeconfig from file
#     config.load_kube_config(config_file=kubeconfig_file)

#     # Use Kubernetes client to access the cluster
#     v1 = client.CoreV1Api()

#     # Fetch pods from the specified namespace or from all namespaces
#     if namespace == "all":
#         pods = v1.list_pod_for_all_namespaces(watch=False)
#     else:
#         pods = v1.list_namespaced_pod(namespace=namespace, watch=False)

#     # Gather pod details including CPU and memory usage
#     pod_list = []
#     for pod in pods.items:
#         container = pod.spec.containers[0]
#         resources = container.resources

#         # Check if resource requests exist, otherwise set to 'Unknown'
#         cpu = resources.requests.get('cpu', 'Unknown') if resources and resources.requests else 'Unknown'
#         memory = resources.requests.get('memory', 'Unknown') if resources and resources.requests else 'Unknown'

#         pod_list.append({
#             "name": pod.metadata.name,
#             "cpu": cpu,
#             "memory": memory
#         })

#     return pod_list

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)



# import os
# import yaml
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import sqlite3
# import boto3
# from kubernetes import client, config
# import subprocess

# app = FastAPI()

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all methods
#     allow_headers=["*"],  # Allow all headers
# )

# # Ensure the database and table are created when the application starts
# def init_db():
#     conn = sqlite3.connect('clusters.db')
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS clusters (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             access_key TEXT NOT NULL,
#             secret_key TEXT NOT NULL,
#             cluster_name TEXT NOT NULL UNIQUE,
#             region TEXT NOT NULL
#         )
#     """)
#     conn.commit()
#     conn.close()

# # Call the init_db function to create the table if it doesn't exist
# init_db()

# # SQLite database connection function
# def get_db_connection():
#     conn = sqlite3.connect('clusters.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # Model to capture cluster registration details
# class ClusterData(BaseModel):
#     access_key: str
#     secret_key: str
#     cluster_name: str
#     region: str

# # Generate kubeconfig for EKS
# def create_eks_kubeconfig(cluster_name: str, region: str, access_key: str, secret_key: str) -> str:
#     """Generate a kubeconfig file for the given AWS EKS cluster and save it locally."""
    
#     session = boto3.Session(
#         aws_access_key_id=access_key,
#         aws_secret_access_key=secret_key,
#         region_name=region
#     )
    
#     eks_client = session.client('eks')
#     cluster_info = eks_client.describe_cluster(name=cluster_name)['cluster']
#     api_server = cluster_info['endpoint']
#     certificate = cluster_info['certificateAuthority']['data']
    
#     kubeconfig = {
#         "apiVersion": "v1",
#         "kind": "Config",
#         "clusters": [
#             {
#                 "name": "kubernetes",
#                 "cluster": {
#                     "certificate-authority-data": certificate,
#                     "server": api_server
#                 }
#             }
#         ],
#         "users": [
#             {
#                 "name": "aws",
#                 "user": {
#                     "exec": {
#                         "apiVersion": "client.authentication.k8s.io/v1beta1",
#                         "command": "aws",
#                         "args": [
#                             "eks",
#                             "get-token",
#                             "--cluster-name",
#                             cluster_name,
#                             "--region",
#                             region
#                         ]
#                     }
#                 }
#             }
#         ],
#         "contexts": [
#             {
#                 "name": "aws",
#                 "context": {
#                     "cluster": "kubernetes",
#                     "user": "aws"
#                 }
#             }
#         ],
#         "current-context": "aws"
#     }

#     kubeconfig_file = f"./{cluster_name}-kubeconfig.yaml"
#     with open(kubeconfig_file, "w") as f:
#         yaml.dump(kubeconfig, f)
    
#     return kubeconfig_file

# # API to register a cluster
# @app.post('/register-cluster')
# async def register_cluster(data: ClusterData):
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     try:
#         cursor.execute(
#             "INSERT INTO clusters (access_key, secret_key, cluster_name, region) VALUES (?, ?, ?, ?)", 
#             (data.access_key, data.secret_key, data.cluster_name, data.region)
#         )
#         conn.commit()
#     except sqlite3.IntegrityError:
#         return {"error": "Cluster already registered"}
#     finally:
#         conn.close()

#     return {"message": "Cluster registered successfully"}

# # API to fetch registered clusters
# @app.get('/clusters')
# async def get_clusters():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     clusters = cursor.execute("SELECT cluster_name FROM clusters").fetchall()
#     conn.close()
    
#     return [row['cluster_name'] for row in clusters]

# # API to fetch namespaces for a specific cluster
# @app.get('/namespaces')
# async def get_namespaces(cluster: str = Query(...)):
#     # Fetch the cluster details from the database
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
#     conn.close()

#     if not cluster_data:
#         raise HTTPException(status_code=404, detail="Cluster not found")

#     # Create kubeconfig for the cluster
#     kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
#     os.environ["KUBECONFIG"] = kubeconfig_file

#     try:
#         # Load Kubernetes configuration from the generated kubeconfig file
#         config.load_kube_config(config_file=kubeconfig_file)
#         v1 = client.CoreV1Api()

#         # List namespaces in the cluster
#         namespaces = v1.list_namespace().items
#         namespace_names = [namespace.metadata.name for namespace in namespaces]

#         return {"namespaces": namespace_names}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve namespaces: {str(e)}")

# @app.get('/pods')
# async def get_pods(cluster: str, namespace: str = 'default'):
#     # Fetch the cluster details from the database
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
#     conn.close()

#     if not cluster_data:
#         raise HTTPException(status_code=404, detail="Cluster not found")

#     # Create kubeconfig for the cluster
#     kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
#     os.environ["KUBECONFIG"] = kubeconfig_file

#     try:
#         # Load Kubernetes configuration from the generated kubeconfig file
#         config.load_kube_config(config_file=kubeconfig_file)
#         v1 = client.CoreV1Api()

#         # Check if namespace is 'all', list all pods in all namespaces
#         if namespace == 'all':
#             pods = v1.list_pod_for_all_namespaces().items
#         else:
#             pods = v1.list_namespaced_pod(namespace).items

#         # Parse the pod data
#         pod_list = []
#         for pod in pods:
#             pod_info = {
#                 "name": pod.metadata.name,
#                 "status": pod.status.phase,
#                 "cpu": pod.spec.containers[0].resources.requests.get('cpu') if pod.spec.containers[0].resources.requests else "N/A",
#                 "memory": pod.spec.containers[0].resources.requests.get('memory') if pod.spec.containers[0].resources.requests else "N/A",
#             }
#             pod_list.append(pod_info)

#         # Return pods in the specified namespace
#         return {"pods": pod_list}
#     except client.exceptions.ApiException as e:
#         # Catch API exceptions from Kubernetes client and return as HTTP error
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve pods: {e.reason}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve pods: {str(e)}")

    
# # API to install KEDA via Helm
# @app.post('/install-keda/{cluster}')
# async def install_keda(cluster: str):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
#     conn.close()

#     if not cluster_data:
#         raise HTTPException(status_code=404, detail="Cluster not found")

#     kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
#     os.environ["KUBECONFIG"] = kubeconfig_file

#     keda_installed = subprocess.run(["helm", "list", "-n", "keda"], capture_output=True, text=True)
#     if "keda" in keda_installed.stdout:
#         return {"message": "KEDA is already installed"}

#     install_command = ["helm", "install", "keda", "kedacore/keda", "--namespace", "keda", "--create-namespace"]
#     result = subprocess.run(install_command, capture_output=True, text=True)

#     if result.returncode == 0:
#         return {"message": "KEDA installed successfully"}
#     else:
#         return {"error": "Failed to install KEDA", "details": result.stderr}


# # Run the FastAPI application using uvicorn
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import yaml
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import boto3
from kubernetes import client, config
import subprocess
import time
import subprocess
from kubernetes.client import CustomObjectsApi



app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the database and table are created when the application starts
def init_db():
    conn = sqlite3.connect('clusters.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_key TEXT NOT NULL,
            secret_key TEXT NOT NULL,
            cluster_name TEXT NOT NULL UNIQUE,
            region TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_name TEXT NOT NULL,
            deployment_name TEXT NOT NULL UNIQUE,
            service_name TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kafka_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            consumer_group_name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call init_db during startup
@app.on_event("startup")
def on_startup():
    init_db()

# SQLite database connection function
def get_db_connection():
    conn = sqlite3.connect('clusters.db')
    conn.row_factory = sqlite3.Row
    return conn

# Model to capture cluster registration details
class ClusterData(BaseModel):
    access_key: str
    secret_key: str
    cluster_name: str
    region: str

class KafkaMessageRequest(BaseModel):
    topic_name: str
    message: str
    message_count: int

# Model to capture Kafka topic and consumer group details
class KafkaTopicRequest(BaseModel):
    topic_name: str
    consumer_group_name: str

# Model to capture deployment details
class DeploymentData(BaseModel):
    deployment_name: str
    docker_image: str
    docker_tag: str
    cpu_requests: str
    memory_requests: str
    cpu_limits: str
    memory_limits: str
    ports: list[int]
    target_ports: list[int]
    kafka_topic: str
    consumer_group_name: str


# Generate kubeconfig for EKS
def create_eks_kubeconfig(cluster_name: str, region: str, access_key: str, secret_key: str) -> str:
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        eks_client = session.client('eks')
        cluster_info = eks_client.describe_cluster(name=cluster_name)['cluster']
        api_server = cluster_info['endpoint']
        certificate = cluster_info['certificateAuthority']['data']

        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "kubernetes",
                    "cluster": {
                        "certificate-authority-data": certificate,
                        "server": api_server
                    }
                }
            ],
            "users": [
                {
                    "name": "aws",
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1beta1",
                            "command": "aws",
                            "args": [
                                "eks",
                                "get-token",
                                "--cluster-name",
                                cluster_name,
                                "--region",
                                region
                            ]
                        }
                    }
                }
            ],
            "contexts": [
                {
                    "name": "aws",
                    "context": {
                        "cluster": "kubernetes",
                        "user": "aws"
                    }
                }
            ],
            "current-context": "aws"
        }

        kubeconfig_file = f"./{cluster_name}-kubeconfig.yaml"
        with open(kubeconfig_file, "w") as f:
            yaml.dump(kubeconfig, f)

        return kubeconfig_file
    except Exception as e:
        logger.error(f"Failed to generate kubeconfig: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate kubeconfig: {str(e)}")

# API to register a cluster
@app.post('/register-cluster')
async def register_cluster(data: ClusterData):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO clusters (access_key, secret_key, cluster_name, region) VALUES (?, ?, ?, ?)", 
            (data.access_key, data.secret_key, data.cluster_name, data.region)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return {"error": "Cluster already registered"}
    finally:
        conn.close()

    return {"message": "Cluster registered successfully"}

# API to fetch registered clusters
@app.get('/clusters')
async def get_clusters():
    conn = get_db_connection()
    cursor = conn.cursor()

    clusters = cursor.execute("SELECT cluster_name FROM clusters").fetchall()
    conn.close()

    return [row['cluster_name'] for row in clusters]

# API to fetch namespaces for a specific cluster
@app.get('/namespaces')
async def get_namespaces(cluster: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
    conn.close()

    if not cluster_data:
        raise HTTPException(status_code=404, detail="Cluster not found")

    kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
    os.environ["KUBECONFIG"] = kubeconfig_file

    try:
        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()

        namespaces = v1.list_namespace().items
        namespace_names = [namespace.metadata.name for namespace in namespaces]

        return {"namespaces": namespace_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve namespaces: {str(e)}")

# API to fetch pods in a specific cluster and namespace
@app.get('/pods')
async def get_pods(cluster: str, namespace: str = 'default'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
    conn.close()

    if not cluster_data:
        raise HTTPException(status_code=404, detail="Cluster not found")

    kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
    os.environ["KUBECONFIG"] = kubeconfig_file

    try:
        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()

        # Fetch the pods based on the selected namespace
        if namespace.lower() == 'all':
            pods = v1.list_pod_for_all_namespaces().items
        else:
            pods = v1.list_namespaced_pod(namespace).items

        pod_list = []
        for pod in pods:
            container_statuses = pod.status.container_statuses or []
            pod_status = pod.status.phase  # Get the general pod status
            if container_statuses:
                for container_status in container_statuses:
                    if container_status.state.waiting and container_status.state.waiting.reason:
                        pod_status = container_status.state.waiting.reason  # e.g., CrashLoopBackOff, ErrImagePull
                    elif container_status.state.terminated and container_status.state.terminated.reason:
                        pod_status = container_status.state.terminated.reason  # e.g., Error, Terminated
                    elif container_status.state.running:
                        pod_status = "Running"  # Pod is running
                    else:
                        pod_status = pod.status.phase  # Pending, Succeeded, etc.

            # Safely retrieve CPU and memory requests, handling cases where they're undefined
            cpu_request = 'N/A'
            memory_request = 'N/A'
            if pod.spec.containers and pod.spec.containers[0].resources and pod.spec.containers[0].resources.requests:
                cpu_request = pod.spec.containers[0].resources.requests.get('cpu', 'N/A')
                memory_request = pod.spec.containers[0].resources.requests.get('memory', 'N/A')

            pod_list.append({
                "name": pod.metadata.name,
                "status": pod_status,
                "cpu": cpu_request,
                "memory": memory_request
            })

        return {"pods": pod_list}

    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pods: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pods: {str(e)}")




# API to install Kafka with one replica in the cluster
@app.post('/install-kafka/{cluster}')
async def install_kafka(cluster: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
    conn.close()

    if not cluster_data:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Generate kubeconfig for the cluster
    kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
    os.environ["KUBECONFIG"] = kubeconfig_file

    # Check if Zookeeper is already installed
    zookeeper_installed = subprocess.run(["kubectl", "get", "statefulset", "zk", "-n", "default"], capture_output=True, text=True)
    if "zk" in zookeeper_installed.stdout:
        zookeeper_status = subprocess.run(["kubectl", "get", "pods", "-l", "app=zk", "-n", "default", "-o", "json"], capture_output=True, text=True)
        zookeeper_info = zookeeper_status.stdout
        return {"message": "Kafka & Zookeeper are already installed", "details": zookeeper_info}

    # Check if Kafka is already installed
    kafka_installed = subprocess.run(["kubectl", "get", "statefulset", "kafka", "-n", "default"], capture_output=True, text=True)
    if "kafka" in kafka_installed.stdout:
        kafka_status = subprocess.run(["kubectl", "get", "pods", "-l", "app=kafka", "-n", "default", "-o", "json"], capture_output=True, text=True)
        kafka_info = kafka_status.stdout
        return {"message": "Kafka is already installed", "details": kafka_info}

    # Install Zookeeper if not already installed
    zookeeper_yaml = """
apiVersion: v1
kind: Service
metadata:
  name: zk-hs
  labels:
    app: zk
spec:
  ports:
  - port: 2888
    name: server
  - port: 3888
    name: leader-election
  clusterIP: None
  selector:
    app: zk
---
apiVersion: v1
kind: Service
metadata:
  name: zk-cs
  labels:
    app: zk
spec:
  ports:
  - port: 2181
    name: client
  selector:
    app: zk
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: zk
spec:
  selector:
    matchLabels:
      app: zk
  serviceName: zk-hs
  replicas: 3
  updateStrategy:
    type: RollingUpdate
  podManagementPolicy: Parallel
  template:
    metadata:
      labels:
        app: zk
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: "app"
                    operator: In
                    values:
                    - zk
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: kubernetes-zookeeper
        imagePullPolicy: Always
        image: "gcr.io/google_containers/kubernetes-zookeeper:1.0-3.4.10"
        resources:
          requests:
            memory: "1Gi"
            cpu: "0.5"
        ports:
        - containerPort: 2181
          name: client
        - containerPort: 2888
          name: server
        - containerPort: 3888
          name: leader-election
        command:
        - sh
        - -c
        - "start-zookeeper \
          --servers=3 \
          --data_dir=/var/lib/zookeeper/data \
          --data_log_dir=/var/lib/zookeeper/data/log \
          --conf_dir=/opt/zookeeper/conf \
          --client_port=2181 \
          --election_port=3888 \
          --server_port=2888 \
          --tick_time=2000 \
          --init_limit=10 \
          --sync_limit=5 \
          --heap=512M \
          --max_client_cnxns=60 \
          --snap_retain_count=3 \
          --purge_interval=12 \
          --max_session_timeout=40000 \
          --min_session_timeout=4000 \
          --log_level=INFO"
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "zookeeper-ready 2181"
          initialDelaySeconds: 10
          timeoutSeconds: 5
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "zookeeper-ready 2181"
          initialDelaySeconds: 10
          timeoutSeconds: 5
        volumeMounts:
        - name: datadir
          mountPath: /var/lib/zookeeper
      securityContext:
        runAsUser: 1000
        fsGroup: 1000
      volumes: 
      - name: datadir
        emptyDir: {}
    """

    zookeeper_deployment_file = "/tmp/zookeeper-deployment.yaml"
    with open(zookeeper_deployment_file, "w") as f:
        f.write(zookeeper_yaml)

    try:
        zookeeper_result = subprocess.run(["kubectl", "apply", "-f", zookeeper_deployment_file], check=True, capture_output=True, text=True)
        logger.info(f"Zookeeper apply output: {zookeeper_result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl apply for Zookeeper: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Failed to apply Zookeeper deployment: {e.stderr}")

    # Install Kafka after Zookeeper is successfully deployed
    kafka_yaml = """
apiVersion: v1
kind: Service
metadata:
  name: kafka-hs
  labels:
    app: kafka
spec:
  ports:
  - port: 9093
    name: server
  clusterIP: None
  selector:
    app: kafka
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  selector:
    matchLabels:
      app: kafka
  serviceName: kafka-hs
  replicas: 1
  updateStrategy:
    type: RollingUpdate
  podManagementPolicy: Parallel
  template:
    metadata:
      labels:
        app: kafka
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: "app"
                    operator: In
                    values:
                    - kafka
              topologyKey: "kubernetes.io/hostname"
      terminationGracePeriodSeconds: 300
      containers:
      - name: k8skafka
        imagePullPolicy: Always
        image: gcr.io/google_containers/kubernetes-kafka:1.0-10.2.1
        resources:
          requests:
            memory: "1Gi"
            cpu: "0.5"
        ports:
        - containerPort: 9093
          name: server
        command:
        - sh
        - -c
        - "exec kafka-server-start.sh /opt/kafka/config/server.properties --override broker.id=${HOSTNAME##*-} \
          --override listeners=PLAINTEXT://:9093 \
          --override zookeeper.connect=zk-cs.default.svc.cluster.local:2181 \
          --override log.dir=/var/lib/kafka \
          --override auto.create.topics.enable=true \
          --override auto.leader.rebalance.enable=true \
          --override background.threads=10 \
          --override compression.type=producer \
          --override delete.topic.enable=false \
          --override leader.imbalance.check.interval.seconds=300 \
          --override leader.imbalance.per.broker.percentage=10 \
          --override log.flush.interval.messages=9223372036854775807 \
          --override log.flush.offset.checkpoint.interval.ms=60000 \
          --override log.flush.scheduler.interval.ms=9223372036854775807 \
          --override log.retention.bytes=-1 \
          --override log.retention.hours=168 \
          --override log.roll.hours=168 \
          --override log.roll.jitter.hours=0 \
          --override log.segment.bytes=1073741824 \
          --override log.segment.delete.delay.ms=60000 \
          --override message.max.bytes=1000012 \
          --override min.insync.replicas=1 \
          --override num.io.threads=8 \
          --override num.network.threads=3 \
          --override num.recovery.threads.per.data.dir=1 \
          --override num.replica.fetchers=1 \
          --override offset.metadata.max.bytes=4096 \
          --override offsets.commit.required.acks=-1 \
          --override offsets.commit.timeout.ms=5000 \
          --override offsets.load.buffer.size=5242880 \
          --override offsets.retention.check.interval.ms=600000 \
          --override offsets.retention.minutes=1440 \
          --override offsets.topic.compression.codec=0 \
          --override offsets.topic.num.partitions=50 \
          --override offsets.topic.replication.factor=3 \
          --override offsets.topic.segment.bytes=104857600 \
          --override queued.max.requests=500 \
          --override quota.consumer.default=9223372036854775807 \
          --override quota.producer.default=9223372036854775807 \
          --override replica.fetch.min.bytes=1 \
          --override replica.fetch.wait.max.ms=500 \
          --override replica.high.watermark.checkpoint.interval.ms=5000 \
          --override replica.lag.time.max.ms=10000 \
          --override replica.socket.receive.buffer.bytes=65536 \
          --override replica.socket.timeout.ms=30000 \
          --override request.timeout.ms=30000 \
          --override socket.receive.buffer.bytes=102400 \
          --override socket.request.max.bytes=104857600 \
          --override socket.send.buffer.bytes=102400 \
          --override unclean.leader.election.enable=true \
          --override zookeeper.session.timeout.ms=6000 \
          --override zookeeper.set.acl=false \
          --override broker.id.generation.enable=true \
          --override connections.max.idle.ms=600000 \
          --override controlled.shutdown.enable=true \
          --override controlled.shutdown.max.retries=3 \
          --override controlled.shutdown.retry.backoff.ms=5000 \
          --override controller.socket.timeout.ms=30000 \
          --override default.replication.factor=1 \
          --override fetch.purgatory.purge.interval.requests=1000 \
          --override group.max.session.timeout.ms=300000 \
          --override group.min.session.timeout.ms=6000 \
          --override inter.broker.protocol.version=0.10.2-IV0 \
          --override log.cleaner.backoff.ms=15000 \
          --override log.cleaner.dedupe.buffer.size=134217728 \
          --override log.cleaner.delete.retention.ms=86400000 \
          --override log.cleaner.enable=true \
          --override log.cleaner.io.buffer.load.factor=0.9 \
          --override log.cleaner.io.buffer.size=524288 \
          --override log.cleaner.io.max.bytes.per.second=1.7976931348623157E308 \
          --override log.cleaner.min.cleanable.ratio=0.5 \
          --override log.cleaner.min.compaction.lag.ms=0 \
          --override log.cleaner.threads=1 \
          --override log.cleanup.policy=delete \
          --override log.index.interval.bytes=4096 \
          --override log.index.size.max.bytes=10485760 \
          --override log.message.timestamp.difference.max.ms=9223372036854775807 \
          --override log.message.timestamp.type=CreateTime \
          --override log.preallocate=false \
          --override log.retention.check.interval.ms=300000 \
          --override max.connections.per.ip=2147483647 \
          --override num.partitions=1 \
          --override producer.purgatory.purge.interval.requests=1000 \
          --override replica.fetch.backoff.ms=1000 \
          --override replica.fetch.max.bytes=1048576 \
          --override replica.fetch.response.max.bytes=10485760 \
          --override reserved.broker.max.id=1000 "
        env:
        - name: KAFKA_HEAP_OPTS
          value : "-Xmx512M -Xms512M"
        - name: KAFKA_OPTS
          value: "-Dlogging.level=INFO"
        volumeMounts:
        - name: datadir
          mountPath: /var/lib/kafka
      securityContext:
        runAsUser: 1000
        fsGroup: 1000
      volumes:
      - name: datadir
        emptyDir: {}
    """

    kafka_deployment_file = "/tmp/kafka-deployment.yaml"
    with open(kafka_deployment_file, "w") as f:
        f.write(kafka_yaml)

    try:
        kafka_result = subprocess.run(["kubectl", "apply", "-f", kafka_deployment_file], check=True, capture_output=True, text=True)
        logger.info(f"Kubectl apply output: {kafka_result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl apply for Kafka: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Failed to apply Kafka deployment: {e.stderr}")

    return {"message": "Kafka and Zookeeper installed"}




# API to create Kafka topic
@app.post('/create-kafka-topic/{cluster}')
async def create_kafka_topic(cluster: str, request: KafkaTopicRequest):
    try:
        topic_name = request.topic_name
        consumer_group_name = request.consumer_group_name
        
        # Adjust the Zookeeper and Kafka settings as per your environment
        zookeeper_service = "zk-cs.default.svc.cluster.local:2181"

        # Command to create Kafka topic using kubectl run
        create_topic_cmd = [
            "kubectl", "run", "-ti", "--image=gcr.io/google_containers/kubernetes-kafka:1.0-10.2.1",
            "createtopic", "--restart=Never", "--rm", "--",
            "kafka-topics.sh", "--create", "--topic", topic_name,
            "--zookeeper", zookeeper_service, "--partitions", "1", "--replication-factor", "1"
        ]

        # Execute the command using subprocess and capture the output
        result = subprocess.run(create_topic_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check for errors in the command output
        if result.returncode != 0:
            logger.error(f"Failed to create Kafka topic: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Failed to create Kafka topic: {result.stderr}")

        logger.info(f"Created Kafka topic {topic_name}: {result.stdout}")

        # Store the topic and consumer group in the database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO kafka_topics (topic_name, consumer_group_name) VALUES (?, ?)",
                (topic_name, consumer_group_name)
            )
            conn.commit()

        return {"message": f"Created topic {topic_name} and consumer group {consumer_group_name}"}

    except Exception as e:
        logger.error(f"Error creating Kafka topic/consumer group: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating Kafka topic/consumer group: {str(e)}")



# API to deploy an application and create KEDA scaled object
@app.post('/deploy/{cluster}')
async def deploy_application(cluster: str, deployment_data: DeploymentData):
    conn = get_db_connection()
    cursor = conn.cursor()
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()

    if not cluster_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Cluster not found")

    kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
    os.environ["KUBECONFIG"] = kubeconfig_file

    # Define service name based on deployment name
    service_name = f"{deployment_data.deployment_name}-service"

    deployment_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {deployment_data.deployment_name}
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {deployment_data.deployment_name}
  template:
    metadata:
      labels:
        app: {deployment_data.deployment_name}
    spec:
      containers:
      - name: {deployment_data.docker_image.split('/')[-1]}
        image: {deployment_data.docker_image}:{deployment_data.docker_tag}
        resources:
          requests:
            cpu: {deployment_data.cpu_requests}
            memory: {deployment_data.memory_requests}Mi
          limits:
            cpu: {deployment_data.cpu_limits}
            memory: {deployment_data.memory_limits}Mi
        ports:
        {''.join([f"- containerPort: {port}\n" for port in deployment_data.target_ports])}
---
apiVersion: v1
kind: Service
metadata:
  name: {service_name}
  namespace: default
spec:
  selector:
    app: {deployment_data.deployment_name}
  ports:
    - protocol: TCP
      port: {deployment_data.ports[0]}         
      targetPort: {deployment_data.target_ports[0]}     
  type: LoadBalancer
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: {deployment_data.deployment_name}-scaledobject
  namespace: default
spec:
  scaleTargetRef:
    kind: Deployment
    name: {deployment_data.deployment_name}
  minReplicaCount: 1
  maxReplicaCount: 10
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: "kafka.default.svc.cluster.local:9092"
        topic: {deployment_data.kafka_topic}
        consumerGroup: {deployment_data.consumer_group_name}
        lagThreshold: "10"
"""
    deployment_file = f"/tmp/deployment-{deployment_data.deployment_name}.yaml"
    with open(deployment_file, "w") as f:
        f.write(deployment_yaml)

    try:
        result = subprocess.run(["kubectl", "apply", "-f", deployment_file], check=True, capture_output=True, text=True)
        logger.info(f"Kubectl apply output: {result.stdout}")

        # Insert the deployment information into the database, including service_name
        cursor.execute(
            """
            INSERT INTO deployments (cluster_name, deployment_name, service_name)
            VALUES (?, ?, ?)
            """,
            (
                cluster,
                deployment_data.deployment_name,
                service_name
            )
        )
        conn.commit()

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl apply: {e.stderr}")
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to apply Kubernetes resources: {e.stderr}")

    conn.close()
    return {"message": "Deployment created successfully"}


logger = logging.getLogger(__name__)






@app.get('/kafka-topics')
async def get_kafka_topics_consumer_groups():
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch all topics and their associated consumer groups
        topics = cursor.execute("SELECT topic_name, consumer_group_name FROM kafka_topics").fetchall()
        conn.close()
        
        if not topics:
            raise HTTPException(status_code=404, detail="No Kafka topics or consumer groups found")
        
        # Return the list of topics and consumer groups
        return [{"topic_name": row["topic_name"], "consumer_group_name": row["consumer_group_name"]} for row in topics]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Kafka topics/consumer groups: {str(e)}")
    
@app.post('/install-keda/{cluster}')
async def install_keda(cluster: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster,)).fetchone()
    conn.close()

    if not cluster_data:
        raise HTTPException(status_code=404, detail="Cluster not found")

    kubeconfig_file = create_eks_kubeconfig(cluster_data['cluster_name'], cluster_data['region'], cluster_data['access_key'], cluster_data['secret_key'])
    os.environ["KUBECONFIG"] = kubeconfig_file

    keda_installed = subprocess.run(["helm", "list", "-n", "keda"], capture_output=True, text=True)
    if "keda" in keda_installed.stdout:
        return {"message": "KEDA is already installed"}

    install_command = ["helm", "install", "keda", "kedacore/keda", "--namespace", "keda", "--create-namespace"]
    result = subprocess.run(install_command, capture_output=True, text=True)

    if result.returncode == 0:
        return {"message": "KEDA installed successfully"}
    else:
        return {"error": "Failed to install KEDA", "details": result.stderr}
    
import logging

@app.get('/deployments/{cluster}')
async def get_deployment_names(cluster: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        deployments = cursor.execute(
            "SELECT deployment_name FROM deployments WHERE cluster_name = ?",
            (cluster,)
        ).fetchall()

        if not deployments:
            raise HTTPException(status_code=404, detail="No deployments found for the specified cluster")

        deployment_names = [row["deployment_name"] for row in deployments]
    finally:
        conn.close()

    return {"deployments": deployment_names}

@app.delete('/delete-deployment/{cluster_name}/{deployment_name}')
async def delete_deployment(cluster_name: str, deployment_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch cluster details from the database
    cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster_name,)).fetchone()
    if not cluster_data:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    service_name = cursor.execute("SELECT service_name FROM deployments WHERE deployment_name = ?", (deployment_name,)).fetchone()
    if not service_name:
        raise HTTPException(status_code=404, detail="Service not found")

    conn.close()

    # Set up Kubernetes configuration
    try:
        kubeconfig_file = create_eks_kubeconfig(
            cluster_data['cluster_name'],
            cluster_data['region'],
            cluster_data['access_key'],
            cluster_data['secret_key']
        )
        os.environ["KUBECONFIG"] = kubeconfig_file
        config.load_kube_config(config_file=kubeconfig_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to configure Kubernetes client: " + str(e))

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    custom_objects_api = client.CustomObjectsApi()

    namespace = "default"

    try:
        # Delete the deployment
        apps_v1.delete_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Delete the associated service
        v1.delete_namespaced_service(name=service_name[0], namespace=namespace)

        # Delete the scaled object if it exists (assuming KEDA ScaledObject CRD)
        try:
            custom_objects_api.delete_namespaced_custom_object(
                group="keda.sh",
                version="v1alpha1",
                namespace=namespace,
                plural="scaledobjects",
                name=deployment_name
            )
        except client.exceptions.ApiException as e:
            # Log but ignore if scaled object does not exist
            if e.status != 404:
                raise e

    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=500, detail="Failed to delete deployment, service, or scaled object: " + str(e))

    return {"message": f"Deployment {deployment_name} and its associated resources deleted successfully."}

@app.get('/deployment-details/{cluster_name}/{deployment_name}')
async def get_deployment_summary(cluster_name: str, deployment_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    logger.info("Fetching deployment summary for cluster: %s, deployment: %s", cluster_name, deployment_name)

    try:
        deployment = cursor.execute("SELECT * FROM deployments WHERE deployment_name = ?", (deployment_name,)).fetchone()
        if not deployment:
            logger.error("Deployment %s not found in the database", deployment_name)
            raise HTTPException(status_code=404, detail="Deployment not found")

        service_name = deployment["service_name"]
        cluster_data = cursor.execute("SELECT * FROM clusters WHERE cluster_name = ?", (cluster_name,)).fetchone()
        if not cluster_data:
            logger.error("Cluster %s not found in the database", cluster_name)
            raise HTTPException(status_code=404, detail="Cluster not found")
    finally:
        conn.close()

    try:
        kubeconfig_file = create_eks_kubeconfig(
            cluster_data['cluster_name'],
            cluster_data['region'],
            cluster_data['access_key'],
            cluster_data['secret_key']
        )
        os.environ["KUBECONFIG"] = kubeconfig_file

        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        metrics_api = CustomObjectsApi()

        # Fetch deployment details
        deployment_obj = apps_v1.read_namespaced_deployment(name=deployment_name, namespace="default")

        # Fetch pod details related to the deployment
        pods = v1.list_namespaced_pod(namespace="default", label_selector=f"app={deployment_name}").items
        pod_status_list = []
        total_restarts = 0
        running_pods = 0

        # Get metrics for pods
        metrics = metrics_api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace="default",
            plural="pods"
        )
        
        # Create a dictionary for quick lookup of pod metrics
        pod_metrics = {item['metadata']['name']: item['containers'][0]['usage'] for item in metrics['items']}

        for pod in pods:
            restart_count = sum([cs.restart_count for cs in pod.status.container_statuses or []])
            total_restarts += restart_count
            if pod.status.phase == "Running":
                running_pods += 1

            # Fetch CPU and memory usage from metrics
            cpu_usage = pod_metrics.get(pod.metadata.name, {}).get('cpu', 'N/A')
            memory_usage = pod_metrics.get(pod.metadata.name, {}).get('memory', 'N/A')

            pod_status_list.append({
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "restarts": restart_count,
                "pod_ip": pod.status.pod_ip,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage
            })

        # Fetch service details using the service_name
        service = v1.read_namespaced_service(name=service_name, namespace="default")

        # Get external IP from the LoadBalancer (if applicable)
        external_ip = None
        if service.status.load_balancer and service.status.load_balancer.ingress:
            external_ip = service.status.load_balancer.ingress[0].ip or service.status.load_balancer.ingress[0].hostname

        # Prepare the summary response
        deployment_summary = {
            "deployment_name": deployment_obj.metadata.name,
            "replicas": deployment_obj.spec.replicas,
            "pods_running": running_pods,
            "total_restarts": total_restarts,
            "service_name": service.metadata.name,
            "external_ip": external_ip,
            "pod_status_list": pod_status_list
        }

        return deployment_summary

    except client.exceptions.ApiException as e:
        logger.error("Kubernetes API error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve deployment summary: {str(e)}")


@app.post('/send-kafka-messages')
async def send_kafka_messages(request: KafkaMessageRequest):
    topic_name = request.topic_name
    message = request.message
    message_count = request.message_count

    # Identify the Kafka pod
    try:
        pod_name_result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "default", "-l", "app=kafka", "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True
        )
        pod_name = pod_name_result.stdout.strip()

        if not pod_name:
            raise HTTPException(status_code=500, detail="Kafka pod not found.")

        print(f"Found Kafka pod: {pod_name}")  # Log pod name

        # Create a script to send messages
        script = f"""
        for i in $(seq 1 {message_count}); do
          echo "{message} $i" | /opt/bitnami/kafka/bin/kafka-console-producer.sh --broker-list kafka.default.svc.cluster.local:9092 --topic {topic_name};
        done
        """

        print(f"Running script: {script}")  # Log script details

        # Exec into the pod and run the script
        exec_result = subprocess.run(
            ["kubectl", "exec", "-i", pod_name, "-n", "default", "--", "bash", "-c", script],
            capture_output=True, text=True
        )

        if exec_result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error while producing Kafka messages: {exec_result.stderr}")

        return {"message": f"Successfully sent {message_count} messages to topic {topic_name}"}

    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")  # Log any subprocess errors
        raise HTTPException(status_code=500, detail=f"Failed to exec into Kafka pod: {str(e)}")
    except Exception as e:
        print(f"Unhandled error: {str(e)}")  # Log any other unhandled errors
        raise HTTPException(status_code=500, detail=f"Unhandled error: {str(e)}")

# Run the FastAPI application using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



