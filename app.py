from flask import Flask, render_template, request, redirect, session, Markup, send_file
from models.firebaseAuth import *
from models.databaseConfig import *
import pyrebase
import string, random
import requests
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)

# import secrets
# secrets.token_urlsafe(16)
app.config['SECRET_KEY'] = 'OYsOFfvZ-6DRJomg04GTig'

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
                session["authenticated"] = True
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
            return('<h2>User not logged in</h2>')
    
    elif request.method == 'POST':
        session["meterVal"] = request.form['meterSelect']
        return redirect('/date')


# Date Select Page
@app.route('/date', methods=["GET", "POST"])
def date():
    if request.method == 'GET':
        if session.get("authenticated", None):
            meterVal = session.get("meterVal", None)
            meterConfig = METERNAME_CONFIG_MAPPING[meterVal]
            meter = pyrebase.initialize_app(meterConfig)
            db = meter.database()
            dates = list(db.child("/Timestamp Data").shallow().get().val())
            dates.sort(key=lambda date:datetime.strptime(date, '%d-%m-%Y'))
            staticData = db.child("/Static Information").get().val()
            name, sno, year = staticData['Manufacturer Name'], staticData['Serial No'], staticData['Manufacture Year']
            meterInfo = [name, sno, year]
            return render_template('date.html', meterInfo=meterInfo, dates=dates)
        else:
            return('<h2>User not logged in</h2>')

    elif request.method == 'POST':
        if request.form['datePage'] == 'dateValue':
            dateVal = request.form['date']
            session["dateVal"] = dateVal
            return redirect('/charts')
        elif request.form['datePage'] == 'liveData':
            return redirect('/live')


# Live Data Page
@app.route('/live', methods=["GET", "POST"])
def live():
    if request.method == 'GET':
        if session.get("authenticated", None):
            meterVal = session.get("meterVal", None)
            meterConfig = METERNAME_CONFIG_MAPPING[meterVal]
            dbURL = meterConfig['databaseURL'] + '/Real Time Data.json'
            return render_template('live.html', dbURL=dbURL)
        else:
            return('<h2>User not logged in</h2>')


# Charts Page
@app.route('/charts', methods=["GET", "POST"])
def chart():
    if request.method == 'GET':
        if session.get("authenticated", None):
            meterVal = session.get("meterVal", None)
            dateVal = session.get("dateVal", None)
            meterConfig = METERNAME_CONFIG_MAPPING[meterVal]
            meter = pyrebase.initialize_app(meterConfig)
            db = meter.database()
            times = list(db.child("/Timestamp Data/"+dateVal).shallow().get().val())
            data = db.child('Timestamp Data/'+dateVal).get()
            df = pd.DataFrame(data.val())
            df.loc['Power'].to_json('power.json')
            dfPower = pd.read_json('power.json')
            df.loc['Energy'].to_json('energy.json')
            dfEnergy = pd.read_json('energy.json')
            os.remove('power.json')
            os.remove('energy.json')
            df.drop(['Power', 'Energy'], axis = 0, inplace = True)
            df = df.append([dfPower, dfEnergy]).T
            df.reset_index(level=0, inplace=True)
            df.rename(columns={"index": "Time"}, inplace=True)
            paramValues = {}
            for param in df.columns:
                paramValues[param] = df[param].tolist()
            df.to_csv('data.csv', index=False)
            return render_template('charts.html', paramValues=paramValues)
        else:
            return('<h2>User not logged in</h2>')

    elif request.method == 'POST':
        if request.form['submit'] == 'DataDownload':
            meterVal = session.get("meterVal", None)
            dateVal = session.get("dateVal", None)
            filename = 'Meter' + str(meterVal[1]) + '(' + str(dateVal) + ').csv'
            return send_file('data.csv', attachment_filename=filename, as_attachment=True)


# Logout Page
@app.route("/logout")
def logout():
    session.clear()
    session["authenticated"] = False
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)