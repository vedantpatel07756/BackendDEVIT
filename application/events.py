from flask import Blueprint, request, jsonify
from .model import Request, db, User,Event,Eventcount
from datetime import datetime
import boto3
import os
# from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename


# Create a Blueprint for the 'auth' module
event_bp = Blueprint('event', __name__)


# AWS S3 Configuration
# Retrieve environment variables
S3_BUCKET = os.getenv('S3_BUCKET')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_REGION = os.getenv('S3_REGION') # Example: 'us-east-1'

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)




from PIL import Image
import io

def upload_image_to_s3(file, bucket_name, acl="public-read", max_size_kb=500):
    try:
        # Open the image and reduce its size
        img = Image.open(file)
        img.thumbnail((1024, 1024))  # Resize to keep it under a reasonable max resolution
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', optimize=True, quality=85)
        img_bytes.seek(0)
        
        # Continue reducing quality until under max_size_kb
        while img_bytes.tell() > max_size_kb * 1024:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', optimize=True, quality=75)
            img_bytes.seek(0)
        
        # Define the full path with folder name and secure filename
        folder_name = "Events"
        filename = secure_filename(file.filename)
        full_s3_path = f"{folder_name}/{filename}"

        # Upload the optimized image
        s3.upload_fileobj(
            img_bytes,
            bucket_name,
            full_s3_path,
            ExtraArgs={"ACL": acl, "ContentType": "image/jpeg"}
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
    name = request.form['name'].title()
    date = request.form['date']
    description = request.form['description']
    drive=request.form['drivelink']

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
            image_url=image_url,
            drivelink=drive
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
            "image_url": event.image_url,
            "drivelink":event.drivelink,
        } for event in events
    ]
    return jsonify(events_data), 200


@event_bp.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    try:
        # Delete the event image from S3
        file_key = event.image_url.split(f"https://{S3_BUCKET}.s3.amazonaws.com/")[1]
        s3.delete_object(Bucket=S3_BUCKET, Key=file_key)
        
        # Remove the event from the database
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'message': 'Event deleted successfully!'}), 200
    except Exception as e:
        print("Error deleting event: ", e)
        return jsonify({'error': 'Failed to delete event'}), 500
    

# @event_bp.route('/eventcount', methods=['GET', 'POST'])
# def handle_eventcount():
#     if request.method == 'GET':
#         # eventcounts = Eventcount.query.all()
#         eventcounts = Eventcount.query.order_by(Eventcount.date.desc()).all()
#         result = [
#             {
#                 'id': event.id,
#                 'eventname': event.eventname.title(),
#                 'eventtype': event.eventtype,
#                 'date': event.date,
#                 'eventcount': event.eventcount,
#                 'participant': event.participant,
#                 'feedback': event.feedback
#             } for event in eventcounts
#         ]
#         return jsonify(result), 200

#     if request.method == 'POST':
#         data = request.get_json()
#         eventname = data.get('eventname')
#         eventtype = data.get('eventtype')  # Get the event type from the request
#         date = data.get('date')
#         eventcount = data.get('eventcount')
#         participant = data.get('participant')
#         feedback = data.get('feedback')

#         if not eventcount or not participant:
#             return jsonify({'error': 'Event count and participant are required fields'}), 400

#         new_event = Eventcount(
#             eventname=eventname,
#             eventtype=eventtype,
#             date=date,
#             eventcount=int(eventcount),
#             participant=int(participant),
#             feedback=int(feedback) if feedback else None
#         )
#         db.session.add(new_event)
#         db.session.commit()

#         return jsonify({
#             'id': new_event.id,
#             'eventname': new_event.eventname,
#             'eventtype': new_event.eventtype,
#             'date': new_event.date,
#             'eventcount': new_event.eventcount,
#             'participant': new_event.participant,
#             'feedback': new_event.feedback
#         }), 201



@event_bp.route('/eventcount', methods=['GET', 'POST'])
def handle_eventcount():
    if request.method == 'GET':
        # Retrieve all events
        eventcounts = Eventcount.query.all()

        # Sort the events by date in descending order
        sorted_events = sorted(
            eventcounts,
            key=lambda event: datetime.strptime(event.date, '%d.%m.%Y'), 
            reverse=True
        )

        result = [
            {
                'id': event.id,
                'eventname': event.eventname.title(),
                'eventtype': event.eventtype,
                'date': event.date,
                'eventcount': event.eventcount,
                'participant': event.participant,
                'feedback': event.feedback
            } for event in sorted_events
        ]
        return jsonify(result), 200

    if request.method == 'POST':
        data = request.get_json()
        eventname = data.get('eventname')
        eventtype = data.get('eventtype')  # Get the event type from the request
        date = data.get('date')
        eventcount = data.get('eventcount')
        participant = data.get('participant')
        feedback = data.get('feedback')

        if not eventcount or not participant:
            return jsonify({'error': 'Event count and participant are required fields'}), 400

        new_event = Eventcount(
            eventname=eventname,
            eventtype=eventtype,
            date=date,
            eventcount=int(eventcount),
            participant=int(participant),
            feedback=int(feedback) if feedback else None
        )
        db.session.add(new_event)
        db.session.commit()

        return jsonify({
            'id': new_event.id,
            'eventname': new_event.eventname,
            'eventtype': new_event.eventtype,
            'date': new_event.date,
            'eventcount': new_event.eventcount,
            'participant': new_event.participant,
            'feedback': new_event.feedback
        }), 201
