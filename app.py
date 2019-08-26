from flask import Flask,render_template,request,redirect,url_for,Response,session,flash
from flask_mail import Mail,Message
from pymongo import MongoClient
import json
import urllib
import datetime
import threading,jinja2

mongo = MongoClient('mongodb+srv://cmsnoc93:'+ urllib.parse.quote('cmsnoc@123') + '@cluster0-qxw77.mongodb.net/test?retryWrites=true&w=majority')
db = mongo.CMS_Hiring
openingsDb = db.Openings
userDb = db.Users
app = Flask(__name__)
app.secret_key = 'some_secret'

@app.route('/view_openings/<manager>/<level>',methods=['GET','POST'])
def view_openings(manager,level):
    openings = openingsDb.find({'manager':manager})    
    if request.method == 'GET':
        m = dict()
        m['beg'] = 'Beginner'
        m['int'] =  'Intermediate'
        m['adv'] = 'Advanced'
        level_applied = m[level]
        return render_template('view_openings.html',openings=openings,chosen=level,lvl = level_applied)
     

@app.route('/add_opening',methods=['GET','POST'])
def add_opening():
    if request.method == 'GET':
        return render_template('add_opening.html')    
    if request.method == 'POST':          
        vertical = request.form['vertical']
        count = request.form['count']
        expertise = request.form['expertise']
        skills = request.form.getlist('skills')

        job = {"position":"NOC Engineer","requirements":skills,"expertise":expertise,"count":count,"tower":vertical}
        print(job)
        openingsDb.update( {"manager":session['username'],"levels.id":expertise},{"$inc": { "levels.$.count": int(count) },"$push":{"levels.$.jobs":job}})
        return redirect(url_for('landing'))
    
           

@app.route('/login', methods=['GET', 'POST'])
def login():

    if session and session['logged_in']:
        return redirect(url_for('landing'))

    m = dict()
    users = userDb.find()

    for u in users:
        m[u['username']] = u['password']

    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        if (request.form['username'] in m.keys()):
                if (m[request.form['username']] == request.form['password']):
                    session['logged_in'] = True
                    session['role'] = 'Admin'
                    session['username'] = request.form['username']                    
                    return redirect(url_for('landing'))
                else:                    
                    flash("Invalid Password", 'log_msg')
                    return redirect(url_for('login'))
        else:
            session['logged_in'] = True
            session['role'] = 'User'
            session['username'] = request.form['username'] 
            redirect(url_for('landing'))
            
        
    return redirect(url_for('login')) 

@app.route('/landing',methods=['GET','POST'])
def landing():

    openings = openingsDb.find()
    users = userDb.find()
    if request.method == 'GET':
        return render_template('landing.html', openings=openings)
    
    return render_template('landing.html', openings=openings, users=users)

        
@app.route('/logout',methods=['GET'])
def logout():
    session['logged_in'] = False
    flash(u'You were successfully logged  out!', 'log_msg')
    return redirect(url_for('login'))


@app.route('/add_obj',methods=['GET','POST'])
def add_obj():
    openingsDb.insert({"manager":"Vaibhav","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    openingsDb.insert({"manager":"Rashmikanth","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    
    return "Done"