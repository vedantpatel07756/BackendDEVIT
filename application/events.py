from flask import Blueprint, request, jsonify
from .model import Request, db, User,Event
from datetime import datetime
import boto3
import os
# from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename


# Create a Blueprint for the 'auth' module
event_bp = Blueprint('event', __name__)


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


def upload_image_to_s3(file, bucket_name, acl="public-read"):
    """
    Uploads file to AWS S3 and returns the file URL.
    """

    try:
        # file.filename = secure_filename(file.filename)
          # Prepend the folder name to the filename
        folder_name = "Events"
        filename = secure_filename(file.filename)
        full_s3_path = f"{folder_name}/{filename}"  # Store in 'Profile Photo' folder


        s3.upload_fileobj(
            file,
            bucket_name,
            full_s3_path,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
        return f"https://{bucket_name}.s3.amazonaws.com/{full_s3_path}"
    except Exception as e:
        print("Error uploading to S3: ", e)
        return None

@event_bp.route('/add_event', methods=['POST'])
def add_event():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    image = request.files['image']
    name = request.form['name']
    date = request.form['date']
    description = request.form['description']

    # Upload image to S3
    image_url = upload_image_to_s3(image, S3_BUCKET)
    if not image_url:
        return jsonify({'error': 'Failed to upload image'}), 500

    # Store event in database
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d").date()
        new_event = Event(
            name=name,
            date=event_date,
            description=description,
            image_url=image_url
        )
        db.session.add(new_event)
        db.session.commit()

        return jsonify({'message': 'Event added successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Route to get events (pass data to the frontend)
@event_bp.route('/get_events', methods=['GET'])
def get_events():
    events = Event.query.all()
    events_data = [
        {
            "id": event.id,
            "name": event.name,
            "date": event.date.strftime('%Y-%m-%d'),
            "description": event.description,
            "image_url": event.image_url
        } for event in events
    ]
    return jsonify(events_data), 200
