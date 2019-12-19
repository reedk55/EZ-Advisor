from flask import Flask, render_template, flash, redirect, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, logout_user, login_required
from ezadvisor import app, db
from ezadvisor.forms import LoginForm
from ezadvisor.data import Student, Advisor, Campus, Semester, Major, Courses, Catalog, proposedSchedule, submittedSchedules
from werkzeug.urls import url_parse
from datetime import datetime


#Route for index.html
#This page contains the login form for the system
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
#GET and POST methods are for getting information from the web browser and posting info to the server
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_started'))
    form = LoginForm()
    if form.validate_on_submit():
        #User must either be a student or an advisor
        student = Student.query.filter_by(vip_id=form.username.data).first()
        advisor = Advisor.query.filter_by(vip_id=form.username.data).first()
        if (student is None or not student.check_password(form.password.data)) and (advisor is None or not advisor.check_password(form.password.data)):
            flash('The password or username you entered was invalid.')
            return redirect(url_for('login'))
        if student is None:
            login_user(advisor)
        else:
            login_user(student)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('get_started')
        return redirect(next_page)
    return render_template('index.html', title='Login', form=form)


#Route for logging out of the system using the Logout link in the navigation bar
#User is redirected to index.html
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


#Route for get-started.html
@app.route('/get-started', methods=['GET', 'POST'])
@login_required
def get_started():
    if request.method == 'POST':
        #Both students and advisors will first be directed to this page after logging in
        #and then they will be directed to two different pages
        student = Student.query.filter_by(vip_id=current_user.vip_id).first()
        if student is None:
            return redirect(url_for('approve_schedules'))
        else:
            return redirect(url_for('build_schedule'))
    return render_template('get-started.html')


#Route for access-denied.html
@app.route('/access-denied')
@login_required
def access_denied():
    #Student will be directed to this page if they try to access an advisor page
    #Advisor will be directed to this page if they try to access a student page
    return render_template('access-denied.html')


############# Student pages ##############


#Route for build-schedule.html
#This page just contains a button that allows them to initiate building a schedule
@app.route('/build-schedule')
@login_required
def build_schedule():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    return render_template('build-schedule.html')


#Route for select-campus.html
#This page contains a form of USC campuses displayed as a list of clickable buttons
@app.route('/select-campus', methods=['GET', 'POST'])
@login_required
def select_campus():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    campuses = Campus.query.all()
    if request.method == 'POST':
        #Set campus as a session variable so that the variable will persist across pages and functions
        session['campus'] = request.form.get('campus')
        return redirect(url_for('select_term'))
    return render_template('select-campus.html', campuses=campuses)
    

#Route for select-term.html
#This page contains a form of the next semester and the following semester displayed as a list of clickable buttons
@app.route('/select-term', methods=['GET', 'POST'])
@login_required
def select_term():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    terms = Semester.query.all()
    if request.method == 'POST':
        #Set term as a session variable so that the variable will persist across pages and functions
        session['term'] = request.form.get('term')
        return redirect(url_for('select_subject'))
    return render_template('select-term.html', terms=terms)


#Route for select-subject.html
#This page contains a form of the subjects offered at the campus displayed as a list of clickable buttons
@app.route('/select-subject', methods=['GET', 'POST'])
@login_required
def select_subject():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    subject = Major.query.all()
    if request.method == 'POST':
        #Set subject as a session variable so that the variable will persist across pages and functions
        session['subject'] = request.form.get('subject')
        return redirect(url_for('search_results'))
    return render_template('select-subject.html', subject=subject)


#Route for search-results.html
#This page contains a form of the different classes for the chosen subject displayed as a list of clickable buttons
@app.route('/search-results', methods=['GET', 'POST'])
@login_required
def search_results():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    if request.method == 'POST':
        #Set course as a session variable so that the variable will persist across pages and functions
        session['course'] = request.form.get('course')
        return redirect(url_for('class_sections'))
    #Select all courses that match the chosen campus and term. Limit the displayed courses to the one the student has not already
    #taken in the past and for which the student received at least a 'C' as the grade.
    courses = db.session.execute('SELECT * FROM catalog WHERE course_id in \
        (SELECT course_id FROM courses WHERE campus = :val1 AND semester = :val2) AND course_id NOT IN \
        (SELECT course_id FROM "completedCourses" where student_id = :val3 and grade <= :val4)', \
        {'val1': session['campus'], 'val2': session['term'], 'val3': current_user.vip_id, 'val4': 'C'})
    return render_template('search-results.html', courses=courses)


