from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from ezadvisor import db, app, login
from flask_login import UserMixin
import datetime
from sqlalchemy import DateTime

# required = db.Table('required',
#     db.Column('major', db.String(40), db.ForeignKey('major.title')),
#     db.Column('requirement_area', db.String(30)),
#     db.Column('sub_area', db.String(30)),
#     db.Column('course_id', db.String(10), db.ForeignKey('catalog.course_id')))

completedCourses = db.Table('completedCourses',
    db.Column('student_id', db.Integer, db.ForeignKey('student.vip_id')),
    db.Column('course_id', db.String(10), db.ForeignKey('catalog.course_id')),
    db.Column('grade', db.String(3)))

class submittedSchedules(db.Model):
    student_vip_id = db.Column(db.Integer, db.ForeignKey('student.vip_id'), primary_key=True)
    advisor_vip_id = db.Column(db.Integer, db.ForeignKey('advisor.vip_id'), primary_key=True)
    semester = db.Column(db.String(20), db.ForeignKey('semester.semester'), primary_key=True)
    submit_datetime = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    status = db.Column(db.String(30), primary_key=True, default='Not submitted')
    advisor_feedback = db.Column(db.String(1000))
    student_signed = db.Column(db.String(20), default='No')
    advisor_signed = db.Column(db.String(20), default='No')
    

class proposedSchedule(db.Model):
    student_vip_id = db.Column(db.Integer, db.ForeignKey('student.vip_id'), primary_key=True)
    course_crn = db.Column(db.Integer, db.ForeignKey('courses.crn'), primary_key=True)
    semester = db.Column(db.String(20), db.ForeignKey('semester.semester'), primary_key=True)


class Advisor(UserMixin, db.Model):
    vip_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    password = db.Column(db.String(25))
    job = db.Column(db.String(25))
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(50))
    office = db.Column(db.String(50))
    student = db.relationship('Student', backref='advisor', lazy='joined')

    def check_password(self, password):
        return self.password == password
    
    def get_id(self):
           return (self.vip_id)

    
    def __repr__(self):
        return f"Advisor('{self.name}', '{self.email}', '{self.office}')"



class Student(UserMixin, db.Model):
    vip_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    password = db.Column(db.String(25))
    email = db.Column(db.String(50))
    major_title = db.Column(db.String(50), db.ForeignKey('major.title'))
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisor.vip_id'))
    completed_Course = db.relationship('Catalog', secondary=completedCourses, backref=db.backref('completed', lazy='dynamic'))
    #registered = db.relationship('Courses', secondary=registered, backref=db.backref('registered', lazy='dynamic'))

    def check_password(self, password):
        return self.password == password
    
    def get_id(self):
           return (self.vip_id)
    
    
    def __repr__(self):
        return f"Student('{self.name}', '{self.email}', '{self.major_title}')"
        

class Major(db.Model):
    title = db.Column(db.String(40), primary_key=True)
    description = db.Column(db.String(150))
    student = db.relationship('Student', backref='major')

    def __repr__(self):
        return f"Major('{self.title}', '{self.description}')"

class Catalog(db.Model):
    course_id = db.Column(db.String(10), primary_key=True)
    course_title = db.Column(db.String(40))
    course_desc = db.Column(db.String(250))
    prereq = db.Column(db.String(100))
    credit_hours = db.Column(db.Integer)
    # major = db.relationship('Major', secondary=required, backref=db.backref('required', lazy='dynamic'))
    course_offered = db.relationship('Courses', backref='course', lazy='joined')

    def __repr__(self):
        return f"Catalog('{self.course_id}', '{self.course_title}', '{self.course_desc}', '{self.prereq}', '{self.credit_hours}')"

class Courses(db.Model):
    crn = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(10), db.ForeignKey('catalog.course_id'))
    course_title = db.Column(db.String(40))
    section_num = db.Column(db.Integer)
    semester = db.Column(db.String(10), db.ForeignKey('semester.semester'))
    professor_name = db.Column(db.String(25))
    day = db.Column(db.String(5))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    campus = db.Column(db.String(25))
    credit_hours = db.Column(db.Integer)

    def __repr__(self):
        return f"Courses('{self.course_id}', '{self.section_num}', '{self.semester}', '{self.day}', '{self.start_time_MWF}', '{self.end_time_MWF}', '{self.start_time_TTh}', '{self.end_time_MWF}')"

class Semester(db.Model):
    semester = db.Column(db.String(10), primary_key=True)
    course_present = db.relationship('Courses', backref='semester_taken')

    def __repr__(self):
        return f"{self.semester}"

class Campus(db.Model):
    campus = db.Column(db.String(20), primary_key=True)

    def __repr__(self):
        return f"{self.campus}"



#keep track of person logged in
@login.user_loader
def load_user(vip_id):
    advisor = Advisor.query.get(str(vip_id))
    student = Student.query.get(str(vip_id))
    if student is None:
        return advisor
    else:
        return student
