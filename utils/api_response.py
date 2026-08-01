from flask import jsonify

def success_response(data, message="Success", status_code=200):
    return jsonify({
        "status": "success",
        "statusCode": status_code,
        "message": message,
        "data": data,
        "errors": []
    }), status_code

def error_response(message, errors=None, status_code=400):
    return jsonify({
        "status": "failed",
        "statusCode": status_code,
        "message": message,
        "data": {},
        "errors": errors or []
    }), status_code
