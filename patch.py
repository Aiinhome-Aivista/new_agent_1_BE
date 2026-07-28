import re
with open('agents/orchestrator.py', 'r') as f:
    text = f.read()

# For Phase 1
text = text.replace(
    '        update_step_status(proposal_id, "Ingesting", "running", "Processing RFP files, reading case studies, and chunking into ArangoDB...")',
    '        if "Ingesting" not in completedd, "Analyzing", "running", "Extracting requirements & querying internal assets repository (RAG)...")',
    '        if "Analyzing" not in complet_steps:\n            update_step_status(proposal_id, "Ingesting", "running", "Processing RFP files, reading case studies, and chunking into ArangoDB...")'
)

text = text.replace(
    '        update_step_status(proposal_ied_steps:\n            update_step_status(proposal_id, "Analyzing", "running", "Extracting requirements & querying internal assets repository (RAG)...")'
)

text = text.replace(
    '        for step in STEPS:\n            update_step_status(proposal_id, step, "failed", f"Failed due to error: {str(e)}\\n{tb}")',
    '        for step in STEPS:\n            if step not in completed_steps:\n                update_step_status(proposal_id, step, "failed", f"Failed due to error: {str(e)}\\n{tb}")'
)

# Insert completed_steps block
insert_pos = text.find('    try:\n        # Initialize LangChain Agents')
block = '''    completed_steps = set()
    if resume:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True) if hasattr(conn.cursor, 'dictionary') else conn.cursor()
            cursor.execute("SELECT step_name, status FROM proposal_steps WHERE proposal_id = %s", (proposal_id,))
            for r in cursor.fetchall():
                if (r.get('status') if isinstance(r, dict) else r[1]) == 'completed':
                    completed_steps.add(r.get('step_name') if isinstance(r, dict) else r[0])
            cursor.close()
            conn.close()
        except: pass
'''
text = text[:insert_pos] + block + text[insert_pos:]

# For Phase 2
text = text.replace(
    '        update_step_status(proposal_id, "Designing", "running", f"Designing technical solution using {ui_tech}, {backend_tech}, {db_tech}...")',
    '        if "Designing" not in completed_steps:\n            update_step_status(proposal_id, "Designing", "running", f"Designing technical solution using {ui_tech}, {backend_tech}, {db_tech}...")'
)

text = text.replace(
    '        update_step_status(proposal_id, "Planning", "running", "Calculating resources loading, rates sizing, and deliverables timeline...")',
    '        if "Planning" not in completed_steps:\n            update_step_status(proposal_id, "Planning", "running", "Calculating resources loading, rates sizing, and deliverables timeline...")'
)

text = text.replace(
    '        update_step_status(proposal_id, "Assembling", "running", "Assembling final proposal content and running Reflexion quality checks...")',
    '        if "Assembling" not in completed_steps:\n            update_step_status(proposal_id, "Assembling", "running", "Assembling final proposal content and running Reflexion quality checks...")'
)

text = text.replace(
    '        update_step_status(proposal_id, "Complete", "running", "Rendering slides into brand-compliant PowerPoint deliverable...")',
    '        if "Complete" not in completed_steps:\n            update_step_status(proposal_id, "Complete", "running", "Rendering slides into brand-compliant PowerPoint deliverable...")'
)

insert_pos_2 = text.find('    try:\n        # Retrieve the partial state')
block_2 = '''    completed_steps = set()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) if hasattr(conn.cursor, 'dictionary') else conn.cursor()
        cursor.execute("SELECT step_name, status FROM proposal_steps WHERE proposal_id = %s", (proposal_id,))
        for r in cursor.fetchall():
            if (r.get('status') if isinstance(r, dict) else r[1]) == 'completed':
                completed_steps.add(r.get('step_name') if isinstance(r, dict) else r[0])
        cursor.close()
        conn.close()
    except: pass
'''
text = text[:insert_pos_2] + block_2 + text[insert_pos_2:]

with open('agents/orchestrator.py', 'w') as f:
    f.write(text)
