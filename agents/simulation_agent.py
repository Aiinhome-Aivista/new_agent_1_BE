import json
from utils.llm_client import query_llm, safe_json_loads

SIMULATION_SYS_PROMPT = """You are a Principal Enterprise Solutions Architect and Lead UX/Product Designer.
Analyze the provided High-Level Architecture (HLA) document, proposal scope, and solution specifications.
Identify what target applications (Web Portal, Native Mobile App, Admin Console, Executive Dashboard, etc.) and what exact screens are required for this business system.

Generate a comprehensive UI Screen Hierarchy with realistic components, mock data, and user actions.
Strictly return JSON matching this schema:
{
  "application_name": "string",
  "target_platforms": ["web", "mobile", "tablet"],
  "theme": {
    "primary": "#0ea5e9",
    "mode": "dark",
    "borderRadius": "12px"
  },
  "screens": [
    {
      "id": "screen_1",
      "name": "Screen Title",
      "category": "core|workflow|analytics|settings|auth",
      "description": "Short explanation of the screen purpose",
      "supported_devices": ["mobile", "tablet", "desktop"],
      "components": [
        {
          "type": "stats_grid",
          "props": {
            "title": "Core KPI Overview",
            "items": ["Metric 1: 95%", "Metric 2: $120k", "Metric 3: 4 Active"]
          }
        },
        {
          "type": "action_card",
          "props": {
            "title": "Workflow Card Title",
            "description": "Details about action item",
            "actions": ["Approve", "Review", "Reject"]
          }
        },
        {
          "type": "action_table",
          "props": {
            "title": "Table Title",
            "columns": ["Col 1", "Col 2", "Status", "Action"],
            "rows": [
              { "col_1": "Val 1", "col_2": "Val 2", "status": "Pending", "action": "View" }
            ]
          }
        },
        {
          "type": "timeline_chart",
          "props": {
            "title": "Timeline Velocity",
            "stages": ["Stage 1", "Stage 2", "Stage 3"]
          }
        }
      ]
    }
  ]
}
Return ONLY valid JSON.
"""

