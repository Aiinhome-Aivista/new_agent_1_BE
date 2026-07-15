import os
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

# Serve static files (uploads and generated presentations)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ----------------------------------------------------
# DIRECT PATH API ROUTES (NO BLUEPRINTS)
# ----------------------------------------------------

@app.route('/api/auth/login', methods=['POST'])
def login():
    return auth_controller.login()

@app.route('/api/proposals/upload', methods=['POST'])
def upload_proposal():
    return proposal_controller.upload_proposal()

@app.route('/api/proposals', methods=['GET'])
def get_proposals_list():
    return proposal_controller.get_proposals_list()

@app.route('/api/proposals/status/<proposal_id>', methods=['GET'])
def get_proposal_status(proposal_id):
    return proposal_controller.get_proposal_status(proposal_id)

@app.route('/api/proposals/edit/<proposal_id>', methods=['POST'])
def edit_proposal_ir(proposal_id):
    return proposal_controller.edit_proposal_ir(proposal_id)

@app.route('/api/proposals/download/<proposal_id>', methods=['GET'])
def download_proposal_pptx(proposal_id):
    return proposal_controller.download_proposal_pptx(proposal_id)

# Knowledge retrieval routes (for viewing seeded RAG data in settings)
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
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

if __name__ == '__main__':
    # Initialize the database structures
    print("Initializing database...")
    init_db()
    
    # Ensure static directories exist
    os.makedirs(os.path.join(os.getcwd(), 'static', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), 'static', 'proposals'), exist_ok=True)
    
    port = int(os.getenv("PORT", 5000))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
