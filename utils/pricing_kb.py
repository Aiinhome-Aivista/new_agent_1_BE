import json
from database.vector_client import search_embeddings
from utils.llm_client import query_llm, safe_json_loads

# Static list of technology names for the UI dropdowns.
# No hardcoded costs here! The LLM determines the cost based on the vector knowledge base.
TECH_OPTIONS = {
    "ui": {
        "react": {"label": "React.js"},
        "angular": {"label": "Angular"},
        "vue": {"label": "Vue.js"},
        "html_vanilla": {"label": "Vanilla HTML/JS"}
    },
    "backend": {
        "flask": {"label": "Flask (Python)"},
        "django": {"label": "Django (Python)"},
        "express": {"label": "Express (Node.js)"},
        "spring": {"label": "Spring Boot (Java)"}
    },
    "database": {
        "mysql": {"label": "MySQL"},
        "postgres": {"label": "PostgreSQL"},
        "mongodb": {"label": "MongoDB"},
        "arango": {"label": "ArangoDB"}
    }
}

def get_technology_options():
    """
    Returns available technologies to populate the UI dropdowns.
    """
    return {
        "ui": [{"value": k, "label": v["label"]} for k, v in TECH_OPTIONS["ui"].items()],
        "backend": [{"value": k, "label": v["label"]} for k, v in TECH_OPTIONS["backend"].items()],
        "database": [{"value": k, "label": v["label"]} for k, v in TECH_OPTIONS["database"].items()]
    }

def calculate_budget(ui_tech, backend_tech, db_tech):
    """
    Calculates the total budget dynamically using LLM and Vector Knowledge Base.
    """
    # 1. Map values to their human readable labels
    ui_label = TECH_OPTIONS["ui"].get(ui_tech, {}).get("label", ui_tech)
    backend_label = TECH_OPTIONS["backend"].get(backend_tech, {}).get("label", backend_tech)
    db_label = TECH_OPTIONS["database"].get(db_tech, {}).get("label", db_tech)
    
    # 2. Search knowledge base for pricing context
    search_query = f"Cost budget pricing estimation for {ui_label}, {backend_label}, {db_label}"
    results = search_embeddings("knowledge_assets", search_query, n_results=5)
    
    # Compile context strings
    kb_context = []
    for r in results:
        meta = r.get("metadata", {})
        kb_context.append(f"Asset: {meta.get('name', 'Unknown')} - Capabilities/Pricing info: {meta.get('capabilities', '')} / {meta.get('description', '')}")
        
    context_str = "\n".join(kb_context) if kb_context else "No specific pricing knowledge found."
    
    # 3. Prompt LLM to calculate the budget
    sys_prompt = (
        "You are a technical presales estimator. You need to calculate the total software development budget based on the selected tech stack.\n"
        "Read the provided Knowledge Base Context to find the cost associated with each technology. If a technology's cost is missing, estimate it reasonably (e.g., $15000).\n"
        "Include a base platform setup cost of $15000.\n"
        "Respond ONLY as a JSON object with two keys:\n"
        "- 'total_cost': an integer representing the total sum.\n"
        "- 'formatted_budget': a string formatted as currency (e.g., '$75,000').\n"
        "Do not include markdown or explanations."
    )
    
    user_prompt = (
        f"Selected Tech Stack:\n- UI: {ui_label}\n- Backend: {backend_label}\n- Database: {db_label}\n\n"
        f"Knowledge Base Context:\n{context_str}"
    )
    
    response = query_llm(sys_prompt, user_prompt, json_mode=True)
    
    default_fallback = {
        "total_cost": 50000,
        "formatted_budget": "$50,000"
    }
    
    if not response:
        return default_fallback
        
    parsed_json = safe_json_loads(response, default_fallback)
    return parsed_json
