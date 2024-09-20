from flask import Flask, request, jsonify,Blueprint
from .model import db, Highlight
from werkzeug.utils import secure_filename
from datetime import datetime
import boto3

# Create a Blueprint for the 'auth' module
highlight_bp = Blueprint('highlight', __name__)


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


# # AWS S3 Configuration
# S3_BUCKET = 'devitapp'
# S3_ACCESS_KEY = 'AKIA4HWJUIFVTEMTCE6Q'
# S3_SECRET_KEY = 'NYFVNSq6teVtM7NHxrUbj4x+a11B3W3JMEbos8r1'
# S3_REGION = 'ap-southeast-2'  # Example: 'us-east-1'

# # Initialize S3 client
# s3 = boto3.client(
#     's3',
#     aws_access_key_id=S3_ACCESS_KEY,
#     aws_secret_access_key=S3_SECRET_KEY,
#     region_name=S3_REGION
# )

# # Helper function to upload an image to AWS S3
# def upload_to_s3(file, bucket_name, acl="public-read"):
#     try:
#         # Prepend the folder name to the filename
#         folder_name = "Highlight"
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
    


# # Create Highlight (with image upload)
# @highlight_bp.route('/highlight', methods=['POST'])
# def create_highlight():
#     data = request.form  # Use form data to capture the fields
#     name = data.get('name')
    
#     if 'image' not in request.files:
#         return jsonify({"error": "Image file is required"}), 400
    
#     image = request.files['image']
#     if name is None or not name:
#         return jsonify({"error": "Name is required"}), 400

#     filename = secure_filename(image.filename)
    
#     # Upload the file to AWS S3 and get the URL
#     image_url = upload_to_s3(image, filename)
    
#     if image_url is None:
#         return jsonify({"error": "Failed to upload image to S3"}), 500
    
#     # Create a new highlight and save to database
#     highlight = Highlight(name=name, image_url=image_url, date=datetime.utcnow())
#     db.session.add(highlight)
#     db.session.commit()
    
#     return jsonify({
#         "message": "Highlight created successfully",
#         "highlight": {
#             "id": highlight.id,
#             "name": highlight.name,
#             "image_url": highlight.image_url,
#             "date": highlight.date
#         }
#     }), 201


@highlight_bp.route('/highlight', methods=['POST'])
def create_highlight():
    try:
        data = request.form
        name = data.get('name')
        
        if 'image' not in request.files:
            # logging.error("No image file found in request.")
            return jsonify({"error": "Image file is required"}), 400
        
        image = request.files['image']
        if not name:
            # logging.error("Name is required but not provided.")
            return jsonify({"error": "Name is required"}), 400

        filename = secure_filename(image.filename)
        
        # Replace with your actual upload function
        image_url = upload_to_s3(image,S3_BUCKET)
        
        if not image_url:
            # logging.error("Failed to upload image to S3.")
            return jsonify({"error": "Failed to upload image to S3"}), 500
        
        highlight = Highlight(name=name, image_url=image_url, date=datetime.utcnow())
        db.session.add(highlight)
        db.session.commit()
        
        return jsonify({
            "message": "Highlight created successfully",
            "highlight": {
                "id": highlight.id,
                "name": highlight.name,
                "image_url": highlight.image_url,
                "date": highlight.date  # Format date as ISO string
            }
        }), 201 

    except Exception as e:
        # logging.exception("An error occurred while creating a highlight.")
        return jsonify({"error": str(e)}), 500


# Get all highlights
@highlight_bp.route('/highlights', methods=['GET'])
def get_highlights():
    highlights = Highlight.query.all()
    print(highlights[0].date)
    
    highlight_list = [{
        "id": h.id,
        "name": h.name,
        "image_url": h.image_url,
        "date": h.date[:10]
    } for h in highlights]
    
    return jsonify(highlight_list), 200


# Delete a highlight by ID
@highlight_bp.route('/highlight/<int:id>', methods=['DELETE'])
def delete_highlight(id):
    highlight = Highlight.query.get_or_404(id)
    
    # Optionally, remove the image from S3
    # You would have to implement a method to delete the file from S3 using `boto3` here if necessary
    
    db.session.delete(highlight)
    db.session.commit()
    
    return jsonify({"message": "Highlight removed successfully"}), 200