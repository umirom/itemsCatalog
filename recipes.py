from flask import Flask, render_template, request, redirect, url_for
from flask import flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Recipe, User

# imports for anti forgery state token for Google OAth
from flask import session as login_session
import random
import string

# imports for gconnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# import for decorator function
from functools import wraps
from flask import g

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Hipster Recipe Database"

engine = create_engine('sqlite:///recipedatabasewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create function decorator for functions where users need to be logged in
# Unfortunatley, it is not yet working

"""
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You need to be logged in to perform this action!')
            return redirect ('/login')
        return decorated_function
"""

# Create a state token to prevent request forgery
# Store it in the session for later validation


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# CONNECT with Facebook
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/'
    'access_token?grant_type=fb_exchange_token&client_id='
    '%s&client_secret=%s&'
    'fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the first index
        which gives us the key : value for the server access token
        then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing
        so that it can be used directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/'
    'me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/'
    'picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px;height: 300px;border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# DISCONNECT from Facebook


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?'
    'access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# CONNECT with Google Plus


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response
        (json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # check if user exists - if not, make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += '<br/>'
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px;height: 150px;border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User helper functions to create a user,
# retrieve user info and get a user's id


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
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

# DISCONNECT from Google Plus


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']

    # only disconnect a connected user
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Curr. user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?'
    'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Make API endpoints for JSON


@app.route('/overview/<int:cat_id>/JSON')
def showCategoryJSON(cat_id):
    category = session.query(Category).filter_by(id=cat_id)
    recipes = session.query(Recipe).filter_by(category_id=cat_id).all()
    return jsonify(Recipes=[r.serialize for r in recipes])


@app.route('/recipe/<int:rec_id>/JSON')
def showRecipeJSON(rec_id):
    recipe = session.query(Recipe).filter_by(id=rec_id).one()
    return jsonify(Recipe=recipe.serialize)

# Routing functions

# Show all categories and recipes on app landing page


@app.route('/')
@app.route('/overview')
def Overview():
    categories = session.query(Category).all()
    recipes = session.query(Recipe).all()
    users = session.query(User).all()
    if 'username' not in login_session:
        return render_template(
            'overview_public.html',
            categories=categories, recipes=recipes, users=users)
    else:
        return render_template(
            'overview.html',
            categories=categories, recipes=recipes,
            login_session=login_session, users=users)

# Show all recipes within a given category


@app.route('/<int:cat_id>')
@app.route('/overview/<int:cat_id>')
def showCategory(cat_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    recipes = session.query(Recipe).filter_by(category_id=cat_id).all()

    if 'username' not in login_session:
        return render_template(
            'showcategory_public.html',
            category=category, recipes=recipes)
    else:
        return render_template(
            'showcategory.html',
            category=category, recipes=recipes, login_session=login_session)

# Show a specific recipe


@app.route('/recipe/<int:rec_id>')
@app.route('/overview/recipe/<int:rec_id>')
def showRecipe(rec_id):
    recipe = session.query(Recipe).filter_by(id=rec_id).one()
    creator = getUserInfo(recipe.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template(
            'showrecipe_public.html', recipe=recipe, creator=creator)
    else:
        return render_template(
            'showrecipe.html',
            recipe=recipe, login_session=login_session, creator=creator)

# Add a new recipe - only possible if user is logged in


@app.route('/new', methods=['GET', 'POST'])
@app.route('/overview/recipe/new', methods=['GET', 'POST'])
@app.route('/<int:cat_id>/new', methods=['GET', 'POST'])
@app.route('/overview/<int:cat_id>/new', methods=['GET', 'POST'])
# @login_required
def addRecipe():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newRecipe = Recipe(
            name=request.form['recipe_name'],
            user_id=login_session['user_id'],
            category_id=request.form['recipe_category'],
            description=request.form['recipe_description'],
            instruction=request.form['recipe_instruction'])
        session.add(newRecipe)
        session.commit()
        flash("Sweet! New recipe added to the database.")
        return redirect(url_for('Overview'))
    else:
        categories = session.query(Category).all()
        return render_template(
            'addrecipe.html',
            categories=categories, login_session=login_session)

# Edit an existing recipe
# only possible if user is logged in AND recipe was created by him


@app.route('/recipe/<int:rec_id>/edit', methods=['GET', 'POST'])
@app.route('/overview/recipe/<int:rec_id>/edit', methods=['GET', 'POST'])
def editRecipe(rec_id):

    if 'username' not in login_session:
        return redirect('/login')

    editedRecipe = session.query(Recipe).filter_by(id=rec_id).one_or_none()
    if editedRecipe.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this recipe. You can only edit recipes that were created by you.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['recipe_name']:
            editedRecipe.name = request.form['recipe_name']
        if request.form['recipe_description']:
            editedRecipe.description = request.form['recipe_description']
        if request.form['recipe_instruction']:
            editedRecipe.instruction = request.form['recipe_instruction']

        session.add(editedRecipe)
        session.commit()
        flash("Recipe updated! I hope you made it hipper than it used to be.")

        # redirect to Recipe
        return redirect(url_for('showRecipe', rec_id=rec_id))
        # return redirect(url_for('Overview'))
    else:
        categories = session.query(Category).all()
        return render_template(
            'editrecipe.html', recipe=editedRecipe,
            categories=categories, login_session=login_session)

# Delete an existing recipe
# only possible if user is logged in AND recipe was created by him


@app.route('/recipe/<int:rec_id>/delete', methods=['GET', 'POST'])
@app.route('/overview/recipe/<int:rec_id>/delete', methods=['GET', 'POST'])
def deleteRecipe(rec_id):

    if 'username' not in login_session:
        return redirect('/login')

    deletedRecipe = session.query(Recipe).filter_by(id=rec_id).one_or_none()
    if deletedRecipe.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to delete this recipe. You can only delete recipes that were created by you.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(deletedRecipe)
        session.commit()
        flash("Item wasn't hip enough for this world and has been deleted.")
        return redirect(url_for('Overview'))
    else:
        return render_template(
            'deleterecipe.html',
            recipe=deletedRecipe, login_session=login_session)

# Disconnect function that can be used for different OAuth's


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('You have successfully been logged out')
        return redirect(url_for('Overview'))
    else:
        flash('You were not logged in.')
        return redirect(url_for('Overview'))

if __name__ == '__main__':
    # secret key needed for flash messages
    app.secret_key = 'super-secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
