


from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import boto3
import os
from io import BytesIO
from PIL import Image
from .model import db, Announcement

announcement_bp = Blueprint('announcement', __name__)

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

# Resize image to ensure it is within the 500KB limit
def resize_image(image):
    img = Image.open(image)
    img_format = img.format  # Preserve original format
    max_size = (1024, 1024)  # Set max resolution as needed
    img.thumbnail(max_size)

    # Save resized image to a BytesIO object
    buffer = BytesIO()
    img.save(buffer, format=img_format, quality=85)
    
    # Check if the file is under the 500KB limit, if not, compress further
    while buffer.tell() > 500 * 1024:
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format=img_format, quality=70)  # Reduce quality further if needed

    buffer.seek(0)
    return buffer

# Upload to AWS S3
def upload_to_s3(file, bucket_name, filename, acl="public-read"):
    try:
        folder_name = "Announcement"
        full_s3_path = f"{folder_name}/{filename}"
        
        s3.upload_fileobj(
            file,
            bucket_name,
            full_s3_path,
            ExtraArgs={
                "ACL": acl,
                "ContentType": "image/jpeg"
            }
        )
        return f"https://{bucket_name}.s3.{S3_REGION}.amazonaws.com/{full_s3_path}"
    
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

# Helper function to delete from AWS S3
def delete_from_s3(bucket_name, file_path):
    try:
        s3.delete_object(Bucket=bucket_name, Key=file_path)
    except Exception as e:
        print(f"Error deleting from S3: {e}")

# Create Announcement
@announcement_bp.route('/announcements', methods=['POST'])
def create_announcement():
    title = request.form.get('title')
    image_file = request.files.get('image')
    link = request.form.get('link')

    if not title or not image_file:
        return jsonify({"error": "Title and image are required"}), 400

    resized_image = resize_image(image_file)
    filename = secure_filename(image_file.filename)

    image_url = upload_to_s3(resized_image, S3_BUCKET, filename)
    if not image_url:
        return jsonify({"error": "Failed to upload image to S3"}), 500

    announcement = Announcement(title=title, image_url=image_url, link=link)
    db.session.add(announcement)
    db.session.commit()

    return jsonify({"message": "Announcement created", "id": announcement.id}), 201

# # Get Announcements
# @announcement_bp.route('/announcements', methods=['GET'])
# def get_announcements():
#     announcements = Announcement.query.all()
#     return jsonify([
#         {
#             "id": a.id,
#             "title": a.title,
#             "image_url": a.image_url,
#             "link": a.link if a.link is not None else "NULL"
#         } 
#         for a in announcements
#     ]), 200

# Get Announcements
@announcement_bp.route('/announcements', methods=['GET'])
def get_announcements():
    # Order by id in descending order to get the newest announcements on top
    announcements = Announcement.query.order_by(Announcement.id.desc()).all()
    return jsonify([
        {
            "id": a.id,
            "title": a.title,
            "image_url": a.image_url,
            "link": a.link if a.link is not None else "NULL"
        } 
        for a in announcements
    ]), 200
# Delete Announcement and associated image from S3
@announcement_bp.route('/announcements/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    announcement = Announcement.query.get(id)
    if announcement is None:
        return jsonify({"error": "Announcement not found"}), 404

    image_key = '/'.join(announcement.image_url.split('/')[-2:])  # Get path within S3 bucket
    delete_from_s3(S3_BUCKET, image_key)

    db.session.delete(announcement)
    db.session.commit()
    return jsonify({"message": "Announcement deleted"}), 204
