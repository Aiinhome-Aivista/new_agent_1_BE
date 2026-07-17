import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ARANGO_URL = os.getenv("ARANGO_URL", "http://localhost:8529").rstrip('/')
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")
ARANGO_DB = os.getenv("ARANGO_DB", "proposal_forge_db")

class ArangoDBClient:
    def __init__(self):
        self.base_url = ARANGO_URL
        self.user = ARANGO_USER
        self.password = ARANGO_PASSWORD
        self.db = ARANGO_DB
        self.auth = (self.user, self.password)
        self.headers = {"Content-Type": "application/json"}
        self.is_connected = False
        self._check_connection()

    def _check_connection(self):
        try:
            # Try connecting to the specified DB
            url = f"{self.base_url}/_db/{self.db}/_api/database/current"
            res = requests.get(url, auth=self.auth, timeout=3)
            if res.status_code == 200:
                self.is_connected = True
                print(f"Connected to ArangoDB database: {self.db}")
            else:
                # DB might not exist yet, try system DB to verify server connection
                url = f"{self.base_url}/_db/_system/_api/database/current"
                res_sys = requests.get(url, auth=self.auth, timeout=3)
                if res_sys.status_code == 200:
                    self.is_connected = True
                    print("Connected to ArangoDB system DB. Target DB needs creation.")
                else:
                    self.is_connected = False
                    print(f"ArangoDB connection failed with status code {res.status_code}")
        except Exception as e:
            self.is_connected = False
            print(f"ArangoDB server unreachable: {e}")

    def init_db(self):
        if not self.is_connected:
            print("ArangoDB is offline. Skipping database initialization.")
            return False

        try:
            # 1. Create database if it doesn't exist
            # Check if db exists
            url = f"{self.base_url}/_db/_system/_api/database"
            res = requests.get(url, auth=self.auth)
            dbs = res.json().get("result", [])
            if self.db not in dbs:
                print(f"Creating ArangoDB database: {self.db}...")
                create_url = f"{self.base_url}/_db/_system/_api/database"
                create_res = requests.post(create_url, auth=self.auth, json={"name": self.db})
                if create_res.status_code not in [200, 201]:
                    print(f"Failed to create ArangoDB database: {create_res.text}")
                    return False

            # 2. Create collections if they don't exist
            collections = ["proposals", "documents", "chunks", "knowledge_assets", "proposal_steps"]
            for col in collections:
                col_url = f"{self.base_url}/_db/{self.db}/_api/collection/{col}"
                col_res = requests.get(col_url, auth=self.auth)
                if col_res.status_code == 404:
                    print(f"Creating collection: {col}...")
                    create_col_url = f"{self.base_url}/_db/{self.db}/_api/collection"
                    requests.post(create_col_url, auth=self.auth, json={"name": col})
            
            # Seed default assets in ArangoDB if empty
            self._seed_default_assets()
            return True
        except Exception as e:
            print(f"Failed to initialize ArangoDB structures: {e}")
            return False

    def _seed_default_assets(self):
        try:
            # Check if already seeded
            query = "FOR a IN knowledge_assets LIMIT 1 RETURN a"
            res = self.query(query)
            if res:
                return # Already seeded

            default_assets = [
                {
                    "name": "PwC Cloud Migration Toolkit",
                    "description": "A framework containing reusable Ansible and Terraform templates for migrating enterprise Java/React apps to AWS/Azure.",
                    "category": "Asset",
                    "capabilities": "AWS,Azure,Terraform,Ansible,Migration,Java,React"
                },
                {
                    "name": "Enterprise Data Governance Framework",
                    "description": "Standard templates, policies, and schemas for metadata management, lineage tracking, and data cataloging.",
                    "category": "Asset",
                    "capabilities": "Governance,Collibra,Data Catalog,Metadata,SQL"
                },
                {
                    "name": "DevOps Pipeline Accelerator",
                    "description": "Pre-configured CI/CD pipelines using GitHub Actions and GitLab CI, with integrated security scans (Snyk, SonarQube).",
                    "category": "Asset",
                    "capabilities": "DevOps,GitHub Actions,GitLab CI,Snyk,SonarQube,Docker,Kubernetes"
                },
                {
                    "name": "React/TypeScript Front-End Competency",
                    "description": "Large pool of skilled front-end engineers specializing in React, TypeScript, State Management (Zustand/Redux), and Tailwind CSS.",
                    "category": "Competency",
                    "capabilities": "React,TypeScript,Zustand,Tailwind CSS,Vite"
                },
                {
                    "name": "Python Data Engineering Competency",
                    "description": "Team of data engineers experienced in PySpark, Pandas, Airflow, and building robust ETL pipelines.",
                    "category": "Competency",
                    "capabilities": "Python,PySpark,Pandas,Airflow,ETL,Data Pipeline"
                },
                {
                    "name": "Cybersecurity Compliance Competency",
                    "description": "Certified auditors and engineers specializing in ISO27001, SOC2, and data privacy compliance assessments.",
                    "category": "Competency",
                    "capabilities": "ISO27001,SOC2,Cybersecurity,Compliance,Audit"
                }
            ]

            print("Seeding default knowledge assets to ArangoDB...")
            for asset in default_assets:
                url = f"{self.base_url}/_db/{self.db}/_api/document/knowledge_assets"
                # Seed with embeddings for vector search
                from database.vector_client import get_embedding
                asset["embedding"] = get_embedding(f"{asset['name']} {asset['description']}")
                requests.post(url, auth=self.auth, json=asset)
        except Exception as e:
            print(f"ArangoDB seeding warning: {e}")

    def query(self, aql, bind_vars=None):
        try:
            url = f"{self.base_url}/_db/{self.db}/_api/cursor"
            payload = {"query": aql}
            if bind_vars:
                payload["bindVars"] = bind_vars
            res = requests.post(url, auth=self.auth, json=payload, timeout=5)
            if res.status_code == 201:
                return res.json().get("result", [])
            return []
        except Exception as e:
            print(f"ArangoDB query error: {e}")
            return []

    def insert(self, collection, document):
        try:
            url = f"{self.base_url}/_db/{self.db}/_api/document/{collection}"
            res = requests.post(url, auth=self.auth, json=document, timeout=5)
            return res.status_code in [200, 201, 202]
        except Exception as e:
            print(f"ArangoDB insert error: {e}")
            return False
            
    def upsert_document(self, collection, doc_key, document):
        try:
            from database.vector_client import get_embedding
            text_to_embed = f"{document.get('name', '')} {document.get('description', '')} {document.get('capabilities', '')}"
            document["embedding"] = get_embedding(text_to_embed)
            document["_key"] = doc_key
            
            aql = f"""
            UPSERT {{ _key: @doc_key }}
            INSERT @doc
            UPDATE @doc
            IN @@collection
            """
            bind_vars = {
                "doc_key": doc_key,
                "doc": document,
                "@collection": collection
            }
            self.query(aql, bind_vars)
            return True
        except Exception as e:
            print(f"ArangoDB upsert error: {e}")
            return False

# Export initialized client
arango_client = ArangoDBClient()
