from flask import Flask, request, jsonify,Blueprint
from .model import db, UserRole, User  # Assuming models are imported from models.py
from sqlalchemy.exc import IntegrityError



# Create a Blueprint for the 'auth' module
userrole_bp = Blueprint('userrole', __name__)


# Create User ROle

@userrole_bp.route('/create_user_role', methods=['POST'])
def create_user_role():
    # Parse JSON data from request
    data = request.get_json()
    email = data.get('email')
    permission = data.get('permission')

    # Validate email and permission
    if not email or not permission:
        return jsonify({"error": "Email and permission are required"}), 400
    
    if permission not in ['basic', 'manager', 'full access']:
        return jsonify({"error": "Invalid permission value"}), 400

    # Find the user by email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Create a new user role
    new_user_role = UserRole(
        user_id=user.id,
        email_id=email,
        permission=permission
    )

    # Add to the database
    db.session.add(new_user_role)
    db.session.commit()

    return jsonify({"message": "User role created successfully"}), 201



# get user Role 


@userrole_bp.route('/get_user_roles', methods=['GET'])
def get_user_roles():
    # Query to join User and UserRole tables
    user_roles = db.session.query(UserRole, User).join(User, User.id == UserRole.user_id).all()

    # Format the result as a list of dictionaries
    result = []
    for user_role, user in user_roles:
        result.append({
            "email_id": user_role.email_id,
            "fullname": user.fullname,
            "permission": user_role.permission,
            "photo": user.photo,
            "user_id":user.id
        })

    # Return the result as JSON
    return jsonify(result), 200



# delete 

@userrole_bp.route('/delete_user_role/<int:user_id>', methods=['DELETE'])
def delete_user_role(user_id):
    try:
        # Find the user role by user_id
        user_role = UserRole.query.filter_by(user_id=user_id).first()

        if not user_role:
            return jsonify({"error": "User role not found"}), 404

        # Delete the user role
        db.session.delete(user_role)
        db.session.commit()

        return jsonify({"message": "User role deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500