def extract_screens_from_hla(hla_text, ir_data=None):
    """Generates screen hierarchy from HLA text and/or structured IR."""
    ir_summary = ""
    if ir_data:
        try:
            ir_summary = json.dumps(ir_data)[:3000]
        except Exception:
            ir_summary = str(ir_data)[:3000]

    user_prompt = f"""
HLA Document / Architecture Content / Requirements:
{str(hla_text)[:7000] if hla_text else "Enterprise Solution Architecture"}

Intermediate Representation / Solution Modules:
{ir_summary if ir_summary else "None"}

Please design 3 to 6 comprehensive screens covering authentication, primary dashboard/core view, key business workflows, and reporting/analytics.
Ensure all screen names, descriptions, labels, and widget values are in professional English.
Ensure each screen contains meaningful components (stats_grid, action_card, action_table, or timeline_chart).
"""
    res = query_llm(SIMULATION_SYS_PROMPT, user_prompt, temperature=0.3, max_tokens=4000, json_mode=True)
    fallback = {
        "application_name": "Enterprise Architecture Solution",
        "target_platforms": ["web", "mobile", "tablet"],
        "theme": {"primary": "#0ea5e9", "mode": "dark", "borderRadius": "12px"},
        "screens": [
            {
                "id": "screen_dashboard",
                "name": "Executive Dashboard",
                "category": "core",
                "description": "High-level overview of enterprise operational metrics, health, and throughput.",
                "supported_devices": ["desktop", "tablet", "mobile"],
                "components": [
                    {
                        "type": "stats_grid",
                        "props": {
                            "title": "Core KPI Overview",
                            "items": ["System Health: 99.98%", "Active Workflows: 24", "Security Score: A+"]
                        }
                    },
                    {
                        "type": "timeline_chart",
                        "props": {
                            "title": "Milestone Velocity",
                            "stages": ["Phase 1: Ingestion", "Phase 2: AI Pipeline", "Phase 3: Production Rollout"]
                        }
                    },
                    {
                        "type": "action_table",
                        "props": {
                            "title": "Recent System Activity",
                            "columns": ["Service", "Status", "Latency", "Action"],
                            "rows": [
                                {"service": "Auth Gateway", "status": "Healthy", "latency": "14ms", "action": "Inspect"},
                                {"service": "Workflow Engine", "status": "Active", "latency": "38ms", "action": "Monitor"}
                            ]
                        }
                    }
                ]
            },
            {
                "id": "screen_workflow",
                "name": "Operations & Approvals",
                "category": "workflow",
                "description": "Human-in-the-loop task routing, governance validation, and decision approvals.",
                "supported_devices": ["mobile", "desktop"],
                "components": [
                    {
                        "type": "action_card",
                        "props": {
                            "title": "Pending Governance Approval",
                            "description": "Architecture RFC: Cloud infrastructure scaling policy pending review.",
                            "actions": ["Approve", "Request Changes", "Reject"]
                        }
                    },
                    {
                        "type": "stats_grid",
                        "props": {
                            "title": "Approval Pipeline",
                            "items": ["Pending: 3", "Approved Today: 18", "Escalations: 0"]
                        }
                    }
                ]
            },
            {
                "id": "screen_analytics",
                "name": "Performance Analytics",
                "category": "analytics",
                "description": "Deep-dive business intelligence, resource consumption, and telemetry metrics.",
                "supported_devices": ["desktop", "tablet", "mobile"],
                "components": [
                    {
                        "type": "stats_grid",
                        "props": {
                            "title": "Resource Telemetry",
                            "items": ["CPU Utilization: 42%", "Memory Bandwidth: 61%", "API Requests: 1.4M/day"]
                        }
                    },
                    {
                        "type": "action_table",
                        "props": {
                            "title": "Incident & SLA Tracking",
                            "columns": ["Component", "SLA Target", "Actual", "Status"],
                            "rows": [
                                {"component": "Data Pipeline", "target": "99.9%", "actual": "99.95%", "status": "Met"},
                                {"component": "Vector Index Search", "target": "<100ms", "actual": "45ms", "status": "Optimal"}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    parsed = safe_json_loads(res, fallback)
    if not isinstance(parsed, dict) or "screens" not in parsed or not parsed["screens"]:
        return fallback
    return parsed

def refine_screen_with_chat(current_schema, user_instruction, image_data=None):
    """Refines or updates existing screen schema dynamically based on chatbot commands and optional image references."""
    image_clause = ""
    if image_data:
        image_clause = f"""
An image/diagram reference was uploaded with this request. If the user refers to adding an image, visual mockup, or architecture screenshot, add or modify an "image" or "banner" component with realistic mock/uploaded properties:
{{
  "type": "image",
  "props": {{
    "title": "Uploaded Architecture Reference / Screenshot",
    "image_url": "{image_data if isinstance(image_data, str) and image_data.startswith('http') else (image_data if isinstance(image_data, str) and image_data.startswith('data:') else '')}",
    "caption": "Referenced UI wireframe from user upload"
  }}
}}
"""

    refine_prompt = f"""Current Screen Schema:
{json.dumps(current_schema, indent=2)}

User Instruction:
"{user_instruction}"
{image_clause}

Carefully modify the screen schema to fulfill the user's instructions immediately:
- If asked to add a component, metric, button, table, or chart, add it to the active or relevant screen.
- If asked to add an image or mockup, insert an "image" component.
- If asked to add a new screen, append it to "screens".
- If modifying fields/actions, update them directly in "props".
- Ensure all names, labels, and text values are in professional English.

Maintain the exact schema structure. Return ONLY valid JSON.
"""
    res = query_llm(
        "You are an interactive UI schema editor for a real-time responsive screen simulator. Output strictly valid JSON matching the schema.",
        refine_prompt,
        temperature=0.2,
        max_tokens=4000,
        json_mode=True
    )
    return safe_json_loads(res, current_schema)

