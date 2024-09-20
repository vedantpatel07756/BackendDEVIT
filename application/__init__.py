from flask import Flask, jsonify, request
from flask_migrate import Migrate
from .model import User, db
 
def create_app():
    app = Flask(__name__)

    # Set up the database
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:18272610@localhost:5432/DEVITAPP'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://avnadmin:AVNS_zkSIWdIFhGdIBINeh44@pg-3134c6ee-kdkce-c5a4.i.aivencloud.com:24895/defaultdb?sslmode=require'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    migrate = Migrate(app, db)

    # Initialize the database
    db.init_app(app)

   



    # Create the database tables if they don't exist
    with app.app_context():
        
        from .auth import auth_bp
        from .request import request_bp
        from .events import event_bp
        from .userrole import userrole_bp
        from .highlight import highlight_bp
        from .anouncement import announcement_bp
        db.create_all()


     # Register the Blueprint for the auth routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(userrole_bp)
    app.register_blueprint(highlight_bp)
    app.register_blueprint(announcement_bp)
    return app

















# from flask import Flask,render_template
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# from .model import db,User

# app = Flask(__name__)


# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:18272610@localhost:5432/DEVITAPP"
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)


# @app.route("/")
# def hello_world():
#     return render_template("index.html")


# # Run the application
# if __name__ == '__main__':
#     app.run(debug=True)