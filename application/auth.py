from flask import Blueprint, request, jsonify
from .model import db, User


# from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
# Import the User model and db from your models
import boto3
import os

# Create a Blueprint for the 'auth' module
auth_bp = Blueprint('auth', __name__)




# AWS S3 Configuration
S3_BUCKET = 'devitapp'
S3_ACCESS_KEY = 'AKIA4HWJUIFVTEMTCE6Q'
S3_SECRET_KEY = 'NYFVNSq6teVtM7NHxrUbj4x+a11B3W3JMEbos8r1'
S3_REGION = 'ap-southeast-2'  # Example: 'us-east-1'

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# Helper function to upload an image to AWS S3
def upload_to_s3(file, bucket_name, acl="public-read"):
    try:
        # Prepend the folder name to the filename
        folder_name = "Profile Photo"
        filename = secure_filename(file.filename)
        full_s3_path = f"{folder_name}/{filename}"  # Store in 'Profile Photo' folder

        # Upload the file to S3 with the folder path
        s3.upload_fileobj(
            file,
            bucket_name,
            full_s3_path,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
        
        # Return the public URL of the uploaded file
        return f"https://{bucket_name}.s3.{S3_REGION}.amazonaws.com/{full_s3_path}"
    
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
    

# Update View 

@auth_bp.route('/submitForm/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        # Fetch the user from the database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Update user fields from the request (if provided)
        user.fullname = request.form.get('name', user.fullname)
        user.email = request.form.get('email', user.email)
        user.phonenumber = request.form.get('phoneNumber', user.phonenumber)
        user.year = request.form.get('year', user.year)
        user.branch = request.form.get('branch', user.branch)
        user.post = request.form.get('postRequest', user.post)
        user.verify = request.form.get('verify', "PENDING")
        

        # Handle image file (if provided)
        if 'image' in request.files:
            image = request.files['image']
            # Upload the image to S3 and get the URL
            image_url = upload_to_s3(image, S3_BUCKET)
            if image_url:
                user.photo = image_url

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'User updated successfully', 'user_id': user_id}), 200

    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({'message': 'Error updating user'}), 500

    



# Register view 

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Assuming the request sends JSON data
    
    # Extract data from the request
    fullname = data.get('fullname')
    email = data.get('email')
    phonenumber = data.get('phonenumber')
    password = data.get('password')

    # Check if the email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already exists!"}), 409

    # Create a new user instance
    new_user = User(fullname=fullname, email=email, phonenumber=phonenumber, password=password,year="NULL",branch="NULL",post="Volunteer",verify="DONE",photo="NULL",attandance=0,total_point=0)
    
    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201



# Login view 
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Assuming the request sends JSON data
    
    # Extract data from the request
    email = data.get('email')
    password = data.get('password')

    # Query the user by email
    user = User.query.filter_by(email=email).first()

    # Check if the user exists and the password matches
    if user and user.password == password:
        # Pass the user ID from the database
        return jsonify({
            "message": "Login successful!",
            "user_id": user.id,  # Retrieve the user ID from the database
            "user_name":user.fullname
        }), 200
    else:
        return jsonify({"message": "Invalid email or password!"}), 401



# Get Profile Detail 
    
@auth_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    try:
        # Query the user by user_id
        user = User.query.get(user_id)

        # If the user doesn't exist, return an error
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Convert the user object to a dictionary
        user_details = {
            'id': user.id,
            'fullname': user.fullname,
            'email': user.email,
            'phonenumber': user.phonenumber,
            'year': user.year,
            'branch': user.branch,
            'post': user.post,
            'verify': user.verify,
            'photo': user.photo,
            'attendance': user.attandance,
            'total_point': user.total_point
        }

        # Return the user details as JSON
        return jsonify(user_details), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Get all member data at once 
    
@auth_bp.route('/members', methods=['GET'])
def get_members():
    try:
        # Query all users from the database
        users = User.query.all()
        
        # Create a list of dictionaries with user data
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'fullname': user.fullname,
                'email': user.email,
                'phonenumber': user.phonenumber,
                'year': user.year,
                'branch': user.branch,
                'post': user.post,
                'verify': user.verify,
                'photo': user.photo,
                'attandance': user.attandance,
                'total_point': user.total_point
            }
            users_data.append(user_data)
        
        # Return the data as JSON
        return jsonify(users_data)
    
    except Exception as e:
        # Handle any exceptions
        return jsonify({'error': str(e)}), 500