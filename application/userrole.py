from flask import Flask, request, jsonify,Blueprint
from .model import db, UserRole, User  # Assuming models are imported from models.py
from sqlalchemy.exc import IntegrityError



# Create a Blueprint for the 'auth' module
userrole_bp = Blueprint('userrole', __name__)

# Define a route to handle the JSON data for creating a user role
@userrole_bp.route('/user-role', methods=['POST'])
def create_user_role():
    try:
        # Extract data from the request's JSON payload
        data = request.get_json()

        # Ensure all necessary data is provided
        if 'user_id' not in data or 'permission' not in data:
            return jsonify({'error': 'Missing user_id or permission in request body'}), 400

        user_id = data['user_id']
        permission = data['permission']

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Create a new UserRole entry
        user_role = UserRole(user_id=user_id, permission=permission)
        db.session.add(user_role)
        db.session.commit()

        return jsonify({'message': 'User role created successfully'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Integrity error, possibly duplicate entry'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
