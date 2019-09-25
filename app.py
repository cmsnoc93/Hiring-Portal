from flask import Flask,render_template,request,redirect,url_for,Response,session,flash
from flask_mail import Mail,Message
from pymongo import MongoClient
import json
import urllib
import datetime
import threading,jinja2
import os
import binascii
from bson import ObjectId
from ldap3 import Server,Connection,ALL
from functools import wraps
import datetime,random
# cmsnoc93:'+ urllib.parse.quote('cmsnoc@123') + '@cluster0-qxw77.mongodb.net/test?retryWrites=true&w=majority
mongo = MongoClient('mongodb+srv://cmsnoc93:'+ urllib.parse.quote('cmsnoc@123') + '@cluster0-qxw77.mongodb.net/test?retryWrites=true&w=majority')
db = mongo.CMS_Hiring
openingsDb = db.Openings
OpeningstempDb = db.Openings_temp
userDb = db.Users
JobsDb = db.Jobs
CandiDb = db.Candidates
app = Flask(__name__)
app.config.from_pyfile('config.cfg')
mail = Mail(app)
app.secret_key = 'some_secret'

# @app.route('/view_openings/<manager>/<level>',methods=['GET','POST'])
# def view_openings(manager,level):
#     openings = JobsDb.find({'manager':manager,'expertise':level})
#     if request.method == 'GET':
#         m = dict()
#         m['beg'] = 'Beginner'
#         m['int'] =  'Intermediate'
#         m['adv'] = 'Advanced'
#         level_applied = m[level]
#         return render_template('view_openings_temp.html',openings=openings,chosen=level,lvl = level_applied)
def technical_role(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if session:
        if session['role'] == 'Technical':
            return f(*args,**kwargs )
      else:
            return redirect(url_for('landing'))
    return decorated_function

@app.route('/email',methods=['GET'])
def email():
    msg = Message(subject='Test mail!',
                  body='This is a Flask generated Mail',
                  sender="araviana@cisco.com",
                  recipients="neemenon@cisco.com")
    mail.send(msg)
    return "Mail DONE"

@app.route('/view_openings/<manager>/<level>',methods=['GET','POST'])
def view_openings(manager,level):
    openings = JobsDb.find({'manager':manager,'expertise':level})
    if request.method == 'GET':
        m = dict()
        m['beg'] = 'Beginner'
        m['int'] =  'Intermediate'
        m['adv'] = 'Advanced'
        level_applied = m[level]
        return render_template('datatable_openings.html',openings=openings,chosen=level,manager=manager,lvl = level_applied)
     

@app.route('/add_opening',methods=['GET','POST'])
def add_opening():
   if session['role'] == 'User':
        flash('Sorry! not authorized for the page')
        return redirect(url_for('landing'))
   elif session['role'] == 'Admin' or session['role'] == 'Technical':
    if request.method == 'GET':
        return render_template('add_opening.html')    
    if request.method == 'POST':          
        jobs_arr = []
        id_arr = []
        vertical = request.form['vertical']
        count = request.form['count']
        expertise = request.form['expertise']
        skills = request.form.getlist('skills')
        date = request.form['date']
        technical_res = request.form.getlist('Hirer')
        for var in range(0,int(count)):   
            id = binascii.hexlify(os.urandom(16))
            id_arr.append(id)
            job = {"job_id":random.sample(range(10000, 99999) ,1)[0],"position":"NOC Engineer","requirements":skills,"expertise":expertise,"tower":vertical,'technical_cec':technical_res,'id':id,"manager":session['username'],"opening_date":date,'candidates':[]}
            jobs_arr.append(job)
        job_id = JobsDb.insert(jobs_arr)
        print(id_arr)
        for x in id_arr:
            a = JobsDb.find({'id':x})
            for p in a:
                print("HAHAHAHA")
                OpeningstempDb.update( {"manager":session['username'],"levels.id":expertise},{"$push":{"levels.$.jobs":p['_id']}})
        OpeningstempDb.update( {"manager":session['username'],"levels.id":expertise},{"$inc": { "levels.$.count": int(count) }})
        print("JOBS")
        print(jobs_arr)
        # for var in range(0,int(count)):   
        #     job_id = JobsDb.insert(job)
        #     print("inserted")
        #     print(job_id)
        #     print("\n\n\n\n")
        #     OpeningstempDb.update( {"manager":session['username'],"levels.id":expertise},{"$push":{"levels.$.jobs":job_id}}) 
        # print(job)
        # openingsDb.update( {"manager":session['username'],"levels.id":expertise},{"$inc": { "levels.$.count": int(count) },"$push":{"levels.$.jobs":job}})
        return redirect(url_for('landing'))

@app.route('/login1',methods = ['GET','POST'])
def login1():
    # if session and session['logged_in']:
    #     return redirect(url_for('landing'))
    m = dict()
    p = dict()
    users = userDb.find()

    for u in users:
        m[u['username']] = u['password']
        p[u['username']] = u['role']

    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        if (request.form['cec'] in m.keys()):
                if (m[request.form['cec']] == request.form['password']):
                    session['logged_in'] = True
                    session['role'] = p[request.form['cec']]
                    session['username'] = request.form['cec']
                    return redirect(url_for('landing'))
                else:
                    flash("Invalid Password", 'log_msg')
                    return redirect(url_for('login1'))
        else:
            session['logged_in'] = True
            session['role'] = p[request.form['cec']]
            session['username'] = request.form['cec']
            return redirect(url_for('landing'))


    return redirect(url_for('login1'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    # if session and session['logged_in']:
    #  return redirect(url_for('landing'))
    m = dict()
    p = dict()
    users = userDb.find()

    for u in users:
        m[u['cec']] = u['cec']
        p[u['cec']] = u['role']

    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':

        server = Server('ds.cisco.com')
        userdn = 'cn=' + request.form['cec'] + ',ou=Employees,ou=Cisco Users,dc=cisco,dc=com'
        try:
            conn = Connection(server, user=userdn, password=request.form['password'], check_names=True, lazy=False,
                              raise_exceptions=True)
            print(conn)
        except:
            flash('Cisco Authentication Failed', 'log_msg')
            return redirect(url_for('login'))

        try:
            conn.bind()
        except:
            flash('Cisco authentication Failed', 'log_msg')
            return redirect(url_for('login'))

        session['logged_in'] = True
        session['username'] = request.form['cec']

        if (request.form['cec'] in m.keys()):
            session['role'] = p[request.form['cec']]
        else:
            session['role'] = 'User'
        return redirect(url_for('landing'))
    print(session['role'])
    return redirect(url_for('login'))

@app.route('/landing',methods=['GET','POST'])
def landing():

   # openings = openingsDb.find()
    openings = OpeningstempDb.find()
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
    # openingsDb.insert({"manager":"Vaibhav","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    # openingsDb.insert({"manager":"Rashmikanth","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    # OpeningstempDb.insert({"manager":"Vaibhav","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    # OpeningstempDb.insert({"manager":"Rashmikanth","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    OpeningstempDb.insert({"manager":"araviana","levels":[{"id":"beg","count":0,"jobs":[]},{"id":"int","count":0,"jobs":[]},{"id":"adv","count":0,"jobs":[]}]})
    # userDb.insert({'username':'Aravind','cec':'araviana','password':'araviana'})
    return "Done"

@app.route('/adddetail/<id>', methods=['GET', 'POST'])
def add_detail(id):
    job = JobsDb.find({'_id':ObjectId(id)})
    req = []
    for x in job:
        req = x['requirements']
    return render_template('add_detail.html',id=id,req=req)

@app.route('/view_tech_interviews',methods=['GET','POST'])
def tech_inter():
    cecs = dict()
    candis = []
    all_jobs = JobsDb.find()
    for x in all_jobs:
        #print(x)
        if session['username'] in x['technical_cec']:
          if x['candidates']:
            for p in x['candidates']:
                candis.append(p)
    cand_det = CandiDb.find({'_id':{'$in':candis},'tech_done':0})
    return render_template('tech_interview.html', candidates =cand_det)

@app.route('/tech_status/<id>',methods=['GET','POST'])
def tech_status(id):
    name = ''
    cand_det = CandiDb.find({'_id': ObjectId(id)})
    for v in cand_det:
        name = v['name']
    return render_template('update_tech_status.html',name=name,id = id)

@app.route('/manager_status/<id>/<job_id>/<opening_id>',methods=['GET','POST'])
def manager_status(id,job_id,opening_id):
    name = ''
    cand_det = CandiDb.find({'_id': ObjectId(id)})
    for v in cand_det:
        name = v['name']
    return render_template('manager_update_status.html',name=name,id = id,job_id=job_id,opening_id = opening_id)

@app.route('/save_tech_update/<id>',methods=['POST'])
def save_tech_update(id):
    if request.method=='POST':
        status = int(request.form['status'])
        feedback = request.form['feedback']
    myquery = {"_id": ObjectId(id)}
    newvalues = {"$set": {"tech_done": status,"tech_feedback":feedback}}
    CandiDb.update_one(myquery, newvalues)
    return redirect(url_for('tech_inter'))

@app.route('/save_manager_update/<id>/<opening_id>',methods=['POST'])
def save_manager_update(id,opening_id):
    if request.method=='POST':
        status = int(request.form['status'])
        feedback = request.form['feedback']
        job_id = request.form['job_id']
    myquery = {"_id": ObjectId(id)}
    newvalues = {"$set": {"managerial_done": status,"manager_feedback":feedback}}
    CandiDb.update_one(myquery, newvalues)
    return redirect(url_for('view_jobs', id=opening_id,job_id=job_id))

@app.route('/sched_date/<id>',methods=['POST'])
def sched_date(id):
    date = request.form['int_date']
    myquery = {"_id":ObjectId(id)}
    newvalues = {"$set": {"sched_date": date}}
    CandiDb.update_one(myquery, newvalues)
    return redirect(url_for('tech_inter'))

@app.route('/save_detail/<id>', methods=['POST'])
def save_detail(id):
    if request.method == 'POST':
        name= request.form['name']
        skills = request.form.getlist('skill')
        profile = request.form['linked_in']
        quali = request.form['qualification']
        experience = request.form['experience']
        date_today = datetime.datetime.today().strftime('%d-%m-%Y')
        add_skill = request.form['add_skills']
        Check_num_of_jobs = JobsDb.find({'_id':ObjectId(id)})
        for x in Check_num_of_jobs:
         if len(x['candidates']) == 5:
             flash('Limit Reached!')
             return redirect(url_for('add_detail',id=id))
         elif len(x['candidates']) < 5:
            obj_id = CandiDb.insert({'name':name,'profile_url':profile,'skills':skills,'add_skills':add_skill,'qualification':quali,'experience':experience,'date':date_today,'vendor':session['username'],'tech_done':0,'managerial_done':0})
            JobsDb.update({'_id':ObjectId(id)} , {"$push": { "candidates": obj_id }})
    return redirect(url_for('landing'))

@app.route('/view_jobs/<id>/<job_id>', methods=['GET','POST'])
def view_jobs(id,job_id):
    selected_jobs = JobsDb.find({'_id':ObjectId(id)})
    candi = []
    for x in selected_jobs:
        candi = x['candidates']
    vacancies = CandiDb.find({'_id':{'$in': candi}})
    print(candi)
    return render_template('candidates.html', candidates = vacancies,job_id=job_id,opening_id=id)

@app.route('/candi_detail/<id>', methods=['GET'])
def candi_detail(id):
    name=''
    candi = CandiDb.find({"_id":ObjectId(id)})
    candi1 = CandiDb.find({"_id":ObjectId(id)})
    for x in candi1:
        print(x)
        name = x['name']
    print(name)
    return render_template('view_cand_detail.html',records=candi,name=name)

@app.route('/delete/<manager>/<level>/<id>', methods=['GET', 'POST'])
def delete(manager,level,id):
    levels = []
    level_d = dict()
    level_d['beg'] = 0
    level_d['int'] = 1
    level_d['adv'] = 2
    ans = OpeningstempDb.find({"manager":manager})
    for x in ans:
        levels = x['levels']
    #print(ObjectId(id))
    print(levels)
    print(levels[level_d[level]])
    print("\n\n")
    if ObjectId(id) in levels[level_d[level]]['jobs']:
        index  = levels[level_d[level]]['jobs'].index(ObjectId(id))
        del  levels[level_d[level]]['jobs'][index]
        count = levels[level_d[level]]['count'] - 1
        new_jobs = levels[level_d[level]]['jobs']
        OpeningstempDb.update({"manager": manager, "levels.id": level},{"$set": {"levels.$.jobs": new_jobs, "levels.$.count":count}})
    myquery = {"_id": ObjectId(id)}
    JobsDb.remove(myquery)
    print(levels[level_d[level]]['jobs'])

    return redirect(url_for('landing'))