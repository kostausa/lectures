from seminar import app, db

from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy


def auth():
  if 'admin' in session and session['admin']:
    return True
  else: 
    return False

def sendlink(user):
  msg = MIMEText(
    render_template(
      'link-email.html', 
      user=user
    ), 
    'html', 'UTF-8'
  )
  
  msg['Subject'] = 'Seminar Link'
  msg['From'] = 'webhelp@kostausa.org'
  msg['To'] = 'eungyu.kim@gmail.com'

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

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  kname = db.Column(db.String(255), unique=False)
  email = db.Column(db.String(255), unique=True)
  gender = db.Column(db.String(1), unique=False)
  secret = db.Column(db.String(255), unique=True)

  def __init__(self, kname, email):
    self.kname = kname
    self.email = email

  def __repr__(self):
    return '<User %r>' % self.kname        

@app.route("/login")
def login():
  return render_template('login.html')

@app.route("/link", methods=['POST'])
def link():
  email=request.form['email']
  m = hashlib.md5()
  m.update(email)
  m.update(app.config['SECRET'])
  h = m.hexdigest()
  user = User.query.filter_by(email=email).first()
  if user is None:
    return jsonify(result='invalid')
  else:
    sendlink(user)
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

