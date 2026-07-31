from utils.prompts import PRICING_KB_SYS_PROMPT_0, PRICING_KB_SYS_PROMPT_2
import json
from database.vector_client import search_embeddings
from utils.llm_client import query_llm, safe_json_loads

def get_technology_options():
    """
    Dynamically loads technology options by extracting and classifying capabilities
    from the knowledge assets database. If no skills exist, returns empty lists.
    """
    try:
        from database.db_connection import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT capabilities FROM knowledge_assets")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching capabilities from database: {e}")
        rows = []

    # Gather all capabilities
    all_skills = set()
    for row in rows:
        caps = row.get("capabilities", "")
        if caps:
            # Split by commas and clean up
            for val in caps.split(','):
                cleaned = val.strip()
                if cleaned and cleaned.lower() not in ["file upload", "document"]:
                    all_skills.add(cleaned)

    empty_options = {
        "ui": [],
        "backend": [],
        "database": []
    }

    if not all_skills:
        return empty_options

    # Call LLM to classify these unique skills
    sys_prompt = PRICING_KB_SYS_PROMPT_0
    user_prompt = f"List of skills to classify:\n{', '.join(all_skills)}"
    
    try:
        response = query_llm(sys_prompt, user_prompt, temperature=0.1, json_mode=True)
        if response:
            classified = safe_json_loads(response, empty_options)
            # Validate format
            for key in ["ui", "backend", "database"]:
                if key not in classified or not isinstance(classified[key], list):
                    classified[key] = []
                # Ensure elements have 'value' and 'label'
                cleaned_list = []
                for item in classified[key]:
                    if isinstance(item, dict) and "value" in item and "label" in item:
                        cleaned_list.append(item)
                    elif isinstance(item, str):
                        cleaned_list.append({"value": item.lower().replace(' ', '_'), "label": item})
                classified[key] = cleaned_list
            return classified
    except Exception as e:
        print(f"Error classifying skills with LLM: {e}")

    return empty_options

def calculate_budget(ui_tech, backend_tech, db_tech):
    """
    Calculates the total budget dynamically using LLM and Vector Knowledge Base.
    """
    # 1. Map values to their human readable labels dynamically
    options = get_technology_options()
    
    def find_label(tech_val, category):
        for opt in options.get(category, []):
            if opt.get("value") == tech_val:
                return opt.get("label")
        # Fallback if not found
        return tech_val.replace('_', ' ').title()

    ui_label = find_label(ui_tech, "ui")
    backend_label = find_label(backend_tech, "backend")
    db_label = find_label(db_tech, "database")
    
    # 2. Search knowledge base for pricing context
    search_query = f"Cost budget pricing estimation for {ui_label}, {backend_label}, {db_label}"
    results = search_embeddings("knowledge_assets", search_query, n_results=5)
    
    # Compile context strings
    kb_context = []
    for r in results:
        meta = r.get("metadata", {})
        doc_text = r.get("document", "")
        kb_context.append(
            f"Asset: {meta.get('name', 'Unknown')} (Category: {meta.get('category', 'Asset')})\n"
            f"Capabilities: {meta.get('capabilities', '')}\n"
            f"Description: {meta.get('description', '')}\n"
            f"Details: {doc_text}\n"
        )
        
    context_str = "\n".join(kb_context) if kb_context else "No specific pricing knowledge found."
    
    # 3. Prompt LLM to calculate the budget
    sys_prompt = PRICING_KB_SYS_PROMPT_2
    
    user_prompt = f"Selected Tech Stack:\n- UI: {ui_label}\n- Backend: {backend_label}\n- Database: {db_label}\n\nKnowledge Base Context:\n{context_str}"
    
    response = query_llm(sys_prompt, user_prompt, json_mode=True)
    
    default_fallback = {
        "total_cost": 50000,
        "formatted_budget": "$50,000"
    }
    
    if not response:
        return default_fallback
        
    parsed_json = safe_json_loads(response, default_fallback)
    return parsed_json
