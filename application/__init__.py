import os
from flask import Flask, jsonify, request,render_template, url_for
from flask_migrate import Migrate
from .model import User, db
 
def create_app():
    app = Flask(__name__)

    # Set up the database

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    migrate = Migrate(app, db)

    # Set the secret key for session management
    app.secret_key = 'Hello'


    
    # Initialize the database
    db.init_app(app)
        # DEV-IT contact email for account deletion
    DEVIT_EMAIL = "contact@devitforum.com"

    @app.route('/delete-account', methods=['GET'])
    def delete_account():
        # Generate the URL for the Play Store account deletion process
        playstore_link = url_for('playstore_account_deletion', _external=True)
        return render_template('delete_account.html', email=DEVIT_EMAIL, playstore_link=playstore_link)

    @app.route('/playstore-account-deletion', methods=['GET'])
    def playstore_account_deletion():
        return "Account deletion process initiated. Please contact DEV-IT for further assistance."

   

  


    # Create the database tables if they don't exist
    with app.app_context():
        
        from .auth import auth_bp
        from .request import request_bp
        from .events import event_bp
        from .userrole import userrole_bp
        from .highlight import highlight_bp
        from .anouncement import announcement_bp
        from .webpage import webpage_bp
        db.create_all()


     # Register the Blueprint for the auth routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(userrole_bp)
    app.register_blueprint(highlight_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(webpage_bp)
    return app

















