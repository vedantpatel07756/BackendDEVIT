# from flask import Flask, request, jsonify,Blueprint
# from .model import db, Highlight
# from werkzeug.utils import secure_filename
# from datetime import datetime
# import boto3

# # Create a Blueprint for the 'auth' module
# highlight_bp = Blueprint('highlight', __name__)


# # AWS S3 Configuration
# S3_BUCKET = 'devitapp'
# S3_ACCESS_KEY = 'AKIA4HWJUIFV7QKGFWD5'
# S3_SECRET_KEY = 'QmI7Y6UyKC620E59JudSUTYleZauC4YeCnx1i0HL'
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




# @highlight_bp.route('/highlight', methods=['POST'])
# def create_highlight():
#     try:
#         data = request.form
#         name = data.get('name')
        
#         if 'image' not in request.files:
#             # logging.error("No image file found in request.")
#             return jsonify({"error": "Image file is required"}), 400
        
#         image = request.files['image']
#         if not name:
#             # logging.error("Name is required but not provided.")
#             return jsonify({"error": "Name is required"}), 400

#         filename = secure_filename(image.filename)
        
#         # Replace with your actual upload function
#         image_url = upload_to_s3(image,S3_BUCKET)
        
#         if not image_url:
#             # logging.error("Failed to upload image to S3.")
#             return jsonify({"error": "Failed to upload image to S3"}), 500
        
#         highlight = Highlight(name=name, image_url=image_url, date=datetime.utcnow())
#         db.session.add(highlight)
#         db.session.commit()
        
#         return jsonify({
#             "message": "Highlight created successfully",
#             "highlight": {
#                 "id": highlight.id,
#                 "name": highlight.name,
#                 "image_url": highlight.image_url,
#                 "date": highlight.date  # Format date as ISO string
#             }
#         }), 201 

#     except Exception as e:
#         # logging.exception("An error occurred while creating a highlight.")
#         return jsonify({"error": str(e)}), 500


# # Get all highlights
# @highlight_bp.route('/highlights', methods=['GET'])
# def get_highlights():
#     highlights = Highlight.query.all()
#     print(highlights[0].date)
    
#     highlight_list = [{
#         "id": h.id,
#         "name": h.name,
#         "image_url": h.image_url,
#         "date": h.date[:10]
#     } for h in highlights]
    
#     return jsonify(highlight_list), 200


# # Delete a highlight by ID
# @highlight_bp.route('/highlight/<int:id>', methods=['DELETE'])
# def delete_highlight(id):
#     highlight = Highlight.query.get_or_404(id)
    
#     # Optionally, remove the image from S3
#     # You would have to implement a method to delete the file from S3 using `boto3` here if necessary
    
#     db.session.delete(highlight)
#     db.session.commit()
    
#     return jsonify({"message": "Highlight removed successfully"}), 200




import os
from flask import Flask, request, jsonify, Blueprint
from .model import Eventcount, db, Highlight
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import boto3
import io

# Create a Blueprint for the 'auth' module
highlight_bp = Blueprint('highlight', __name__)

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

# Helper function to resize and compress the image
def resize_image(image, max_size_kb=500):
    img = Image.open(image)
    output = io.BytesIO()
    
    # Resize the image by adjusting its quality until it's under the desired size limit
    quality = 85  # Start with high quality
    img.save(output, format=img.format, quality=quality)
    while output.tell() > max_size_kb * 1024 and quality > 10:
        quality -= 5
        output.seek(0)
        img.save(output, format=img.format, quality=quality)
    
    output.seek(0)
    return output

# Helper function to upload an image to AWS S3
def upload_to_s3(file, bucket_name, filename, acl="public-read"):
    try:
        folder_name = "Highlight"
        full_s3_path = f"{folder_name}/{filename}"

        s3.upload_fileobj(
            file,
            bucket_name,
            full_s3_path,
            ExtraArgs={
                "ACL": acl,
                "ContentType": "image/jpeg"  # Set content type explicitly, or use file.content_type if needed
            }
        )
        
        return f"https://{bucket_name}.s3.{S3_REGION}.amazonaws.com/{full_s3_path}"
    
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
    

# Helper function to delete an image from AWS S3
def delete_from_s3(bucket_name, s3_key):
    try:
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Deleted {s3_key} from S3")
    except Exception as e:
        print(f"Error deleting from S3: {e}")
# Create Highlight
@highlight_bp.route('/highlight', methods=['POST'])
def create_highlight():
    try:
        data = request.form
        name = data.get('name')

        if 'image' not in request.files:
            return jsonify({"error": "Image file is required"}), 400
        
        image = request.files['image']
        if not name:
            return jsonify({"error": "Name is required"}), 400

        # Resize the image before uploading
        resized_image = resize_image(image)

        # Use the original filename for the S3 upload
        filename = secure_filename(image.filename)

        # Upload resized image to S3
        image_url = upload_to_s3(resized_image, S3_BUCKET, filename)
        if not image_url:
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
                "date": highlight.date
            }
        }), 201 

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# # Get all highlights
# @highlight_bp.route('/highlights', methods=['GET'])
# def get_highlights():
#     highlights = Highlight.query.all()
#     highlight_list = [{
#         "id": h.id,
#         "name": h.name,
#         "image_url": h.image_url,
#         "date": h.date  # Format date as ISO string
#     } for h in highlights]
    
#     return jsonify(highlight_list), 200


@highlight_bp.route('/highlights', methods=['GET'])
def get_highlights():
    # Get all highlights
    highlights = Highlight.query.all()
    highlight_list = [{
        "id": h.id,
        "name": h.name,
        "image_url": h.image_url,
        "date": h.date  # Format date as ISO string
    } for h in highlights]

    # Calculate totals for eventcount, participant, and feedback
    total_eventcount = db.session.query(db.func.sum(Eventcount.eventcount)).scalar() or 0
    total_participant = db.session.query(db.func.sum(Eventcount.participant)).scalar() or 0
    total_feedback = db.session.query(db.func.sum(Eventcount.feedback)).scalar() or 0

    # Prepare the response with totals and highlights
    response = {
        "highlights": highlight_list,
        "totals": {
            "total_eventcount": total_eventcount,
            "total_participant": total_participant,
            "total_feedback": total_feedback
        }
    }
    
    return jsonify(response), 200


# Delete a highlight by ID
@highlight_bp.route('/highlight/<int:id>', methods=['DELETE'])
def delete_highlight(id):
    highlight = Highlight.query.get_or_404(id)

    # Extract the S3 key from the image URL
    s3_key = highlight.image_url.split(f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]

    # Delete image from S3
    delete_from_s3(S3_BUCKET, s3_key)

    db.session.delete(highlight)
    db.session.commit()

    return jsonify({"message": "Highlight removed successfully"}), 200
