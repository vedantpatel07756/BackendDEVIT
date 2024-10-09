# from urllib.request import Request
from flask import Blueprint, render_template, request, jsonify,flash,url_for,redirect
from .model import UserRole, db, User,Request


# from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
# Import the User model and db from your models
import boto3
import os

# Create a Blueprint for the 'auth' module
auth_bp = Blueprint('auth', __name__)




# AWS S3 Configuration
# Retrieve environment variables
S3_BUCKET = os.getenv('S3_BUCKET')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_REGION = os.getenv('S3_REGION')

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)


# # Helper function to upload an image to AWS S3
# def upload_to_s3(file, bucket_name, acl="public-read"):
#     try:
#         # Prepend the folder name to the filename
#         folder_name = "Profile Photo"
#         filename = secure_filename(file.filename)
#         full_s3_path = f"{folder_name}/{filename}"  # Store in 'Profile Photo' folder

#         # Upload the file to S3 with the folder path
#         s3.upload_fileobj(
#             file,
#             bucket_name,
#             full_s3_path,
#             ExtraArgs={
#                 "ACL": acl,
#                 "ContentType": file.content_type
#             }
#         )
        
#         # Return the public URL of the uploaded file
#         return f"https://{bucket_name}.s3.{S3_REGION}.amazonaws.com/{full_s3_path}"
    
#     except Exception as e:
#         print(f"Error uploading to S3: {e}")
#         return None
    

# Helper function to upload an image to AWS S3
def upload_to_s3(file, bucket_name, file_name, content_type='image/jpeg', acl="public-read"):
    try:
        # Prepend the folder name to the filename
        folder_name = "Profilephoto"
        full_s3_path = f"{folder_name}/{file_name}"  # Store in 'Profile Photo' folder

        # Upload the file to S3 with the folder path
        s3.upload_fileobj(
            file,
            bucket_name,
            full_s3_path,
            ExtraArgs={
                "ACL": acl,
                "ContentType": content_type
            }
        )
        
        # Return the public URL of the uploaded file
        return f"https://{bucket_name}.s3.amazonaws.com/{full_s3_path}"
    
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


# Web View 

@auth_bp.route('/', methods=['POST','GET'])
def Home():
    return render_template('index.html')



@auth_bp.route('/web/login', methods=['GET', 'POST'])
def weblogin():
    if request.method == 'POST':
        # Get data from form
        email = request.form.get('email').lower()
        password = request.form.get('password')

        # Query the user by email
        user = User.query.filter_by(email=email).first()

        # Check if the user exists and password matches
        if user and user.password == password:
            # Successful login - Pass user data as JSON if needed
            return redirect(url_for('webpage.dashboard'))
        else:
            # Invalid login attempt
            flash('Invalid email or password!', 'danger')
            return render_template('index.html')

    # Render the login page for GET requests
    return render_template('index.html')



# app view below





# Update View 
from PIL import Image
import io
import time

