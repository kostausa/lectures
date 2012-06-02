import hashlib
import smtplib
from email.mime.text import MIMEText

from seminar import app, db

from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy


def auth():
  if 'admin' in session and session['admin']:
    return True
  else: 
    return False

def sendlink(user,h):
  msg = MIMEText(
    render_template(
      'link-email.html', 
      user=user,
      hash=h
    ), 'html', 'UTF-8'
  )
  
  msg['Subject'] = '2012 KOSTA/USA Seminar'
  msg['From'] = 'webhelp@kostausa.org'
  msg['To'] = user.email

  s = smtplib.SMTP('smtp.1and1.com')
  s.login('web@kosta.us','gkskslaskfk')
  s.sendmail('webhelp@kostausa.org', [user.email], msg.as_string())
  s.quit()

class Lecture(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.Text, unique=False)
  speaker = db.Column(db.Text, unique=False)
  abstract = db.Column(db.Text, unique=False)
  grouping = db.Column(db.Integer, unique=False)
  subject = db.Column(db.Text, unique=False)
  schedule = db.Column(db.String(32), unique=False)
  conf = db.Column(db.Integer, unique=False)
  bio = db.Column(db.Text, unique=False)
  capacity = db.Column(db.Integer, unique=False)
  sessions = db.relationship('Session', backref='lecture')

  def __init__(self, title, speaker, abstract, grouping, subject, schedule, conf, bio, capacity):
    self.title = title
    self.speaker = speaker
    self.abstract = abstract
    self.grouping = grouping
    self.subject = subject
    self.schedule = schedule
    self.conf = conf
    self.bio = bio
    self.capacity = capacity

  def __repr__(self):
    return ''

