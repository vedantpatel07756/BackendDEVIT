from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=False, nullable=False)
    phonenumber = db.Column(db.String(15), unique=False, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    year=db.Column(db.String(10),nullable=True)
    branch=db.Column(db.String(15),nullable=True)
    rollno=db.Column(db.String(15),nullable=True)
    post=db.Column(db.String(20),nullable=True)
    verify=db.Column(db.String(10),nullable=True)
    photo=db.Column(db.String(200),nullable=True)
    attandance=db.Column(db.Integer,nullable=True)
    total_point=db.Column(db.Integer, nullable=True)


class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_id = db.Column(db.String(50), nullable=False) 
    permission = db.Column(db.String(50), nullable=False)  # Permission can be 'basic', 'manager', 'full'
    # Relationship with the User table
    user = db.relationship('User', backref='roles')


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    task_done = db.Column(db.String(200), nullable=False)
    task_desc = db.Column(db.String(200), nullable=False)
    time_option = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    task_point=db.Column(db.Integer, nullable=True)
    

    
    # Define the relationship with User
    user = db.relationship('User', backref=db.backref('requests', lazy=True))





class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)  # Store S3 URL here
    drivelink=db.Column(db.String(200), nullable=False)






class Highlight(db.Model):
    __tablename__ = 'highlights'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String, nullable=False, )
    image_url = db.Column(db.String(200), nullable=True)



class Announcement(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        image_url = db.Column(db.String(255), nullable=False)
        link = db.Column(db.String(255), nullable=True)


class Eventcount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventname = db.Column(db.String(255), nullable=False)
    eventtype = db.Column(db.String(255), nullable=False)  # New field for event type
    date = db.Column(db.String(255), nullable=False)
    eventcount = db.Column(db.Integer, nullable=False)
    participant = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Integer, nullable=True)