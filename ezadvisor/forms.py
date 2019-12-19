from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from ezadvisor.data import Student, Advisor, Campus

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"placeholder": "Network Username/VIP ID"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class CampusForm(FlaskForm):
    campus = SubmitField()

class SemesterForm(FlaskForm):
    semester = SubmitField()

class SubjectForm(FlaskForm):
    subject = SubmitField()

class CourseForm(FlaskForm):
    course = SubmitField()

class SectionForm(FlaskForm):
    add = SubmitField('Add')
    cancel = SubmitField('Cancel')
    
    