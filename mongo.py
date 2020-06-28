from flask import Flask, jsonify, request, json,send_file,redirect,url_for,session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from bson.json_util import dumps
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'final'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/final'
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['SECRET_KEY'] ='super-secret'


mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

CORS(app)

@app.route('/users/register',methods=['POST'])
def register():
    users = mongo.db.users
    username = request.json['username']
    email = request.json['email']
    passwordtest=request.json['password']
    password = bcrypt.generate_password_hash(passwordtest).decode('utf-8')
    created = datetime.utcnow()
    if username =='':
        resp = jsonify({"msg":'username can not be empty'})
        return resp
    if email =='':
        resp = jsonify({"msg":'invalid email'})
        return resp
    if len(passwordtest) < 6:
            resp = jsonify({"msg":'Make sure your password is at least 6 letters'})
            return resp
    existing_users = users.find_one({'email':request.json['email']})
    if existing_users is None:
        user_id = users.insert({
            'username':username,
            'email':email,
            'password':password,
            'created':created
        })
        resp=jsonify({"msg":'registered successfully!'})
        return resp
    resp = jsonify({"msg":'user already exists!'})
    return resp

@app.route('/users/login',methods=['POST'])
def login():
    users = mongo.db.users
    email = request.json['email']
    password = request.json['password']
    result = ""

    login_user = users.find_one({'email':email})

    if login_user:
        if bcrypt.check_password_hash(login_user['password'],password):
            access_token = create_access_token(identity = {
                'username':login_user['username'],
                'email':login_user['email']
            })
            #session['email'] = login_user['email']
            #session['username'] = login_user['username']

            result = jsonify({'token':access_token})
            #result = jsonify({'session':session['email']+'--'+session['username']})
        else:
            result = jsonify({"msg":'Invalid username and password'})
    else:
            result = jsonify({"msg":"No results found"})
    return result


@app.route('/profile')
def profile():
    users = mongo.db.users
    login_user = users.find(email=session['email'])
    result = jsonify({'firstname' :login_user['username']+'email' +login_user['email']})
    return result
    



@app.route('/users/update',methods=['POST'])  #for update the user (username, password )
def update():
    if request.method == 'POST':
        users = mongo.db.users
       # the_user = users.find_one({"email":request.form['email']})
       # _id = id
        email = request.json['email']
        username = request.json['username']
        password = bcrypt.generate_password_hash(request.json['password']).decode('utf-8')
      
        #mongo.db.users.update_one({'_id':ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)},{'$set':{'username':username,'password':password}})
        update_user= mongo.db.users.update_one({'email':email},{'$set':{'username':username,'password':password}})
        #resp = jsonify({"email":update_user['email'],"username":update_user['username'],"password":update_user['password']})
        resp=jsonify('updated!')
        return resp
   


@app.route('/users/post',methods=['POST']) # add a new post according to the user
def post():
    if request.method == 'POST':
        users = mongo.db.users
        the_user = users.find_one({"email":request.form['email']})
        #login_user = users.filter(email=create_access_token['email']).first()
        date = datetime.utcnow()

        posts = mongo.db.posts
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'msg' : 'No file selected for uploading'})
            return resp
        mongo.save_file(file.filename,file)

      
        post = posts.insert({"title":title,"content":content,"category":category,'file':file.filename,'user_id':the_user['_id'],'username':the_user['username'],'date':date, 'like':0, 'dislike':0})
        resp = jsonify({'msg':'you have added new post!'})
        return resp



  
   

@app.route('/users/posts',methods=['GET']) #to get all the posts
def get_posts():
    posts = mongo.db.posts.find()
    resp = dumps(posts)
    return resp


@app.route('/get_post',methods=['POST']) #get all post specific for a user
def get_post():
    
    users = mongo.db.users
    the_user = users.find_one({"email":request.json['email']})

    posts = mongo.db.posts
    user_post = posts.find({'user_id':the_user['_id']})
    post_list =''
    #for e in user_post:
    #    post_list += e['title'] +'---'+e['content']+'--'+e['category']+'--'+e['file']+'--'
    #return post_list
    resp = dumps(user_post)
    return resp

#@app.route('/getId/<email>',methods=['GET'])
#def get_id(email):
 #   users = mongo.db.users
  #  the_user = users.find_one({"email":email})
   # resp= the_user['_id'].toString()
    #return resp


@app.route('/get_username') #get username from the post no use because already insert the username when add post
def username():
    users= mongo.db.users

    post_username = users.find_one({"email":request.json['email']})

    posts = mongo.db.posts

    post_user = posts.find_one({"user_id":post_username['_id']})

    if post_user['user_id'] == post_username['_id']:
        return post_username['username']

    resp = jsonify({'username': post_username['username']})
    return resp
    


#@app.route('/download',methods=['GET'])
#def download():
    #users = mongo.db.users
    #the_user = users.find_one({"email":request.json['email']})

    #posts = mongo.db.posts
    #user_post = posts.find({'user_id':the_user['_id']})
    #post_list =''
    #for e in user_post:
     #   post_list += e['file']+'--'
    #file = posts.find({'file':"Assignment 6.pdf"})
    #return post_list
    #if post_list:
     #   file=post_list['file']
     #file_data=
    #return send_file((BytesIO(file_data,file)),attachment_filename='flask.pdf',as_attachment=True)

@app.route('/file',methods=['POST'])  #to download the file given a filename
def file():
        file = request.json['file']
        return mongo.send_file(file)


@app.route('/updatepost/<id>',methods=['POST']) #update the post: title, content, category first
def updatePost(id):
    if request.method == 'POST':
        _id = id
        posts = mongo.db.posts
        title = request.json['title']
        content = request.json['content']
        category = request.json['category']

        mongo.db.posts.update_one({'_id':ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)},{'$set':{'title':title,'content':content,'category':category}})
        resp = jsonify('you have updated the post!')
        return resp





@app.route('/deletepost',methods=['DELETE']) #delete the post
def delete():
        title=request.json['title']
        posts = mongo.db.posts
        posts.delete_one({'title':title})
        resp = jsonify('post deleted')
        return resp

        
@app.route('/plusLike',methods=['POST']) #add 1 to the like counter of a specific post
def plusLike():
    if request.method == 'POST':
        id1=request.json['id']

        id = ObjectId(id1)
        existingPost = mongo.db.posts.find_one({'_id': id})
        result = existingPost['like']
        likeCounter=result+1
        postExists = mongo.db.posts.update_one({'_id': id},{'$set':{'like':likeCounter}})
        if postExists is None :
            resp = jsonify('like counter did not increase successfully!')
            return resp
        else :
            resp = jsonify('like counter increased successfully!')
            return resp


@app.route('/plusDislike',methods=['POST']) #add 1 to the dislike counter of a specific post
def plusDislike():
    if request.method == 'POST':
        id1=request.json['id']

        id = ObjectId(id1)
        existingPost = mongo.db.posts.find_one({'_id': id})
        result = existingPost['dislike']
        likeCounter=result+1
        postExists = mongo.db.posts.update_one({'_id': id},{'$set':{'dislike':likeCounter}})
        if postExists is None :
            resp = jsonify('dislike counter did not increase successfully!')
            return resp
        else :
            resp = jsonify('dsilike counter increased successfully!')
            return resp



if __name__ == '__main__':
    app.run(debug =True )
