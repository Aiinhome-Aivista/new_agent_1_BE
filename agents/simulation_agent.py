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

def refine_screen_with_chat(current_schema, user_instruction, image_data=None, active_screen_id=None):
    """Refines or updates existing screen schema dynamically based on any chatbot commands and optional image references."""
    import copy
    import re

    instr_lower = user_instruction.strip().lower()
    updated = copy.deepcopy(current_schema) if isinstance(current_schema, dict) else {"application_name": "Enterprise Solution", "screens": []}
    screens = updated.get("screens", [])

    # Identify active screen
    target_screen = None
    target_idx = 0
    if active_screen_id:
        for idx, s in enumerate(screens):
            if s.get("id") == active_screen_id:
                target_screen = s
                target_idx = idx
                break
    if not target_screen and len(screens) > 0:
        target_screen = screens[0]
        target_idx = 0

    # -------------------------------------------------------------
    # FAST PATH 1: COLOR / THEME CHANGES (Instant, 0s latency)
    # -------------------------------------------------------------
    color_map = {
        'green': '#10b981', 'emerald': '#059669', 'teal': '#14b8a6',
        'purple': '#a855f7', 'violet': '#8b5cf6', 'indigo': '#6366f1',
        'red': '#ef4444', 'rose': '#f43f5e',
        'orange': '#f97316', 'amber': '#f59e0b', 'yellow': '#eab308',
        'blue': '#3b82f6', 'sky': '#0ea5e9', 'cyan': '#06b6d4',
        'pink': '#ec4899', 'dark': '#1e293b', 'slate': '#475569'
    }
    found_color = None
    for c_name, c_hex in color_map.items():
        if re.search(rf"\b{c_name}\b", instr_lower):
            found_color = c_hex
            break
    
    if found_color and ("color" in instr_lower or "theme" in instr_lower or "whole ui" in instr_lower or "into" in instr_lower):
        if "theme" not in updated or not isinstance(updated["theme"], dict):
            updated["theme"] = {}
        updated["theme"]["primary"] = found_color
        print(f"[Simulation Chat FastPath] Applied theme color: {found_color}")
        return updated

    # -------------------------------------------------------------
    # FAST PATH 2: RENAME SCREEN OR HEADER (Instant, 0s latency)
    # -------------------------------------------------------------
    # e.g. "modify this name into(Welcome to the dashboard)" or "rename screen to Analytics Hub"
    if any(phrase in instr_lower for phrase in ["modify this name", "modify name", "rename screen", "rename this", "change name"]):
        if not any(k in instr_lower for k in ["metric", "kpi", "button", "table"]):
            # Extract new name from parentheses e.g. (Welcome to the dashboard) or quotes or after into/to
            name_in_parens = re.search(r"\(([^)]+)\)", user_instruction)
            if name_in_parens:
                new_name = name_in_parens.group(1).strip()
            else:
                rename_match = re.search(r"(?:modify (?:this )?name (?:to|into)|rename (?:this )?screen to|rename to|change name to)\s+[\"']?([^\"'\n]+)[\"']?", user_instruction, re.IGNORECASE)
                new_name = rename_match.group(1).strip().strip("()") if rename_match else None
            
            if new_name and target_screen:
                target_screen["name"] = new_name
                print(f"[Simulation Chat FastPath] Renamed screen '{target_screen.get('id')}' to '{new_name}'")
                return updated

    # -------------------------------------------------------------
    # FAST PATH 3: MODIFY / ADD METRICS & KPIS (Instant, 0s latency)
    # -------------------------------------------------------------
    # Case A: Adding a new KPI card/metric (e.g. "Add one more KPI card (Income) to the right of the Revenue card")
    if "add" in instr_lower and any(k in instr_lower for k in ["kpi", "metric", "stat"]) and target_screen:
        # Extract title from prompt, e.g. "(Income)", "Income", etc.
        card_name_match = re.search(r"\(([^)]+)\)", user_instruction)
        if not card_name_match:
            card_name_match = re.search(r"(?:kpi card|kpi|metric)\s+(?:called|named|for)?\s*[\"']?([A-Za-z0-9_\s]+?)[\"']?(?:\s+to|\s+at|\s+with|\s*$)", user_instruction, re.IGNORECASE)
        new_kpi_title = card_name_match.group(1).strip() if card_name_match else "Metric"
        
        # Look for existing stats_grid to add alongside
        found_grid = False
        for comp in target_screen.get("components", []):
            if comp.get("type") in ["stats_grid", "kpi", "metric", "stats"]:
                items = comp.setdefault("props", {}).setdefault("items", [])
                items.append(f"{new_kpi_title}: $120K")
                found_grid = True
                print(f"[Simulation Chat FastPath] Appended KPI '{new_kpi_title}' into existing stats_grid alongside existing cards")
                break
        
        if not found_grid:
            target_screen.setdefault("components", []).insert(0, {
                "type": "stats_grid",
                "props": {
                    "title": "Key Metrics",
                    "items": [f"{new_kpi_title}: $120K"]
                }
            })
        return updated

    # Case B: Renaming an existing metric (e.g. "METRIC 1 modify this name into Revenue")
    metric_rename = re.search(r"(?:metric|kpi)\s*(\d+)?\s*(?:modify (?:this )?name (?:to|into)|change (?:name )?to|rename to)\s+[\"']?([^\"'\n]+)[\"']?", user_instruction, re.IGNORECASE)
    if metric_rename and target_screen:
        idx_str = metric_rename.group(1)
        m_idx = (int(idx_str) - 1) if idx_str else 0
        new_metric_name = metric_rename.group(2).strip()
        # Find stats_grid component in target_screen
        for comp in target_screen.get("components", []):
            if comp.get("type") in ["stats_grid", "kpi", "metric", "stats"]:
                items = comp.setdefault("props", {}).setdefault("items", [])
                if m_idx < len(items):
                    raw = items[m_idx]
                    val = raw.split(":", 1)[1].strip() if ":" in raw else "95%"
                    items[m_idx] = f"{new_metric_name}: {val}"
                else:
                    items.append(f"{new_metric_name}: $100K")
                print(f"[Simulation Chat FastPath] Updated metric {m_idx + 1} to '{new_metric_name}'")
                return updated

    # -------------------------------------------------------------
    # FAST PATH 4: ADD BUTTON / CARD WITH EXACT POSITIONING (Instant, 0s latency)
    # -------------------------------------------------------------
    if "add" in instr_lower and "button" in instr_lower and target_screen:
        btn_title_match = re.search(r"(?:called|named|title|for)\s+[\"']?([^\"'\n,]+)[\"']?", user_instruction, re.IGNORECASE)
        btn_title = btn_title_match.group(1).strip() if btn_title_match else "Submit Action"
        new_btn = {
            "type": "button",
            "props": {
                "title": btn_title,
                "action": btn_title
            }
        }
        comps = target_screen.setdefault("components", [])
        
        # Check positioning (at the top, above X, below Y, etc.)
        if "at the top" in instr_lower or "above" in instr_lower or "before" in instr_lower:
            comps.insert(0, new_btn)
            print(f"[Simulation Chat FastPath] Added button '{btn_title}' at top of screen")
        else:
            comps.append(new_btn)
            print(f"[Simulation Chat FastPath] Added button '{btn_title}' to screen")
        return updated

    # -------------------------------------------------------------
    # LLM PATH: FOR COMPLEX ARBITRARY EDITS
    # Scope prompt ONLY to the active screen to keep tokens low and responses under 5-10s!
    # -------------------------------------------------------------
    # IMAGE UPLOAD & VISUAL REPLACEMENT HANDLER
    # -------------------------------------------------------------
    image_url_val = image_data if isinstance(image_data, str) and (image_data.startswith('http') or image_data.startswith('data:')) else ''
    
    # Fast path: User uploads an image and asks to replace something or insert mockup
    if image_url_val and any(k in instr_lower for k in ["replace", "change this into", "put this", "with this photo", "with this image"]) and target_screen:
        comps = target_screen.setdefault("components", [])
        new_img_comp = {
            "type": "image",
            "props": {
                "title": "Updated Visual Prototype / Screenshot",
                "image_url": image_url_val,
                "caption": "Replaced component with user uploaded mockup"
            }
        }
        # Check if user mentioned replacing a specific component (e.g. table, chart, kpi, button)
        replaced = False
        for idx, c in enumerate(comps):
            c_type = c.get("type", "").lower()
            c_title = c.get("props", {}).get("title", "").lower()
            if any(term in instr_lower for term in [c_type, c_title]) and len(c_type) > 2:
                comps[idx] = new_img_comp
                replaced = True
                print(f"[Simulation Chat] Replaced existing component '{c_type}' with uploaded photo")
                break
        if not replaced:
            comps.append(new_img_comp)
        return updated

    image_clause = ""
    if image_url_val:
        image_clause = f"""An image/screenshot was uploaded. If user asked to replace an existing component or insert this image, insert or replace that component in the 'components' array with:
{{
  "type": "image",
  "props": {{
    "title": "Uploaded Prototype / Screenshot",
    "image_url": "USER_UPLOADED_IMAGE_PLACEHOLDER",
    "caption": "Referenced UI wireframe from user upload"
  }}
}}"""

    screen_to_modify = target_screen or {}
    existing_comps = screen_to_modify.get("components", [])

    refine_prompt = f"""Target Screen (Existing state):
{json.dumps(screen_to_modify, indent=2)}

User Instruction:
"{user_instruction}"
{image_clause}

CRITICAL INSTRUCTIONS:
1. PRESERVE EXISTING COMPONENTS: You MUST keep ALL current components in "components" list and only APPEND or MODIFY the requested component, unless user explicitly says "remove" or "delete". DO NOT wipe out existing components!
2. COMPONENT PLACEMENT & POSITIONING:
   - If user asks to add something "to the right of" or "next to" an existing KPI card, ADD IT AS AN ITEM INSIDE THE SAME "stats_grid" component's "items" list, so it renders horizontally side-by-side! DO NOT create a new widget at the bottom.
   - If user asks to place a component "at the top", "above X", or "below Y", insert it at the exact requested index in the "components" array. Do NOT just dump everything at the very bottom.
3. SUPPORTED COMPONENT TYPES & FORMAT:
   - "pie_chart": {{"type": "pie_chart", "props": {{"title": "Distribution", "items": [{{"label": "Direct", "value": 45}}, {{"label": "Partner", "value": 35}}, {{"label": "Online", "value": 20}}]}}}}
   - "bar_chart": {{"type": "bar_chart", "props": {{"title": "Monthly Performance", "items": [{{"label": "Q1", "value": "85%"}}, {{"label": "Q2", "value": "92%"}}, {{"label": "Q3", "value": "88%"}}]}}}}
   - "timeline_chart": {{"type": "timeline_chart", "props": {{"title": "Milestones", "stages": ["Phase 1", "Phase 2", "Phase 3"]}}}}
   - "stats_grid": {{"type": "stats_grid", "props": {{"title": "Key Metrics", "items": ["Revenue: $450K", "Growth: +18%", "Active: 24"]}}}}
   - "action_table": {{"type": "action_table", "props": {{"title": "Data Overview", "columns": ["Item", "Category", "Status"], "rows": [{{"col_1": "Order #101", "col_2": "Retail", "status": "Active"}}]}}}}
   - "action_card": {{"type": "action_card", "props": {{"title": "Action Title", "description": "Details...", "actions": ["Approve", "Review"]}}}}
   - "button": {{"type": "button", "props": {{"title": "Button Title", "action": "Submit"}}}}
   - "input_field": {{"type": "input_field", "props": {{"label": "Field Label", "placeholder": "Enter value..."}}}}

Return ONLY the complete updated screen JSON object with ALL components preserved and placed in their correct positions.
No markdown, no explanation, only valid JSON.
"""
    try:
        res = query_llm(
            "You are an interactive UI screen modifier. Return ONLY valid JSON for the single target screen.",
            refine_prompt,
            temperature=0.1,
            max_tokens=2048,
            json_mode=True,
            timeout=50
        )
        parsed_screen = safe_json_loads(res, None)
        if isinstance(parsed_screen, dict) and "components" in parsed_screen:
            # Rehydrate image placeholder if present
            if image_url_val:
                for c in parsed_screen.get("components", []):
                    if c.get("type") in ["image", "banner"] and c.get("props", {}).get("image_url") == "USER_UPLOADED_IMAGE_PLACEHOLDER":
                        c["props"]["image_url"] = image_url_val
            if target_screen:
                screens[target_idx] = parsed_screen
            else:
                screens.append(parsed_screen)
            updated["screens"] = screens
            return updated
    except Exception as e:
        print(f"[Simulation Chat LLM Error] {e}")

    return current_schema