#Route for class-sections.html
#This page contains a form of the different class sections for the chosen course displayed as a list of clickable buttons
@app.route('/class-sections', methods=['GET', 'POST'])
@login_required
def class_sections():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    #Need to determine the status of the student's submitted schedule to determine if student can add any more courses at the time
    status = db.session.execute("select case when count(student_vip_id) > 0 then (Select status from submitted_schedules \
	    where student_vip_id = :val1 and semester = :val2) else 'Not submitted' end as schedule_status from submitted_schedules \
        where student_vip_id = :val1 and semester = :val2", \
            {'val1': current_user.vip_id, 'val2': session['term']})
    status = status.first()
    if request.method == 'POST':
        crn = request.form.get('course_crn')
        semester = request.form.get('course_semester')
        #Student can only add classes if they have haven't yet submitted a schedule or if they advisor has responded to their proposed schedule with feedback
        if (status[0] == 'Needs review' or status[0] == 'Changes made' or status[0] == 'Advisor approved' or status[0] == 'Student signed'):
            flash('Error: You cannot add more courses at this stage.', 'danger')
        else:
            #Ensure that the student has not already added this specific course section to their schedule.
            already_added = db.session.execute('select count(1) from proposed_schedule where student_vip_id = :val1 \
            and semester = :val2 and course_crn = :val3', \
            {'val1': current_user.vip_id, 'val2': semester, 'val3': crn})
            already_added = proposedSchedule.query.filter_by(student_vip_id = current_user.vip_id, semester = semester, course_crn = crn).first()
            #Otherwise, add the course section to the schedule
            if already_added is None:
                new_course = proposedSchedule(student_vip_id = current_user.vip_id, course_crn = crn, semester=semester)
                db.session.add(new_course)
                db.session.commit()
                flash('Course successfully added!', 'dark')
            else:
                flash('Error: You have already added this course to your schedule', 'danger')
        return redirect(url_for('class_sections'))
    course = session['course']
    course_id = course[0 : 9]
    course = course[11:]
    #Return all the sections that match the chosen campus, term, and course ID
    sections = db.session.execute('SELECT * FROM courses \
             WHERE campus = :val1 AND semester = :val2 AND course_id = :val3', \
            {'val1': session['campus'], 'val2': session['term'], 'val3': course_id})
    #Return sections as a list so that it can be iterated through more than once
    return render_template('class-sections.html', sections=list(sections), course_id=course_id, course=course)


#Route for completed-schedule.html
#This page contains a message for the user and then displays the student's proposed schedule
@app.route('/completed-schedule', methods=['GET', 'POST'])
@login_required
def completed_schedule():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    classes = db.session.execute('SELECT courses.* FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': current_user.vip_id, 'val2': session['term']})
    hours = db.session.execute('SELECT sum(courses.credit_hours) as sum FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': current_user.vip_id, 'val2': session['term']})
    status = db.session.execute("select case when count(student_vip_id) > 0 then (Select status from submitted_schedules \
	    where student_vip_id = :val1 and semester = :val2) else 'Not submitted' end as schedule_status from submitted_schedules \
        where student_vip_id = :val1 and semester = :val2", \
            {'val1': current_user.vip_id, 'val2': session['term']})
    feedback = db.session.execute("SELECT (case when advisor_feedback is null then 'No feedback' else advisor_feedback end) \
        as advisor_feedback FROM submitted_schedules where student_vip_id = :val1 and semester= :val2", \
        {'val1': current_user.vip_id, 'val2': session['term']})
    semester = session['term']
    if request.method == 'POST':
        #Total hours is the sum of all the credit hours of the proposed schedule
        total_hours = request.form.get('total_hours')
        #Student is not allowed to submit the schedule until they add at least one course
        if total_hours == '0':
            flash('Error: You cannot submit a schedule with zero classes added.', 'danger')
        elif request.form['btn'] == 'Delete':
            course_crn = request.form.get('remove_course_crn')
            course = proposedSchedule.query.filter_by(student_vip_id=current_user.vip_id, course_crn=course_crn, semester=session['term']).delete()
            db.session.commit()
            flash('Class has been deleted.', 'dark')
        elif request.form['btn'] == 'SUBMIT TO ADVISOR':
            schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester).first()
            #If the student has not yet submitted a schedule for the chosen term, add this proposed schedule to the database
            if schedule is None: 
                new_schedule = submittedSchedules(student_vip_id = current_user.vip_id, advisor_vip_id = current_user.advisor_id, semester = semester, status = 'Needs review')
                db.session.add(new_schedule)
                db.session.commit()
                flash('Your schedule has been submitted to your advisor for feedback!', 'dark')
            else:
                #If the student has already submitted a schedule for the chosen term, check if the status is "Needs review"
                schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester, status='Needs review').first()
                #If there is a submitted schedule but its status is not 'needs review' for the chosen semester, then change the status of 
                #the submitted schedule to changes made and remove the advisor feedback and resubmit the schedule to the advisor with the changes
                if schedule is None:
                    schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester).first()
                    schedule.status = 'Changes made'
                    schedule.advisor_feedback = None
                    db.session.commit()
                    flash('Your schedule has been submitted to your advisor for feedback!', 'dark')
                else:
                    #Student is not allowed to submit a schedule a second time until the advisor provides feedback
                    flash('Error: You cannot submit your schedule again until your advisor provides feedback.', 'danger')
        elif request.form['btn'] == 'Sign':
            signature = request.form.get('student-signature')
            #Student is now allowed to submit a blank signature 
            if signature == '':
                flash('Error: You must sign your name.', 'danger')
            else:
                #When the student signs to approve the schedule, change the status of the submitted schedule to 'Student signed'
                schedule = submittedSchedules.query.filter_by(student_vip_id=current_user.vip_id, semester=session['term']).first()
                schedule.student_signed = 'Yes'
                schedule.status = 'Student signed'
                db.session.commit()
                flash('Schedule signed!', 'dark')
        return redirect(url_for('review_schedule_student'))
    return render_template('completed-schedule.html', classes=list(classes), hours=hours.first(), semester=session['term'], status=status.first(), feedback=feedback.first())


