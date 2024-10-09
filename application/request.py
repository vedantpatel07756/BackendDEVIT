from flask import Blueprint, request, jsonify
from .model import Request, UserRole, db, User
from datetime import datetime

# from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename


# Create a Blueprint for the 'auth' module
request_bp = Blueprint('request', __name__)


@request_bp.route('/submitRequest', methods=['POST'])
def submit_request():
    try:
        # Retrieve the data from the request
        data = request.json
        print(data)
        user_id = data.get('user_id')
        start_time = datetime.strptime(data.get('start_time'), '%I:%M %p').time()  # Corrected format
        end_time = datetime.strptime(data.get('end_time'), '%I:%M %p').time()  # Corrected format
        task_done = data.get('task_done')
        time_option = data.get('time_option')
        date=data.get('date')
        desc=data.get('desc')
        # Validate user_id
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Create a new request entry
        new_request = Request(
            date=date,
            start_time=start_time,
            end_time=end_time,
            task_desc=desc,
            task_done=task_done,
            time_option=time_option,
            user_id=user_id,

        )

        # Add to the database
        db.session.add(new_request)
        db.session.commit()

        return jsonify({"message": "Request submitted successfully"}), 200

    except Exception as e:
        print(f"Error submitting request: {e}")
        return jsonify({"message": "Error submitting request"}), 500
    

from datetime import datetime

@request_bp.route('/user/requests/<int:userId>', methods=['GET'])
def get_user_requests(userId):  # Add userId as a parameter
    user_id = userId  # Get userId from the URL parameter
    print(user_id)

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        # Query the database for requests associated with the given user_id
        user_requests = Request.query.filter_by(user_id=user_id).all()

        # Query the UserRole table for the user's permission
        user_role = UserRole.query.filter_by(user_id=user_id).first()
        
        # If the user role is found, get the permission; otherwise, set it to "None"
        permission = user_role.permission if user_role else "None"
        
        # Convert the query results to a list of dictionaries and format date as dd-mm-yyyy
        requests_list = []
        for req in user_requests:
            formatted_date = req.date.strftime('%d-%m-%Y')  # Format the date as dd-mm-yyyy
            requests_list.append({
                'id': req.id,
                'date': formatted_date,
                'start_time': req.start_time.isoformat(),
                'end_time': req.end_time.isoformat(),
                'task_done': req.task_done,
                'time_option': req.time_option,
                'task_point': req.task_point
            })

        # Sort the requests list by date first, then by start_time (most recent date and time first)
        requests_list.sort(key=lambda x: (datetime.strptime(x['date'], '%d-%m-%Y'), x['start_time']), reverse=True)

        # Return the requests data along with the user's permission
        return jsonify({
            'requests': requests_list,
            'permission': permission
        }), 200

    except Exception as e:
        # Handle exceptions and return an error message
        return jsonify({'error': str(e)}), 500


# Request Fetching all 
    
# # Serialize request data to JSON
# def serialize_request(request):
#     return {
#         'id': request.id,
#         'date': request.date.strftime('%Y-%m-%d'),  # Formatting date
#         'start_time': request.start_time.strftime('%H:%M'),  # Formatting time
#         'end_time': request.end_time.strftime('%H:%M'),
#         'task_done': request.task_done,
#         'time_option': request.time_option,
#         'user_id': request.user_id,
#         'task_point': request.task_point,
#         'user': {
#             'id': request.user.id,
#             'name': request.user.name,  # Assuming User has a 'name' field
#             'email': request.user.email  # Assuming User has an 'email' field
#         }
#     }

# # Endpoint to retrieve all requests
# @request_bp.route('/api/requests', methods=['GET'])
# def get_requests():
#     try:
#         # Fetch all requests from the database
#         requests = Request.query.all()

#         # Serialize the requests into a list of dictionaries
#         requests_list = [serialize_request(req) for req in requests]

#         # Return the serialized data as JSON
#         return jsonify({
#             'status': 'success',
#             'data': requests_list
#         }), 200

#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e)
#         }), 500
    

import traceback
from flask import jsonify

# Serialize request data to JSON
def serialize_request(request):
    try:
        # In case the user relationship is None, handle it safely
        user_data = {
            'id': request.user.id if request.user else None,
            'name': request.user.fullname if request.user else 'Unknown',
            'email': request.user.email if request.user else 'Unknown'
        }

        return {
            'id': request.id,
            'date': request.date.strftime('%Y-%m-%d'),  # Formatting date
            'start_time': request.start_time.strftime('%H:%M'),  # Formatting time
            'end_time': request.end_time.strftime('%H:%M'),
            'task_done': request.task_done,
            'task_desc':request.task_desc,
            'time_option': request.time_option,
            'user_id': request.user_id,
            'task_point': request.task_point,
            'user': user_data
        }
    except Exception as e:
        print(f"Error serializing request {request.id}: {e}")
        traceback.print_exc()
        return {}

    

@request_bp.route('/api/requests', methods=['GET'])
def get_requests():
    try:
        # Fetch only requests where task_point is null
        requests = Request.query.filter(Request.task_point == None).all()

        if not requests:
            return jsonify({
                'status': 'success',
                'message': 'No requests found',
                'data': []
            }), 200

        # Serialize the requests into a list of dictionaries
        requests_list = [serialize_request(req) for req in requests]

        # Return the serialized data as JSON
        return jsonify({
            'status': 'success',
            'data': requests_list
        }), 200

    except Exception as e:
        print(f"Error fetching requests: {e}")
        traceback.print_exc()  # For detailed error logs
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching the requests',
            'details': str(e)
        }), 500



# Assign Points 
    
# Helper function to update user points and attendance
def update_user(user, task_point=None, add_attendance=False):
    if task_point:
        user.total_point = (user.total_point or 0) + int(task_point)
    if add_attendance:
        user.attandance = (user.attandance or 0) + 1
    db.session.commit()

# Endpoint to approve, disapprove, or mark attendance and assign points
@request_bp.route('/api/approve_request', methods=['POST'])
def approve_request():
    try:
        data = request.json
        request_id = data.get('request_id')
        action = data.get('action')  # Action: approve, disapprove, attendance, assign_points
        task_point = data.get('task_point', None)  # Optional for assigning points

        # Fetch request by ID
        req = Request.query.get(request_id)
        if not req:
            return jsonify({'status': 'error', 'message': 'Request not found'}), 404

        # Fetch the user related to this request
        user = User.query.get(req.user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        # 1. Approve and add points to the user and the request
        if action == 'approve':
            print("hi")
            req.task_point = int(task_point)
            update_user(user, task_point, add_attendance=True)  # Update points and attendance
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Request approved and points assigned'}), 200

        # 2. Disapprove (reject)
        elif action == 'disapprove':
            db.session.delete(req)  # Optionally, remove the request or mark as rejected
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Request disapproved'}), 200

        # 3. Mark only attendance
        elif action == 'attendance':
            update_user(user, add_attendance=True)
            return jsonify({'status': 'success', 'message': 'Attendance marked'}), 200

        # 4. Mark points on the selected value (5, 10, 15)
        elif action == 'assign_points' and task_point in [5, 10, 15]:
            print("hi")
            req.task_point = task_point
            update_user(user, task_point)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'{task_point} points assigned'}), 200

        else:
            return jsonify({'status': 'error', 'message': 'Invalid action or parameters'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500