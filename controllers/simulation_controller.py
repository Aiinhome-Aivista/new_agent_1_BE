import json
from flask import request
from utils.api_response import success_response, error_response
from database.db_connection import get_db_connection
from agents.simulation_agent import extract_screens_from_hla, refine_screen_with_chat

def get_or_generate_screens(proposal_id):
    """Fetches existing simulation_schema from the database or extracts new screens via LLM."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT simulation_schema, requirements_text, files_info, structured_json_ir FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        
        if not row:
            return error_response("Proposal not found", status_code=404)
            
        sim_schema = row.get("simulation_schema")
        req_text = row.get("requirements_text") or ""
        ir_raw = row.get("structured_json_ir")
        
        # If schema already exists and valid, return directly
        if sim_schema:
            try:
                parsed_schema = json.loads(sim_schema) if isinstance(sim_schema, str) else sim_schema
                if isinstance(parsed_schema, dict) and parsed_schema.get("screens"):
                    return success_response(parsed_schema)
            except Exception:
                pass
                
        # Parse IR data if available
        ir_data = None
        if ir_raw:
            try:
                ir_data = json.loads(ir_raw) if isinstance(ir_raw, str) else ir_raw
            except Exception:
                pass

        # Generate new schema using Simulation Agent
        extracted_schema = extract_screens_from_hla(req_text or "Enterprise Application Architecture", ir_data)
        
        # Save back into DB
        cursor.execute("UPDATE proposals SET simulation_schema = %s WHERE id = %s", (json.dumps(extracted_schema), proposal_id))
        conn.commit()
        
        return success_response(extracted_schema)
        
    except Exception as e:
        return error_response(f"Failed to generate or fetch simulation schema: {str(e)}", status_code=500)
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass

def chat_simulation_refine():
    """Handles chatbot instructions to refine/update the simulation schema dynamically."""
    try:
        data = request.get_json() or {}
        proposal_id = data.get('proposal_id')
        user_message = data.get('message')
        current_schema = data.get('current_schema')
        
        if not proposal_id or not user_message:
            return error_response("Proposal ID and message are required", status_code=400)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # If current_schema not provided in request, read from DB
        if not current_schema:
            cursor.execute("SELECT simulation_schema FROM proposals WHERE id = %s", (proposal_id,))
            row = cursor.fetchone()
            if row and row.get("simulation_schema"):
                try:
                    current_schema = json.loads(row["simulation_schema"])
                except Exception:
                    current_schema = {}
                    
        if not current_schema:
            current_schema = {"application_name": "Enterprise Solution", "screens": []}
            
        updated_schema = refine_screen_with_chat(current_schema, user_message)
        
        # Persist updated schema to DB
        cursor.execute("UPDATE proposals SET simulation_schema = %s WHERE id = %s", (json.dumps(updated_schema), proposal_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return success_response({
            "reply": "The screen simulation layout and components have been successfully updated per your request.",
            "updated_schema": updated_schema
        })
        
    except Exception as e:
        return error_response(f"Failed to process chat refinement: {str(e)}", status_code=500)

def reset_simulation_screens(proposal_id):
    """Regenerates the simulation screens from scratch based on proposal architecture."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT requirements_text, structured_json_ir FROM proposals WHERE id = %s", (proposal_id,))
        row = cursor.fetchone()
        if not row:
            return error_response("Proposal not found", status_code=404)
            
        req_text = row.get("requirements_text") or ""
        ir_data = None
        if row.get("structured_json_ir"):
            try:
                ir_data = json.loads(row["structured_json_ir"])
            except Exception:
                pass
                
        new_schema = extract_screens_from_hla(req_text, ir_data)
        cursor.execute("UPDATE proposals SET simulation_schema = %s WHERE id = %s", (json.dumps(new_schema), proposal_id))
        conn.commit()
        
        return success_response(new_schema)
    except Exception as e:
        return error_response(f"Failed to reset simulation screens: {str(e)}", status_code=500)
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass
