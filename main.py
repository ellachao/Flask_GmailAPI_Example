# -*- coding: utf-8 -*-
#pip install flask-oauthlib first
from flask_oauthlib.client import OAuth
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import requests

app = Flask(__name__)
app.config['GOOGLE_ID'] = "ID"
app.config['GOOGLE_SECRET'] = "SECRET"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)


#/ and no / makes a huge difference...
gmail = oauth.remote_app(
    'gmail', 
    consumer_key=app.config.get('GOOGLE_ID'), 
    consumer_secret=app.config.get('GOOGLE_SECRET'), 
    request_token_params={ 'scope': ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/userinfo.email'] },
    base_url='https://www.googleapis.com/oauth2/v2/', 
    authorize_url='https://accounts.google.com/o/oauth2/auth', 
    access_token_method='POST', 
    access_token_url='https://accounts.google.com/o/oauth2/token', 
    request_token_url=None,
)


@app.route('/',methods=['GET', 'POST'])
def hello():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        return render_template('index.html',result=request.form['input'])



@app.route('/login')
def login():
    return gmail.authorize(callback=url_for('authorized', _external=True))


@app.route('/login/authorized')
@gmail.authorized_handler
def authorized(resp):
    session['gmail_token'] = (resp['access_token'],) 
    user = gmail.get('userinfo') 
    session['user_email'] = user.data['email']
    session['user_id'] = user.data['id']
    #return jsonify({"data": user.data})
    return redirect(url_for('requestEmails', _external=True))

@gmail.tokengetter
def get_google_oauth_token():
    return session.get('gmail_token')

@app.route('/request_emails')
def requestEmails():
    #query=' ' 
    uId = session.get('user_id') 
    url = 'https://www.googleapis.com/gmail/v1/users/'+uId+'/messages' 
    response = gmail.get(url, data = {'maxResults': 10}) 
    data = response.data
    return getContent(data['messages'])
    
@app.route('/get_content')
def getContent(messages):
    d={}
    uId = session.get('user_id')
    for m in messages:
        messageId = m['id']
        #can't use array of strings to specify metadataHeaders
        #alternative approach
        url = 'https://www.googleapis.com/gmail/v1/users/'+uId+'/messages/'+messageId+'?format=metadata&metadataHeaders=From&&metadataHeaders=To&&metadataHeaders=Date'
        result=gmail.get(url)
        #print result
        d[messageId]=result.data
    return jsonify(d)
    
    
        

if __name__ == '__main__':
    app.debug = True
    app.run()

