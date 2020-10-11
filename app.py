from flask import Flask, render_template, request, redirect, session, Markup, send_file
from models.firebaseAuth import *
from models.databaseConfig import *
import pyrebase
import string, random
import requests
from datetime import datetime

app = Flask(__name__)

# import secrets
# secrets.token_urlsafe(16)
app.config['SECRET_KEY'] = 'KIxqJtOFwM0ZFTnyvpZpfg'

users = pyrebase.initialize_app(userAuthConfig)
auth = users.auth()
userDb = users.database()
authenticated = False


# Login Page
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()
        return render_template('login.html')
    
    elif request.method == 'POST':
        if request.form['auth'] == 'SignIn':
            try:
                login = user_login(auth, request.form['email'], request.form['password'])
                authenticated = True
                session["authenticated"] = authenticated
                return redirect('/home')
            except requests.exceptions.HTTPError as e:
                return render_template('login.html', message='Wrong Email ID/Password.')
        elif request.form['auth'] == 'SignUp':
            password = ''.join(random.sample((string.ascii_uppercase+string.digits),6))
            email, name, contact = request.form['email'], request.form['name'], request.form['contact']
            try:
                user = create(auth, email, password, name, contact)
                data = {'name': name, 'contact': contact, 'role': ''}
                userDb.child('Users').child(email[:email.find('@')]+email[email.find('@'):][:email[email.find('@'):].find('.')]).set(data)
                verification(auth, email, password)
                return render_template('login.html', message='Successfully Signed Up. Contact the administrator for password.')
            except requests.exceptions.HTTPError as e:
                return render_template('login.html', message='Email Address already exists.')


# Meter Select Page
@app.route('/home', methods=["GET", "POST"])
def meter():
    if request.method == 'GET':
        if session.get("authenticated", None):
            return render_template('home.html')
        else:
            return('<h1>User not logged in</h1>')
    
    elif request.method == 'POST':
        session["meterVal"] = request.form['meterSelect']
        return redirect('/date')


# Date Select Page
@app.route('/date', methods=["GET", "POST"])
def date():
    if request.method == 'GET':
        if session.get("authenticated", None):
            meterVal = session.get("meterVal", None)
            if meterVal == 'M1':
                meterConfig = meter1Config
            elif meterVal == 'M2':
                meterConfig = meter2Config
            meter = pyrebase.initialize_app(meterConfig)
            db = meter.database()
            
            dates = list(db.child("/Timestamp Data").shallow().get().val())
            dates.sort(key=lambda date:datetime.strptime(date, '%d-%m-%Y'))

            static = db.child("/Static Information").get().val()
            name, sno, year = static['Manufacturer Name'], static['Serial No'], static['Manufacture Year']
            meterInfo = [name, sno, year]
            return render_template('date.html', meterInfo=meterInfo, dates=dates)
        else:
            return('<h1>User not logged in</h1>')

    elif request.method == 'POST':
        if request.form['datePage'] == 'dateValue':
            date = request.form['date']
            session["date"] = date
            return redirect('/charts')
        elif request.form['datePage'] == 'liveData':
            return redirect('/live')


# Live Data Page
@app.route('/live', methods=["GET", "POST"])
def live():
    if request.method == 'GET':
        meterVal = session.get("meterVal", None)
        if meterVal == 'M1':
            meterConfig = meter1Config
        elif meterVal == 'M2':
            meterConfig = meter2Config
        dbURL = meterConfig['databaseURL'] + '/Real Time Data.json'
        return render_template('live.html', dbURL=dbURL)


# Charts Page
@app.route('/charts', methods=["GET", "POST"])
def chart():
    if request.method == 'GET':
        return render_template('charts.html')

    elif request.method == 'POST':
        if request.form['submit'] == 'DataDownload':
            meterVal = session.get("meterVal", None)
            date = session.get("date", None)
            filename = str(meterVal[0]) + 'eter' + str(meterVal[1]) + '(' + str(date) + ').csv'
            return send_file('data.csv', attachment_filename=filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)