from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import certifi
import os
from werkzeug.utils import secure_filename
from bson import ObjectId

app=Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB setup
client = MongoClient("mongodb+srv://naokomca:4DV3wwzaOzYdu5iD@cluster0.cedhibt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", tlsCAFile=certifi.where())
db = client['Community_site'] 
users_collection = db['users']
items_collection = db['items']
profiles_collection = db['profiles']


# Home
@app.route('/')
def home():
    items = list(items_collection.find())
    return render_template('home.html', items=items)

 # Sign Up   
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            return "Username already exists"
        
        hashed_pw =generate_password_hash(password)
        users_collection.insert_one({
           'username': username,
           'password': hashed_pw
       })
        
        return redirect('/login')
    return render_template('signup.html')
        
# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username=request.form.get('username')
        password=request.form.get('password')

        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
          session['username'] = username
          return redirect('/dashboard')
        else: 
            return "Invalid username or password"
    return render_template('login.html')
    
# Dashboard
@app.route('/dashboard')
def dashboard():
 
  if 'username' not in session:
    return redirect('/login')
  
  username = session['username']
  user_items = list(items_collection.find({'username': username}))
  print(user_items)
  profile=profiles_collection.find_one({'username': username})

  return render_template(
      'dashboard.html', 
      username=username,
      items=user_items,
      profile=profile
    )

# Logout  
@app.route('/logout')
def logout():
   session.clear()
   return redirect('/login')

# Add Item (New Create)
@app.route('/create', methods=['GET', 'POST'])
def create():

    if 'username' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        title=request.form.get('title')
        description = request.form.get('description')
        image_file = request.files['image']

        image_filename= None
        if image_file and image_file.filename != '':
            filename= secure_filename(image_file.filename)
            image_path = os.path.join('static/images', filename)
            image_file.save(image_path)
            image_filename =filename
           
        items_collection.insert_one({
            'username': session['username'],
            'title': title,
            'description': description,
            'image': image_filename
        })

        return redirect('/dashboard')
    return render_template('create.html')

# Edit Item
@app.route('/edititem/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'username' not in session:
        return redirect('/login')
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if not item or item['username'] != session['username']:
        return "Unauthorized", 403
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': {'title': title, 'description': description}}
        )
        return redirect('/dashboard')
    
    return render_template('edititem.html', item=item)


# Edit Profile
@app.route('/editprofile', methods=['GET', 'POST'])
def edit_profile():

    if 'username' not in session:
        return redirect('/login')
    
    username=session['username']
    
    if request.method == 'POST':
       bio = request.form.get('bio')
       image_url = request.form.get('image_url')

       profile_data={
           'username': username,
           'bio': bio,
           'image_url': image_url
       }

       existing_profile = profiles_collection.find_one({'username': username})
       if existing_profile:
          profiles_collection.update_one({'username': username}, {'$set': profile_data})
       else:
           profiles_collection.insert_one(profile_data)

       return redirect('/dashboard')
    
    profile = profiles_collection.find_one({'username': username})
    
    return render_template('editprofile.html', profile=profile) #from HTML to pyton

@app.route('/market')
def market():
    all_items = list(items_collection.find())
    return render_template('market.html', items=all_items)


if __name__ == '__main__':
    app.run(debug=True)
