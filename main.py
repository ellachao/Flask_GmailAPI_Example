# -*- coding: utf-8 -*-
#pip install flask-oauthlib first
from flask_oauthlib.client import OAuth
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
import re

#TODO: logout, data flow, make templates, better regex, redirect to first page

app = Flask(__name__)
app.config['GOOGLE_ID'] = "ID"
app.config['GOOGLE_SECRET'] = "SECRET"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)


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


#displays the index.html page
@app.route('/',methods=['GET', 'POST'])
def getInput():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        session['keyword']=request.form["input"]
        #if form is submitted, takes user to authentication page
        return redirect(url_for('login', _external=True))



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
    #return redirect(url_for('getInput'))
    return redirect(url_for('requestEmails', _external=True))

@gmail.tokengetter
def get_google_oauth_token():
    return session.get('gmail_token')

@app.route('/request_emails')
def requestEmails():
    query=session['keyword']
    print query
    uId = session.get('user_id') 
    url = 'https://www.googleapis.com/gmail/v1/users/'+uId+'/messages' 
    #limits to 10 emails
    response = gmail.get(url, data = {'q':query,'maxResults': 10}) 
    data = response.data
    if data['resultSizeEstimate']==0:
            return render_template('table.html', r=True)
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
        d[messageId]=result.data
    count=processData(d)    
    return render_template('table.html', count=count);
    
    
#counts emails        
def processData(dic):
    result={}
    for i in dic:
        #from field
        person=dic[i]['payload']['headers'][1]['value']
        #need to fix regex
        eList=re.findall('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-.]+[a-zA-Z0-9-]+)',person)
        for e in eList:
            if e not in result:
                result[e]=1
            else:
                result[e]+=1
    return result


    
if __name__ == '__main__':
    app.debug = True
    app.run()