@auth_bp.route('/submitForm/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        # Fetch the user from the database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Update user fields from the request (if provided)
        user.fullname = request.form.get('name', user.fullname).title()
        user.email = request.form.get('email', user.email).lower()
        user.phonenumber = request.form.get('phoneNumber', user.phonenumber)
        user.year = request.form.get('year', user.year)
        user.branch = request.form.get('branch', user.branch)

        # Get the new post request from the form data
        new_post_request = request.form.get('postRequest', user.post)
        
        # Update post and verify status based on the condition
        user.post = new_post_request
        if user.post == new_post_request:
            user.verify = "DONE"
        else:
            user.verify = "PENDING"

        # Handle image file (if provided)
        if 'image' in request.files:
            image = request.files['image']
            
            # Open the image using PIL
            img = Image.open(image)
            
            # Reduce the image size while maintaining the aspect ratio
            img.thumbnail((300, 300))  # Resize to max 300x300 pixels
            
            # Save the resized image to an in-memory file
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', optimize=True, quality=85)
            img_bytes.seek(0)
            
            # Check if image size is still too large, and reduce quality further if needed
            while img_bytes.tell() > 30 * 1024:  # 30KB limit
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', optimize=True, quality=75)  # Reduce quality
                img_bytes.seek(0)

            # Define a filename and upload to S3 with explicit content type
          

            file_name = f"{user.fullname}_{int(time.time())}.jpg"
            image_url = upload_to_s3(img_bytes, S3_BUCKET, file_name, content_type='image/jpeg')
            # user.photo = image_url
            if image_url:
                print("Ongoing")
                # If a new image was successfully uploaded, delete the old image from S3
                if user.photo:
                    old_file_key = user.photo.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[1]
                    try:
                        s3.delete_object(Bucket=S3_BUCKET, Key=old_file_key)
                    except Exception as e:
                        print(f"Error deleting old image from S3: {e}")
                
                # Update the user's photo with the new image URL
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
    fullname = data.get('fullname').title()  # Capitalizes the first letter of each word
    email = data.get('email').lower()  # Converts the entire email to lowercase
    phonenumber = data.get('phonenumber')
    password = data.get('password')
    branch = data.get('branch')
    year = data.get('year')
    rollno=data.get('rollno')

    # Check if the email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already exists!"}), 409

    # Create a new user instance
    new_user = User(fullname=fullname,
                     email=email,
                       phonenumber=phonenumber,
                         password=password,
                         year=year,
                         branch=branch,
                         rollno=rollno,
                         post="Volunteer",
                         verify="DONE",
                         photo="NULL",
                         attandance=0,
                         total_point=0)
    
    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201



# Login view 
# @auth_bp.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()  # Assuming the request sends JSON data
    
#     # Extract data from the request
#     email = data.get('email').lower()
#     password = data.get('password')

#     # Query the user by email
#     user = User.query.filter_by(email=email).first()

#     # Check if the user exists and the password matches
#     if user and user.password == password:
#         # Pass the user ID from the database
#         return jsonify({
#             "message": "Login successful!",
#             "user_id": user.id,  # Retrieve the user ID from the database
#             "user_name":user.fullname
#         }), 200
#     else:
#         return jsonify({"message": "Invalid email or password!"}), 401


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Assuming the request sends JSON data
    
    # Extract data from the request
    email = data.get('email').lower()
    password = data.get('password')

    # Query the user by email
    user = User.query.filter_by(email=email).first()

    # Check if the user exists and the password matches
    if user and user.password == password:
        print(user.post)
        # Check if the user is the President
        if user.post == "President":
            permission = "full access"
            print(user.post)
        else:
            # Fetch the user's role from the UserRole table based on user_id or email
            user_role = UserRole.query.filter_by(user_id=user.id).first()
            
            # If user role is found, assign the role, else default to 'Volunteer'
            permission = user_role.permission if user_role else 'Volunteer'
        
        # Pass the user ID and permission from the database
        return jsonify({
            "message": "Login successful!",
            "user_id": user.id,  
            "user_name": user.fullname,
            "permission": permission
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
            'rollno':user.rollno,
            'post': user.post,
            'verify': user.verify,
            'photo': user.photo,
            'attendance': user.attandance,
            'total_point': user.total_point
        }

        print(user.photo)

        # Return the user details as JSON
        return jsonify(user_details), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Get all member data at once 
    
# @auth_bp.route('/members', methods=['GET'])
# def get_members():
#     try:
#         # Query all users from the database
#         users = User.query.all()
        
#         # Create a list of dictionaries with user data
#         users_data = []
#         for user in users:
#             user_data = {
#                 'id': user.id,
#                 'fullname': user.fullname,
#                 'email': user.email,
#                 'phonenumber': user.phonenumber,
#                 'year': user.year,
#                 'branch': user.branch,
#                 'post': user.post,
#                 'verify': user.verify,
#                 'photo': user.photo,
#                 'attandance': user.attandance,
#                 'total_point': user.total_point
#             }
#             users_data.append(user_data)
        
#         # Return the data as JSON
#         return jsonify(users_data)
    
#     except Exception as e:
#         # Handle any exceptions
#         return jsonify({'error': str(e)}), 500
    


@auth_bp.route('/members', methods=['GET'])
def get_members():
    try:
        # Query all users from the database
        users = User.query.all()
        
        # Create a list of dictionaries with user data including their requests
        users_data = []
        for user in users:
            # Fetch requests associated with this user
            requests = Request.query.filter_by(user_id=user.id).all()
            
            # Create a list of requests with relevant fields
            user_requests = []
            for request in requests:
                request_data = {
                    'id': request.id,
                    'date': request.date.strftime('%d-%m-%y'),  # Format date as string
                    'start_time': request.start_time.strftime('%H:%M:%S'),  # Format time
                    'end_time': request.end_time.strftime('%H:%M:%S'),  # Format time
                    'task_done': request.task_done,
                    'task_desc': request.task_desc,
                    'time_option': request.time_option,
                    'task_point': request.task_point
                }
                user_requests.append(request_data)
            
            # Prepare user data with requests
            user_data = {
                'id': user.id,
                'fullname': user.fullname,
                'email': user.email,
                'phonenumber': user.phonenumber,
                'year': user.year,
                'branch': user.branch,
                'rollno':user.rollno,
                'post': user.post,
                'verify': user.verify,
                'photo': user.photo,
                'attendance': str(user.attandance),
                'total_point':str(user.total_point),
                'requests': user_requests  # Include requests data
            }
            users_data.append(user_data)
        
        # Return the data as JSON
        return jsonify(users_data)
    
    except Exception as e:
        # Handle any exceptions
        return jsonify({'error': str(e)}), 500
