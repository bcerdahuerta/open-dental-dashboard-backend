from flask import jsonify, request
from marshmallow import ValidationError
from ..schemas import login_schema

def login():
    """
    User Login
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
      400:
        description: No input data provided
      401:
        description: Bad credentials or inactive user
      422:
        description: Validation error
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"msg": "No input data provided"}), 400

    try:
        validated_data = login_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422 # 422 Unprocessable Entity

    email = validated_data.get("email")
    password = validated_data.get("password")

    return jsonify({"msg": "Bad credentials or inactive user"}), 401
