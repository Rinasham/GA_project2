import psycopg2
from flask import Flask, request, redirect, render_template, session, flash
import requests
import bcrypt
## ------------ other files --------------
from db_settings import connectToDB, closeDB
from user import get_name
## ------------ options --------------
import random
import json
import os


SECRET_KEY = os.environ.get('SECRET_KEY', 'This is the secret key for session.')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


#----------------------------- Authentication -----------------------------------

@app.route('/signup')
def show_signup():
    return render_template('/signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    req_email = request.form.get('email')
    req_name = request.form.get('name')
    req_password1 = request.form.get('password1')
    req_password2 = request.form.get('password2')

    # flash for empty input
    if req_email =='' or req_name == '' or req_password1 =='' or req_password2 == '':
        flash('Please enter your email, name and password.','ng')
        return redirect('/signup')
    elif req_password1 != req_password2:
        flash('The password confirmation does not match. Please try again.', 'ng')
        return redirect('/signup')

    else:
        hashed_req_password = bcrypt.hashpw(req_password1.encode(), bcrypt.gensalt()).decode()

    # insert user into DB
    conn, cur = connectToDB()
    try:
        cur.execute("INSERT INTO users(email, name, hashed_password) VALUES(%s,%s,%s)", (req_email, req_name, hashed_req_password))
        conn.commit()
        print('Successfully inserted new user data into table.')
    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to insert new user data", error)
            return redirect['/signup']
    finally:
        if (conn):
            closeDB(conn,cur)

    return redirect('/login')


@app.route('/login')
def show_login():
    return render_template('/login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    req_password = request.form.get('password1')
    print(email)
    print(f'password: {req_password}')

    # flash for empty input
    if email =='' or req_password =='':
        flash('Please enter your email and password.','ng')
        return redirect('/login')
    else:
        conn, cur = connectToDB()
        try:
            cur.execute(f"SELECT id, hashed_password FROM users WHERE email='{email}'")
            result = cur.fetchone()
            print(result)
            ## check whether the password is correct or not
            hashed_password = result[1]
            is_valid = bcrypt.checkpw(req_password.encode(), hashed_password.encode())
            print(is_valid)
            # if the password is correct, set user-id to session
            if is_valid:
                found_id = result[0]
                print(f'User found. {found_id}')
                session['user_id'] = found_id
            else:
                print('Password does not match.')

        except TypeError as error:
            print('No such user.')
            flash('Invalid Credentials. Please try again.','ng')

        except  (Exception, psycopg2.Error) as error:
            if (conn):
                print("Failed to search the data.", error)

        finally:
            if (conn):
                closeDB(conn,cur)
    return redirect('/')


## log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



#----------------------------------------------------------------


@app.route('/')
def index():
    userId = session.get('user_id')
    print(userId)
    if userId != None:
        user = get_name(userId)
    else:
        user = None
    return render_template('home.html', user= user)



@app.route('/contact')
def showContact():
    return render_template('contact.html')


@app.route('/about')
def showAbout():
    return render_template('about.html')


#----------------------------- QUIZ -----------------------------------

@app.route('/quiz')
def quiz_top():


    return render_template('quiz-start.html')

@app.route('/quiz/<categoryName>')
def quiz_main(categoryName):
    print(categoryName)

    url = f'http://localhost:3000/quiz/{categoryName}'
    res = requests.get(url).json()
    # for obj in res:
    #     print(obj['tags'][0]['name'])

    quiz_list = random.sample(res, 1)
    print(json.dumps(quiz_list, indent=2))

    return render_template('quiz-main.html', list = quiz_list)



#----------------------------------------------------------------





#----------------------------- -----------------------------------


if __name__ == '__main__':
    app.run(debug=True)