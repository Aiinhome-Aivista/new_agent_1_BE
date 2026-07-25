import os
import uuid
import json
from flask import request, jsonify
from database.db_connection import get_db_connection
from utils.doc_extractor import extract_text
from utils.llm_client import query_llm

def upload_case_study():
    try:
        files = request.files.getlist("files")
        if not files or not files[0].filename:
            return jsonify({"error": "No file uploaded"}), 400
            
        file = files[0]
        upload_dir = os.path.join(os.getcwd(), 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        save_path = os.path.join(upload_dir, safe_name)
        file.save(save_path)
        
        text = extract_text(save_path)
        if not text or not text.strip():
            return jsonify({"error": "Failed to extract text from file"}), 400
            
        # Call LLM to parse text into rich case study JSON schema
        sys_prompt = (
            "You are an expert Solutions Architect. Parse the provided case study document text "
            "and format it into a structured JSON object representing a detailed case study.\n\n"
            "Your response must ONLY be a JSON object with these keys:\n"
            "- 'project_name': short name of the project (e.g. 'Teradata to Snowflake migration').\n"
            "- 'client_industry': industry/details of the client (e.g. 'Lifestyle Footwear Company in US').\n"
            "- 'business_problem': a list of exactly 3-4 strings representing key business/technical challenges.\n"
            "- 'our_approach': a list of exactly 3-4 strings detailing the steps or architectural choices built to solve it.\n"
            "- 'tech_architecture_mermaid': a valid, clean Mermaid.js flowchart (starting with 'graph LR' for optimal wide layout) representing the technical architecture.\n"
            "- 'tech_architecture_explanation': a list of exactly 3 strings representing concise summaries (1-2 sentences) of: 1. Source/Ingestion, 2. Storage/Processing, and 3. Consumption/Reporting.\n"
            "- 'key_technologies': a list of exactly 3-4 technologies used (e.g. ['Snowflake', 'Azure Data Factory']).\n"
            "- 'benefits_outcome': a list of exactly 3-4 strings summarizing benefits and outcomes.\n\n"
            "Do not include any explanation or markdown formatting outside the JSON."
        )
        
        res = query_llm(sys_prompt, text, json_mode=True)
        if not res:
            return jsonify({"error": "Failed to parse case study with LLM"}), 500
            
        content = res.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed_data = json.loads(content)
        
        # Save to knowledge_assets database table
        conn = get_db_connection()
        cursor = conn.cursor()
        
        name = parsed_data.get("project_name", "Migration Project")
        capabilities = ", ".join(parsed_data.get("key_technologies", []))
        
        cursor.execute(
            "INSERT INTO knowledge_assets (name, description, category, capabilities) VALUES (%s, %s, %s, %s)",
            (name, json.dumps(parsed_data), "Case Study", capabilities)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Case study uploaded and processed successfully",
            "project_name": name
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to upload case study: {str(e)}"}), 500

def get_case_studies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, description, capabilities, created_at FROM knowledge_assets WHERE category = 'Case Study' ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        case_studies = []
        for r in rows:
            try:
                desc = json.loads(r["description"])
            except:
                desc = {}
            case_studies.append({
                "id": r["id"],
                "project_name": r["name"],
                "client_industry": desc.get("client_industry", "Unknown"),
                "key_technologies": r["capabilities"],
                "created_at": str(r["created_at"]) if r["created_at"] else ""
            })
            
        return jsonify(case_studies), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def delete_case_study(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_assets WHERE id = %s AND category = 'Case Study'", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Case study deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
