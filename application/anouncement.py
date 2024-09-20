from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import boto3
import os
from .model import db, Announcement

announcement_bp = Blueprint('announcement', __name__)



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
        folder_name = "Announcement"
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
    



@announcement_bp.route('/announcements', methods=['POST'])
def create_announcement():
    title = request.form.get('title')
    image_file = request.files.get('image')

    if not title or not image_file:
        return jsonify({"error": "Title and image are required"}), 400

    # Use the helper function to upload the image to S3
    image_url = upload_to_s3(image_file, S3_BUCKET)

    if not image_url:
        return jsonify({"error": "Failed to upload image to S3"}), 500

    # Create a new announcement
    announcement = Announcement(title=title, image_url=image_url)
    db.session.add(announcement)
    db.session.commit()

    return jsonify({"message": "Announcement created", "id": announcement.id}), 201

@announcement_bp.route('/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.all()
    return jsonify([{"id": a.id, "title": a.title, "image_url": a.image_url} for a in announcements]), 200

@announcement_bp.route('/announcements/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    announcement = Announcement.query.get(id)
    if announcement is None:
        return jsonify({"error": "Announcement not found"}), 404

    # Optionally, delete the image from S3
    # s3_client.delete_object(Bucket=S3_BUCKET, Key=announcement.image_url.split('/')[-1])

    db.session.delete(announcement)
    db.session.commit()
    return jsonify({"message": "Announcement deleted"}), 204
