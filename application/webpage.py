from flask import Blueprint, request, jsonify,render_template,flash,redirect,url_for

from application.model import User,db



webpage_bp = Blueprint('webpage', __name__)

@webpage_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Handle POST request if needed
        pass
    
    # Query all users from the database
    users = User.query.all()
    
    # Convert user objects to a list of dictionaries for easier rendering in the template
    users_data = [
        {
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
            'total_point': user.total_point,
            'password':user.password
        }
        for user in users
    ]

    # Pass the user data to the template
    return render_template('dashboard.html', users=users_data)


@webpage_bp.route('/PendingRequest', methods=['GET', 'POST'])
def pendingrequest():
    # Query the database for users with 'pending' status in the verify column
    pending_users = User.query.filter_by(verify='PENDING').all()
    
    # Pass the result to the pending.html template
    return render_template('pending.html', pending_users=pending_users)


@webpage_bp.route('/update_request', methods=['POST'])
def update_request():
    user_id = request.form.get('user_id')
    action = request.form.get('action')

    # Retrieve the user from the database
    user = User.query.get(user_id)

    if user:
        if action == "approve":
            user.verify = "DONE"  # Mark as done
            flash(f"User {user.fullname} approved successfully!", "success")
        elif action == "disapprove":
            user.verify = "REJECT"  # Mark as rejected
            flash(f"User {user.fullname} disapproved.", "danger")

        # Commit the changes to the database
        db.session.commit()

    return redirect(url_for('webpage.pendingrequest'))