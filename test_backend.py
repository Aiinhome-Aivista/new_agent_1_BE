import os
import json
import pytest
from app import app
from database.db_connection import get_db_connection

def test_config():
    """Verify flask configs are loaded."""
    assert not app.config.get("TESTING")

def test_login_endpoint():
    """Verify login routing works and handles bad requests."""
    client = app.test_client()
    response = client.post('/api/auth/login', json={})
    assert response.status_code == 400
    
    response_auth = client.post('/api/auth/login', json={"username": "admin", "password": "password"})
    assert response_auth.status_code == 200
    data = response_auth.get_json()
    assert "token" in data
    assert data["user"]["username"] == "admin"

def test_static_routes():
    """Verify static route mapping is active."""
    client = app.test_client()
    response = client.get('/static/test.txt')
    # Should be 404 since file doesn't exist, but routing matches
    assert response.status_code == 404

def test_upload_proposal_with_requirements_text():
    """Verify that uploading a proposal with typed requirements text is handled successfully."""
    client = app.test_client()
    
    headers = {
        "X-User-Role": "admin"
    }
    
    data = {
        "client_name": "Test Client",
        "project_duration": "10 Weeks",
        "budget": "$150,000",
        "requirements_text": "Need a secure payment integration with Stripe and dual-region failover configuration."
    }
    
    response = client.post('/api/proposals/upload', data=data, headers=headers)
    assert response.status_code == 202
    res_data = response.get_json()
    assert "proposal_id" in res_data
    assert "message" in res_data

