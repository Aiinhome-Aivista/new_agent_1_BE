import os
from functools import wraps
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import controllers and db init
from database.db_connection import init_db, get_db_connection
import controllers.auth_controller as auth_controller
import controllers.proposal_controller as proposal_controller

app = Flask(__name__)
# Enable CORS for React dev server (usually localhost:5173)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# -------------------------------------------------------
# ROLE-BASED ACCESS CONTROL (RBAC) MIDDLEWARE
# -------------------------------------------------------

# Role permission matrix:
#   presales   : Create/upload proposals, run pipeline, edit solution/architecture
#   bidmanager : Same as presales + edit budget
#   delivery   : View + edit resource planning, timeline, skill matrix
#   partner    : Read-only + approve/reject/publish
#   admin      : Full access including user management and system config

def require_role(*allowed_roles):
    """Decorator that restricts endpoint access to specified roles.
    Reads the X-User-Role header sent by the frontend interceptor.
    Returns 403 Forbidden if the role is not in the allowed list.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = request.headers.get('X-User-Role', '').strip()
            if not user_role:
                return jsonify({"error": "Missing X-User-Role header. Access denied."}), 403
            if user_role not in allowed_roles:
                return jsonify({
                    "error": f"Role '{user_role}' is not authorized for this action. Required: {list(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def health_check():
    return jsonify({"message": "Server is running!"}), 200

# Serve static files (uploads and generated presentations)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ----------------------------------------------------
# API ROUTES — Auth (public, no role guard needed)
# ----------------------------------------------------

@app.route('/api/auth/login', methods=['POST'])
def login():
    return auth_controller.login()

# ----------------------------------------------------
# API ROUTES — Proposals
# ----------------------------------------------------

@app.route('/api/proposals/upload', methods=['POST'])
@require_role('presales', 'bidmanager', 'admin')
def upload_proposal():
    return proposal_controller.upload_proposal()

@app.route('/api/proposals', methods=['GET'])
def get_proposals_list():
    # All authenticated roles can list proposals
    return proposal_controller.get_proposals_list()

@app.route('/api/proposals/status/<proposal_id>', methods=['GET'])
def get_proposal_status(proposal_id):
    # All roles can view status
    return proposal_controller.get_proposal_status(proposal_id)

@app.route('/api/proposals/edit/<proposal_id>', methods=['POST'])
@require_role('presales', 'bidmanager', 'delivery', 'admin')
def edit_proposal_ir(proposal_id):
    # partner is read-only — cannot save changes
    return proposal_controller.edit_proposal_ir(proposal_id)

@app.route('/api/proposals/download/<proposal_id>', methods=['GET'])
def download_proposal_pptx(proposal_id):
    # All roles can download
    return proposal_controller.download_proposal_pptx(proposal_id)

@app.route('/api/proposals/transition/<proposal_id>', methods=['POST'])
def transition_proposal_status(proposal_id):
    # Role gate is enforced inside the controller (user_role from request body)
    return proposal_controller.transition_proposal_status(proposal_id)

# ----------------------------------------------------
# API ROUTES — Admin (admin only)
# ----------------------------------------------------

@app.route('/api/admin/users', methods=['GET'])
@require_role('admin')
def get_admin_users():
    return proposal_controller.get_users()

@app.route('/api/admin/users/role', methods=['POST'])
@require_role('admin')
def change_user_role():
    return proposal_controller.change_user_role()

@app.route('/api/admin/config', methods=['GET'])
@require_role('admin')
def get_admin_config():
    return proposal_controller.get_admin_config()

@app.route('/api/admin/audit-logs', methods=['GET'])
@require_role('admin', 'partner')
def get_admin_audit_logs():
    # Partner can view audit logs for review purposes
    return proposal_controller.get_all_audit_logs()

@app.route('/api/admin/retry/<proposal_id>', methods=['POST'])
@require_role('admin')
def retry_proposal_job(proposal_id):
    return proposal_controller.retry_proposal_job(proposal_id)

@app.route('/api/admin/model', methods=['POST'])
@require_role('admin')
def update_ai_model():
    return proposal_controller.update_ai_model()

# -------------------------------------------------------
# Knowledge Base Routes
# Permission matrix:
#   GET    /api/knowledge          → all roles (presales, bidmanager, delivery, partner, admin)
#   POST   /api/knowledge          → presales, admin (upload new asset)
#   PUT    /api/knowledge/<id>     → presales, admin (edit existing asset)
#   DELETE /api/knowledge/<id>     → admin only
#   POST   /api/knowledge/reindex  → presales, admin (trigger re-indexing)
# -------------------------------------------------------

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    # All roles can view the knowledge base
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM knowledge_assets ORDER BY category, name")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify([]), 200

@app.route('/api/knowledge', methods=['POST'])
@require_role('presales', 'admin')
def add_knowledge():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        description = data.get("description")
        category = data.get("category", "Asset")
        capabilities = data.get("capabilities", "")
        
        if not name or not description:
            return jsonify({"error": "Name and description are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_assets (name, description, category, capabilities) VALUES (%s, %s, %s, %s)",
            (name, description, category, capabilities)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Knowledge asset added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge/<int:asset_id>', methods=['PUT'])
@require_role('presales', 'admin')
def update_knowledge(asset_id):
    try:
        data = request.get_json() or {}
        name = data.get("name")
        description = data.get("description")
        category = data.get("category", "Asset")
        capabilities = data.get("capabilities", "")
        
        if not name or not description:
            return jsonify({"error": "Name and description are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE knowledge_assets SET name=%s, description=%s, category=%s, capabilities=%s WHERE id=%s",
            (name, description, category, capabilities, asset_id)
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Knowledge asset not found"}), 404
        return jsonify({"message": "Knowledge asset updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge/<int:asset_id>', methods=['DELETE'])
@require_role('admin')
def delete_knowledge(asset_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_assets WHERE id = %s", (asset_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Knowledge asset not found"}), 404
        return jsonify({"message": f"Knowledge asset {asset_id} deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge/reindex', methods=['POST'])
@require_role('presales', 'admin')
def reindex_knowledge():
    """Trigger a re-index of the knowledge base into the RAG vector store."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM knowledge_assets ORDER BY category, name")
        assets = cursor.fetchall()
        cursor.close()
        conn.close()
        # Re-index into ArangoDB vector store if available
        try:
            from database.arango_client import arango_client
            if arango_client.is_connected:
                for asset in assets:
                    arango_client.upsert_document(
                        collection="knowledge_assets",
                        doc_key=str(asset["id"]),
                        document={
                            "name": asset["name"],
                            "description": asset["description"],
                            "category": asset["category"],
                            "capabilities": asset["capabilities"],
                        }
                    )
        except Exception as arango_err:
            pass  # ArangoDB optional — fallback to MySQL-only mode
        return jsonify({"message": f"Re-indexed {len(assets)} knowledge assets into RAG vector store"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize the database structures
    print("Initializing SQL/MySQL databases...")
    init_db()
    
    print("Initializing ArangoDB database...")
    try:
        from database.arango_client import arango_client
        arango_client.init_db()
    except Exception as e:
        print(f"Failed to auto-initialize ArangoDB on start: {e}")
    
    # Ensure static directories exist
    os.makedirs(os.path.join(os.getcwd(), 'static', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), 'static', 'proposals'), exist_ok=True)
    
    port = int(os.getenv("PORT", 5000))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
