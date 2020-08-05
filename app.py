from flask import Flask,render_template,g,request,session,redirect,url_for
import database
from werkzeug.security import generate_password_hash,check_password_hash
import os

app=Flask(__name__)
app.config['DEBUG']=True
app.config['SECRET_KEY']=os.urandom(24)

#Below function tears down database connection 
# everytime our request-response context ends
@app.teardown_appcontext
def close_db(err):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    user=None
    if 'user' in session:
        user=session['user']
    return render_template('home.html',user=user)

@app.route('/register',methods=['GET','POST'])
def regi():
    if request.method=='POST':
        hashed_password=generate_password_hash(request.form.get('password'),method='sha256')
        name=request.form.get('name')

        #Database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            INSERT INTO users (name,password,expert,admin)
            VALUES (?,?,?,?)
        """,[name,hashed_password,False,False])
        conn.commit()
        #connection will be automatically tear down when return statement executes
        return render_template('home.html')

    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        name=request.form.get('name')
        password=request.form.get('password')
        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute("""
            SELECT id,name,password FROM users 
            WHERE name=(?)
        """,(name,))
        user_info=cur.fetchone()
        if check_password_hash(user_info['password'],password):
            session['user']=user_info['name']
            return '<h1>matched!!</h1>'
        else:
            return '<h1>didnt match</h1>'

    return render_template('login.html')

@app.route('/question')
def question():
    return render_template('question.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/ask')
def ask():
    return render_template('ask.html')

@app.route('/unanswered')
def unanswered():
    return render_template('unanswered.html')

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('index'),code=302)


if __name__ == "__main__":
    app.run()