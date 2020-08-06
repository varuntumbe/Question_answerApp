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
    user_info=get_current_user()
    if user_info:

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            SELECT name FROM users JOIN questions on questions.user_id=users.id 
            AND questions.answer_text is NOT NULL
        """)
        asked_by=cur.fetchall()
        cur.execute(""" 
            SELECT name FROM users JOIN questions on questions.expert_id=users.id 
            AND questions.answer_text is NOT NULL
        """)
        answered_by=cur.fetchall()
        return render_template('home.html',user_info=user_info,asked_by=asked_by,answered_by=answered_by)
    return render_template('home.html',user_info=user_info)

@app.route('/register',methods=['GET','POST'])
def regi():
#    user_info=get_current_user()  
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
        return render_template('home.html',user_info=None)

    return render_template('register.html',user_info=None)

@app.route('/login',methods=['GET','POST'])
def login():
    user_info=get_current_user()
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
        if user_info and check_password_hash(user_info['password'],password):
            session['user']=user_info['name']
            return redirect(url_for('index'),code=302)
        else:
            return render_template('login.html',user_info=user_info)

    return render_template('login.html',user_info=user_info)

@app.route('/question')
def question():
    user_info=get_current_user()

    #database part
    conn=database.get_db()
    cur=conn.cursor()
    cur.execute(""" 
        SELECT * FROM questions 
    """)
    question_lists=cur.fetchall()
    cur.execute(""" 
        SELECT name FROM  users JOIN questions
        WHERE users.id=questions.user_id 
    """)
    asked_by=cur.fetchall()
    cur.execute(""" 
        SELECT name FROM  users JOIN questions
        WHERE users.id=questions.expert_id
    """)
    answered_by=cur.fetchall()
    return render_template('question.html',questions_info=question_lists,
    user_info=user_info,asked_by=asked_by,answered_by=answered_by)

@app.route('/answer/<question_id>')
def answer(question_id):
    user_info=get_current_user()
    if user_info:

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            SELECT * FROM questions WHERE id=(?) 
        """,(question_id,))
        question_info=cur.fetchone()
        return render_template('answer.html',user_info=user_info,qinfo=question_info)

    return redirect(url_for('login'),code=302)

@app.route('/ask',methods=['GET','POST'])
def ask():
    user_info=get_current_user()
    if request.method=='POST' and user_info:
        question_text=request.form.get('question_text')
        expert_id=request.form.get('expert_id')
        user_id=user_info['id']

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            INSERT INTO questions (question_text,user_id,expert_id)
            VALUES (?,?,?)
        """,(question_text,user_id,expert_id))
        conn.commit()

        return redirect(url_for('question'),code=302)

    if user_info:

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            SELECT * FROM users WHERE expert=(?)
        """,(True,))
        expert_list=cur.fetchall()
        return render_template('ask.html',user_info=user_info,expert_list=expert_list)
    else:
        return redirect(url_for('login'),code=302)

@app.route('/unanswered')
def unanswered():
    user_info=get_current_user()

    if user_info and user_info['expert']:
        user_id=user_info['id']

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            SELECT name,questions.id FROM users JOIN questions
            on users.id=questions.user_id AND questions.expert_id=(?)
            AND questions.answer_text IS NULL
        """,(user_id,))
        asked_by=cur.fetchall()
        return render_template('unanswered.html',user_info=user_info,asked_by=asked_by)

    return render_template('unanswered.html',user_info=user_info)

@app.route('/users',methods=['GET','POST'])
def users():
    user_info=get_current_user()

    #database part
    conn=database.get_db()
    cur=conn.cursor()
    cur.execute(""" 
        SELECT id,name,expert,admin from users 
    """)
    users=cur.fetchall()
    return render_template('users.html',user_info=user_info,users=users)

@app.route('/logout')
def logout():
#    user_info=get_current_user()
    session.pop('user',None)
    return redirect(url_for('index'),code=302)


@app.route('/promote/<username>')
def promote(username):
    user_info=get_current_user()
    act=request.args.get('action')
    if user_info and username:

        if act=='add':
            #database part
            conn=database.get_db()
            cur=conn.cursor()
            cur.execute(""" 
                UPDATE users SET expert=(?) 
                WHERE name=(?)
            """,(True,username))
            conn.commit()
            return redirect(url_for('users'),code=302)
        else:
            #database part
            conn=database.get_db()
            cur=conn.cursor()
            cur.execute(""" 
                UPDATE users SET expert=(?) 
                WHERE name=(?)
            """,(False,username))
            conn.commit()
            return redirect(url_for('users'),code=302)            


@app.route('/handleanswer/<question_id>',methods=['POST'])
def store_answer(question_id):
    user_info=get_current_user()
    if user_info:
        answer_text=request.form.get('answer_text')
        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            UPDATE questions SET answer_text=(?) 
            WHERE id=(?)
        """,(answer_text,question_id))
        conn.commit()
        return redirect(url_for('unanswered'),code=302)




#some useful functions
def get_current_user():
    user_info=None
    if 'user' in session:

        #database part
        conn=database.get_db()
        cur=conn.cursor()
        cur.execute(""" 
            SELECT * FROM users WHERE NAME=(?)
        """,(session['user'],))
        user_info=cur.fetchone()
    return user_info


if __name__ == "__main__":
    app.run()