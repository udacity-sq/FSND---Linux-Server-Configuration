#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc, join, exists
from sqlalchemy.orm import sessionmaker
#added catalog.database_setup for AWL LS
from catalog.database_setup import Base, Catalog, Items, User 
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
# updated json.loads(client_secrets location) for AWS LS
CLIENT_ID = json.loads(open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web'
        ]['client_id']
APPLICATION_NAME = 'Catalog App'

# Need to add public pages and checks for User Authentication

# Add Database connections
# setup connections between the database, the orm and the python script

# updated code for AWS LS
engine = create_engine('postgresql://catalog:catalog@localhost/catalog.db') 
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase
                    + string.digits) for x in range(32)) #py3 -changed xrange to range
    login_session['state'] = state

    # return "The current session state is %s" % login_session['state']

    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'
                                 ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code

    code = request.data

    try:

        # Upgrade the authorization code into a credentials object
        # updated json.loads(client_secrets location) for AWS LS
        oauth_flow = flow_from_clientsecrets('/var/www/catalog/catalog/client_secrets.json',
                scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = \
            make_response(json.dumps('Failed to upgrade the authorization code.'
                          ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode())

    # If there was an error in the access token info, abort.

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = \
            make_response(json.dumps("Token's user ID doesn't match given user ID."
                          ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps("Token's client ID does not match app's."
                          ), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already connected.'
                          ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += \
        ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash('you are now logged in as %s' % login_session['username'])
    print ('done!')
    return output


# User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email'
            ]).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():

        # Only disconnect a connected user.

    access_token = login_session.get('access_token')
    if access_token is None:
        response = \
            make_response(json.dumps('Current user not connected.'),
                          401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':

        # Reset the user's sesson.

        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        flash('You have successfully logged out')
        return redirect(url_for('showCatalog'))
    else:

        # For whatever reason, the given token was invalid.

        response = \
            make_response(json.dumps('Failed to revoke token for given user.'
                          , 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Making an API Endpoint - providing a list of all Categories

@app.route('/catalog/json')
def catalogJSON():
    catalog = session.query(Catalog).all()
    return jsonify(allCatalog=[i.serialize for i in catalog])


# Making an API Endpoint - providing a list of all Items

@app.route('/catalog/items/json')
def itemsJSON():
    items = session.query(Items).all()
    return jsonify(allItems=[i.serialize for i in items])


# Main web App launch Page:

@app.route('/')
@app.route('/catalog')
def showCatalog():
    catalog = session.query(Catalog).all()
    Latest = session.query(Items.title, Catalog.category).join(Catalog,
            Items.category_id
            == Catalog.id).order_by(desc(Items.id)).limit(10)
    return render_template('catalog.html', catalog=catalog,
                           Items=Latest, session=login_session)


# Show all the items assocaited with a pirticular category

@app.route('/catalog/<category>/items')
def showItems(category):
    catalog = session.query(Catalog).all()
    items = session.query(Items.title, Catalog.category).join(Catalog,
            Items.category_id == Catalog.id).filter(Catalog.category
            == category)
    count = session.query(Items.title, Catalog.category).join(Catalog,
            Items.category_id == Catalog.id).filter(Catalog.category
            == category).count()
    if 'username' not in login_session:
        return render_template('publicshowItems.html', items=items,
                               category=category, catalog=catalog,
                               count=count)
    else:
        return render_template('showItems.html', items=items,
                               category=category, catalog=catalog,
                               count=count, session=login_session)


# Show detailed description of the catalog item

@app.route('/catalog/<category>/<title>')
def itemDetails(category, title):
    details = session.query(Items).filter_by(title=title).one()
    creator = getUserInfo(details.user_id)
    if 'username' not in login_session:
        return render_template('publicitemDetails.html',
                               details=details, category=category,
                               title=title, session=login_session)
    else:
        return render_template('itemDetails.html', details=details,
                               category=category, title=title,
                               creator=creator, session=login_session)


# Add an item

@app.route('/catalog/new', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        cat_id = session.query(Catalog.id).filter_by(category=category)
        newItem = Items(title=request.form['title'],
                        description=request.form['description'],
                        category_id=cat_id,
                        
                        user_id=login_session['user_id'])
        titleExists = session.query(exists().where(Items.title
                                   == title)).scalar()
        
        if not titleExists: 
            session.add(newItem)
            session.commit()
            addMessage = 'New Item Added - {}'.format(newItem.title)
            flash(addMessage)
            return redirect(url_for('showCatalog'))
        else:
            flash('Item already exists. Request can not be completed')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('addItem.html', session=login_session)


# Edit an item

@app.route('/catalog/<title>/edit', methods=['GET', 'POST'])
def editItem(title):

    # Item will contain both the Catalag - Category as well as the Item - title

    cat = session.query(Items.title, Catalog.category).join(Catalog,
            Items.category_id == Catalog.id).filter(Items.title
            == title).one()
    item = session.query(Items).filter_by(title=title).one()  # find item to edit
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit this Catalog item. Please create your own Catalog entry in order to perform edit function.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form['description']
        category = request.form['category']
        cat_id = session.query(Catalog.id).filter_by(category=category)
        item.category_id = cat_id
        session.add(item)
        session.commit()
        flash('Item Details updated Successfully')
        return redirect(url_for('showCatalog', session=login_session))
    else:
        return render_template('editItem.html', item=item, title=title,
                               category=cat.category,
                               session=login_session)


# Delete an item

@app.route('/catalog/<title>/delete', methods=['GET', 'POST'])
def deleteItem(title):
    if 'username' not in login_session:
        return redirect('/login')
    deleteMe = session.query(Items).filter_by(title=title).one()
    item = session.query(Catalog.category, Items.title).join(Items,
            Catalog.id == Items.category_id).filter(Items.title
            == title)
    if login_session['user_id'] != deleteMe.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own Catalog item in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(deleteMe)
        session.commit()
        deleteMessage = 'Item {} Successfully Deleted'.format(title)
        flash(deleteMessage)
        return redirect(url_for('showCatalog', session=login_session))
    else:
        return render_template('deleteItem.html', title=title,
                               category=item, session=login_session)

if __name__ == '__main__':
    #app.secret_key = 'super_secret_key' - commented out code for AWS LS
    #app.debug = True - commented out code for AWS LS
    app.run() # deleted contents of host & port for AWS LS