class Schedule(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  slot = db.Column(db.Integer)
  conf = db.Column(db.Integer)
  description = db.Column(db.String(255))

class Session(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  lectureid = db.Column(db.Integer, db.ForeignKey('lecture.id'))
  slot = db.Column(db.Integer)
  state = db.Column(db.Integer)
  conf = db.Column(db.Integer)
  assignments = db.relationship('Assigned', backref='session')

  def __init__(self, lectureid, slot, state, conf):
    self.lectureid = lectureid
    self.slot = slot
    self.state = state
    self.conf = conf

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  kname = db.Column(db.String(255), unique=False)
  email = db.Column(db.String(255), unique=True)
  gender = db.Column(db.String(1), unique=False)
  secret = db.Column(db.String(255), unique=True)
  track = db.Column(db.String(4), unique=False)
  conf = db.Column(db.Integer)

  def __init__(self, kname, email):
    self.kname = kname
    self.email = email

  def __repr__(self):
    return ''   

class Assigned(db.Model):
  sessionid = db.Column(db.Integer, db.ForeignKey('session.id'), primary_key=True)
  userid = db.Column(db.Integer, primary_key=True)

  def __init__(self, sessionid, userid):
    self.userid = userid
    self.sessionid = sessionid

  def __repr__(self):
    return '<Assigned %r>' % self.userid

# API Section
@app.route("/api/lectures/<conf>")
def lectures(conf):
  lectures = Lecture.query.filter_by(conf=conf).all()
  sessions = Session.query.filter_by(conf=conf).all()
  rs = make_response(render_template('lectures.html', 
    lectures=lectures, sessions=sessions))
  rs.headers['Content-type'] = 'application/json'  
  return rs

@app.route("/api/remove", methods=['POST'])
def unregister():
  userid = int(request.form['userid'])
  sessionid = int(request.form['sessionid'])

  targetSession = Session.query.filter_by(id=sessionid).first()
  if targetSession is None:
    return jsonify(result=False, reason='invalid')

  slot = targetSession.slot  

  assigned = Assigned.query \
    .filter_by(sessionid=sessionid) \
    .filter_by(userid=userid).first()

  if assigned:
    db.session.delete(assigned)
    db.session.commit()

  return jsonify(result=True, slot=slot)

@app.route("/api/register", methods=['POST'])
def register():
  userid = int(request.form['userid'])
  sessionid = int(request.form['sessionid'])

  if session['userid'] != userid:
    return jsonify(result=False, reason='auth')

  targetSession = Session.query.filter_by(id=sessionid).first()
  if targetSession is None:
    return jsonify(result=False, reason='invalid')

  slot = targetSession.slot
  user = User.query.filter_by(id=userid).first()
  if user.conf == 0 and user.track == 'T' and not slot in [2,3]:
    return jsonify(result=False, reason='track')

  maxpeople = targetSession.lecture.capacity

  total = Assigned.query.filter_by(sessionid=sessionid).count()
  if not maxpeople > total:
    return jsonify(result=False, reason='full')

  assigned = Assigned.query \
    .join(Session) \
    .filter(Assigned.userid==userid) \
    .filter(Session.slot == slot) \
    .first()

  if assigned:
    assigned.sessionid = sessionid
  else:
    assignment = Assigned(sessionid, userid)
    db.session.add(assignment)

  db.session.commit()  
  lecture = targetSession.lecture

  return jsonify(
    result=True,     
    id=lecture.id,
    slot=slot,
    title=lecture.title,
    grouping=lecture.grouping,
    speaker=lecture.speaker,
    subject=lecture.subject,
    conf=lecture.conf,
  )

# Registration
@app.route("/open/<hash>")
def begin(hash):
  user = User.query.filter_by(secret=hash).first()
  if user is None:
    return make_response(render_template('notfound.html'), 404)
  else:
    session['userid'] = user.id    
    assigned = Assigned.query.filter_by(userid=user.id).all()    
    schedules = Schedule.query.filter_by(conf=user.conf).order_by(Schedule.id).all()    
    personal = {}
    for schedule in schedules:
      personal[schedule.slot] = { 
        'description' : schedule.description,
        'slot'        : schedule.slot,
        'assigned'    : None,
        'sessionid'   : None
      }
    for assignment in assigned:
      lecture = assignment.session.lecture
      personal[assignment.session.slot]['assigned'] = lecture
      personal[assignment.session.slot]['sessionid'] = assignment.sessionid

    return render_template('start.html', user=user, sessions=personal)


@app.route("/login")
def login():
  return render_template('login.html')

@app.route("/link", methods=['POST'])
def link():
  email=request.form['email']
  conf=request.form['conf']
  user = User.query.filter_by(email=email).filter_by(conf=conf).first()
  if user is None:
    return jsonify(result='invalid')
  elif user.track == 'J':
    # Journey KOSTA cannot register
    return jsonify(result='journey')
  elif user.secret == '' or user.secret == None:
    m = hashlib.md5()
    m.update(email)
    m.update(str(user.conf))
    m.update(app.config['SECRET'])
    h = m.hexdigest()
    user.secret=h
    db.session.add(user)
    db.session.commit()
  else:
    h = user.secret
  sendlink(user, h)
  return jsonify(result='sent', email=email)


# Admin Section 
@app.route("/admin/conf")
def conf():
  return jsonify(result=session['conf'])

@app.route("/admin/update", methods=['POST'])
def update():
  lecture=Lecture.query.filter_by(id=request.form['id']).first()
  lecture.abstract = request.form['abstract']
  lecture.bio = request.form['bio']
  db.session.add(lecture)
  db.session.commit()  
  return jsonify(result=True)

@app.route("/admin/delete", methods=['POST'])
def remove():
  lecture=Lecture.query.filter_by(id=request.form['id']).first()
  db.session.delete(lecture)
  db.session.commit()
  return jsonify(result=True)

@app.route("/admin/login", methods=['POST','GET'])
def adminlogin():
  if request.method == 'POST':
    if request.form['pass'] == app.config['ADMINPASS']:
      session['admin'] = True
      session['conf'] = request.form['conf']
      return redirect('/admin')
    else:
      return redirect('/admin/login')
  else:
    return render_template('admin/login.html')

@app.route("/admin/list", methods=['GET'])
def listall():
  lectures=Lecture.query.filter_by(conf=int(session['conf'])).all()
  rs = make_response(render_template('admin/list.html',lectures=lectures))
  rs.headers['Content-type'] = 'application/json'
  return rs

@app.route("/admin/create", methods=['POST'])
def create():
  lecture = Lecture(
    request.form['title'], 
    request.form['speaker'],
    request.form['abstract'],
    int(request.form['grouping']),
    request.form['subject'],
    request.form['schedule'],
    int(session['conf']),
    request.form['bio'],
    int(request.form['capacity'])
  )
  db.session.add(lecture)
  db.session.commit()

  slots = request.form['schedule'].split(',')
  for s in slots:
    onesession = Session(
      lecture.id, int(s),
      0, int(session['conf'])
    )
    db.session.add(onesession)
    db.session.commit()

  return jsonify(
    result='added', 
    id=lecture.id,
    title=lecture.title,
    bio=lecture.bio,
    abstract=lecture.abstract,
    grouping=lecture.grouping,
    speaker=lecture.speaker,
    schedule=lecture.schedule,
    subject=lecture.subject,
    conf=lecture.conf,
    capacity=lecture.capacity
  )

@app.route("/admin")
def admin():
  if not auth():
    return redirect('/admin/login')
  chicago=False
  conf="Indianapolis"
  if session['conf'] == '0':
    chicago=True
    conf="Chicago"
  return render_template('admin/index.html', conf=conf, chicago=chicago)