#This route is almost identical to the route above, but it is for review-schedule.html. 
#This page was created because we don't want the user to see any animation 
#if they select to review their schedule from the navigation bar.
@app.route('/review-schedule', methods=['GET', 'POST'])
@login_required
def review_schedule_student():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    classes = db.session.execute('SELECT courses.* FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': current_user.vip_id, 'val2': session['term']})
    hours = db.session.execute('SELECT (case when sum(courses.credit_hours) > 0 then sum(courses.credit_hours) else 0 end) \
        as "sum"  FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': current_user.vip_id, 'val2': session['term']})
    status = db.session.execute("select case when count(student_vip_id) > 0 then (Select status from submitted_schedules \
	    where student_vip_id = :val1 and semester = :val2) else 'Not submitted' end as schedule_status from submitted_schedules \
        where student_vip_id = :val1 and semester = :val2", \
            {'val1': current_user.vip_id, 'val2': session['term']})
    feedback = db.session.execute("SELECT (case when advisor_feedback is null then 'No feedback' else advisor_feedback end) \
        as advisor_feedback FROM submitted_schedules where student_vip_id = :val1 and semester= :val2", \
        {'val1': current_user.vip_id, 'val2': session['term']})
    semester = session['term']
    if request.method == 'POST':
        total_hours = request.form.get('total_hours')
        if total_hours == '0':
            flash('Error: You cannot submit a schedule with zero classes added.', 'danger')
        elif request.form['btn'] == 'Delete':
            course_crn = request.form.get('remove_course_crn')
            course = proposedSchedule.query.filter_by(student_vip_id=current_user.vip_id, course_crn=course_crn, semester=session['term']).delete()
            db.session.commit()
            flash('Class has been deleted.', 'dark')
        elif request.form['btn'] == 'SUBMIT TO ADVISOR':
            schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester).first()
            if schedule is None: 
                new_schedule = submittedSchedules(student_vip_id = current_user.vip_id, advisor_vip_id = current_user.advisor_id, semester = semester, status = 'Needs review')
                db.session.add(new_schedule)
                db.session.commit()
                flash('Your schedule has been submitted to your advisor for feedback!', 'dark')
            else:
                schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester, status='Needs review').first()
                if schedule is None:
                    schedule = submittedSchedules.query.filter_by(student_vip_id = current_user.vip_id, semester = semester).first()
                    schedule.status = 'Changes made'
                    schedule.advisor_feedback = None
                    db.session.commit()
                    flash('Your schedule has been submitted to your advisor for feedback!', 'dark')
                else:
                    flash('Error: You cannot submit your schedule again until your advisor provides feedback.', 'danger')
        elif request.form['btn'] == 'Sign':
            signature = request.form.get('student-signature')
            if signature == '':
                flash('Error: You must sign your name.', 'danger')
            else:
                schedule = submittedSchedules.query.filter_by(student_vip_id=current_user.vip_id, semester=session['term']).first()
                schedule.student_signed = 'Yes'
                schedule.status = 'Student signed'
                db.session.commit()
                flash('Schedule signed!', 'dark')
        return redirect(url_for('review_schedule_student'))
    return render_template('review-schedule.html', classes=list(classes), hours=hours.first(), semester=session['term'], status=status.first(), feedback=feedback.first())


