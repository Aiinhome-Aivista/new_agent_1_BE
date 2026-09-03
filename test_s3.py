import os
from dotenv import load_dotenv
load_dotenv()
from utils.s3_utils import upload_to_s3, get_s3_client

client = get_s3_client()
if client is None:
    print("Failed to initialize S3 client")
else:
    print("S3 client initialized")
    
bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "agent-initiative-bucket")
base_folder = os.getenv("AWS_S3_BASE_FOLDER", "Agents_Doc")
agent_folder = os.getenv("AWS_S3_AGENT_FOLDER", "Agent_11")

test_key = f"{base_folder}/{agent_folder}/test_folder/test.txt"

with open("test.txt", "w") as f:
    f.write("test upload")

try:
    with open("test.txt", "rb") as f:
        success, msg = upload_to_s3(f, bucket_name, test_key)
        print(f"Upload success: {success}, msg: {msg}")
except Exception as e:
    print(f"Exception: {e}")
