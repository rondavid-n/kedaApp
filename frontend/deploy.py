import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Fetch environment variables passed from Jenkinsfile
BUCKET_NAME = os.getenv('S3_BUCKET')  
REGION = os.getenv('AWS_REGION')  
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000') 


INPUT_HTML_PATH = 'index.html'  
OUTPUT_HTML_PATH = 'dist/index.html'  


s3 = boto3.client('s3', region_name=REGION)


def ensure_output_directory(output_path):
    directory = os.path.dirname(output_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def inject_env_variables(input_path, output_path, backend_url):
    try:
        with open(input_path, 'r') as file:
            html_content = file.read()
        

        updated_content = html_content.replace('{{BACKEND_URL}}', backend_url)

        ensure_output_directory(output_path)

        with open(output_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Successfully injected BACKEND_URL into {output_path}")
    except Exception as e:
        print(f"Error processing HTML: {e}")
        raise

# Function to upload file to S3
def upload_to_s3(file_name, bucket, object_name=None):
    try:
        if object_name is None:
            object_name = file_name
        s3.upload_file(file_name, bucket, object_name, ExtraArgs={'ACL': 'public-read'})
        print(f"File uploaded successfully to {bucket}/{object_name}")
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")
    except ClientError as e:
        print(f"Failed to upload to S3: {e}")

if __name__ == "__main__":
    inject_env_variables(INPUT_HTML_PATH, OUTPUT_HTML_PATH, BACKEND_URL)

    upload_to_s3(OUTPUT_HTML_PATH, BUCKET_NAME, 'index.html')