#Route for advisor-info.html
#Student is directed to this page if they select Advisor Information in the navigation menu
#This page contains information about the student's advisor
@app.route('/advisor-info', methods=['GET', 'POST'])
@login_required
def advisor_info():
    #Checks to make sure that the current user is a student, not an advisor. 
    student = Student.query.filter_by(vip_id=current_user.vip_id).first()
    if student is None:
        return redirect(url_for('access_denied'))
    advisor = db.session.execute('SELECT * FROM advisor WHERE vip_id = :val', {'val': current_user.advisor_id})
    return render_template('advisor-info.html', advisor=advisor)



############# Advisor pages ##############


#Route for approve-schedules.html
#This page contains a list of all of the students of the advisor who is logged in who have submitted a proposed schedule
@app.route('/approve-schedules', methods=['GET', 'POST'])
@login_required
def approve_schedules():
    #Checks to make sure that the current user is an advisor, not a student. 
    advisor = Advisor.query.filter_by(vip_id=current_user.vip_id).first()
    if advisor is None:
        return redirect(url_for('access_denied'))
    schedules = db.session.execute("select student.name, submit_datetime as submitted_date, \
        submitted_schedules.student_vip_id, submitted_schedules.semester, submitted_schedules.status, \
		CASE \
        WHEN submitted_schedules.status =  'Needs review' THEN 1 \
        WHEN submitted_schedules.status =  'Changes made' THEN 2 \
        WHEN submitted_schedules.status =  'Feedback submitted' THEN 3 \
		WHEN submitted_schedules.status =  'Advisor approved' THEN 4 \
		WHEN submitted_schedules.status =  'Student signed' THEN 5 \
    END as priority \
from submitted_schedules \
left join student on submitted_schedules.student_vip_id = student.vip_id \
where advisor_vip_id = :val1 order by priority", {"val1": current_user.vip_id})
    if request.method == 'POST':
        session['student_vip_id'] = request.form.get('view_schedule_vip_id')
        session['semester'] = request.form.get('view_schedule_semester')
        session['student_name'] = request.form.get('view_schedule_name')
        return redirect(url_for('review_schedule_advisor'))
    return render_template('approve-schedules.html', schedules=schedules)


#Route for review-schedule-advisor-view.html
#This page displays the student's proposed schedule and allows the advisor to approve the schedule or deny the schedule and provide feedback.
@app.route('/review-schedule-advisor-view', methods=['GET', 'POST'])
@login_required
def review_schedule_advisor():
    #Checks to make sure that the current user is an advisor, not a student.
    advisor = Advisor.query.filter_by(vip_id=current_user.vip_id).first()
    if advisor is None:
        return redirect(url_for('access_denied'))
    student_name = session['student_name']
    semester = session['semester']
    student_vip_id = session['student_vip_id']
    classes = db.session.execute('SELECT courses.* FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': session['student_vip_id'], 'val2': session['semester']})
    hours = db.session.execute('SELECT (case when sum(courses.credit_hours) > 0 then sum(courses.credit_hours) else 0 end) \
        as "sum"  FROM proposed_schedule \
        left JOIN courses on proposed_schedule.course_crn = courses.crn \
        where proposed_schedule.student_vip_id = :val1 and proposed_schedule.semester= :val2', \
        {'val1': session['student_vip_id'], 'val2': session['semester']})
    status = db.session.execute("select case when count(student_vip_id) > 0 then (Select status from submitted_schedules \
	    where student_vip_id = :val1 and semester = :val2) else 'Not submitted' end as schedule_status from submitted_schedules \
        where student_vip_id = :val1 and semester = :val2", \
            {'val1': session['student_vip_id'], 'val2': session['semester']})
    if request.method == 'POST':
        if request.form['btn'] == 'Sign':
            signature = request.form.get('advisor-signature')
            if signature == '':
                flash('Error: You must sign your name to approve the schedule', 'danger')
            else:
                schedule = submittedSchedules.query.filter_by(student_vip_id=student_vip_id, semester=semester).first()
                schedule.status = 'Advisor approved'
                schedule.advisor_signed = 'Yes'
                db.session.commit()
                flash('Schedule approved!', 'dark')
        elif request.form['btn'] == 'Send':
            feedback = request.form.get('feedback')
            if feedback == '':
                flash('Error: You must provide feedback to the student', 'danger')
            else: 
                schedule = submittedSchedules.query.filter_by(student_vip_id=student_vip_id, semester=semester).first()
                schedule.status = 'Feedback submitted'
                schedule.advisor_feedback = feedback
                db.session.commit()
                flash('Feedback submitted!', 'dark')
        return redirect(url_for('review_schedule_advisor'))
    return render_template('review-schedule-advisor-view.html', classes=list(classes), hours=hours.first(), student_name=session['student_name'], semester = semester, status=status.first())
