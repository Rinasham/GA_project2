
import psycopg2
from flask import Flask, request, redirect, render_template, session, flash
import requests
import bcrypt
## ------------ other files --------------
from db_settings import DB_URL, connectToDB, closeDB
from user import get_name
from check_answer import check
## ------------ options --------------
import random
import json
import os
import datetime


SECRET_KEY = os.environ.get('SECRET_KEY', 'This is the secret key for session.')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

##--------gloval vals -------------------
page = ''
category_list = ['linux', 'network', 'computer', 'database', 'html', 'css', 'javascript', 'python', 'git']

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

def init_quiz():
    global quiz_list
    global quiz_count
    global correct_count
    global QandA_list

    quiz_list = []
    QandA_list = []
    quiz_count = 10
    correct_count = 0

#--------------------------------


@app.route('/')
def index():
    global page
    page = 'top'
    init_quiz()
    print(f'the length of the quiz_list is {len(quiz_list)} in /home')
    userId = session.get('user_id')
    if userId != None:
        user = get_name(userId)
    else:
        user = None
    return render_template('home.html', user=user, page=page)



@app.route('/contact')
def showContact():
    global page
    page = 'contact'
    init_quiz()
    return render_template('contact.html', page='contact')


@app.route('/about')
def showAbout():
    global page
    page = 'about'
    init_quiz()
    return render_template('about.html', page=page)


#----------------------------- API -----------------------------------

current_category = ''

@app.route('/quiz')
def quiz_top():
    global page
    page = 'quiz'

    return render_template('quiz-start.html', page=page)


@app.route('/quiz/<categoryName>')
def quiz_main(categoryName):
    global quiz_list
    global current_category
    current_category = categoryName

    # url = f'http://localhost:3000/quiz/{categoryName}'
    url = f'https://project2-node-express.herokuapp.com/quiz/{categoryName}'
    res = requests.get(url).json() # list

    list = random.sample(res, 10)
    for item in list:
        quiz_list.append(item)

    print(f'the length of the quiz_list is {len(quiz_list)} in /quiz and quiz count is {quiz_count}')

    return redirect('/progress')




#----------------------------Quiz control ------------------------------------

##------------ variable ---------------
quiz_list = []
current_quiz_answer = ''
quiz_count = 10
correct_count = 0
options_list = ['a', 'b', 'c', 'd']

##-------------------------------------


@app.route('/progress')
def handle_quiz():
    global quiz_list
    global quiz_count
    global current_quiz_answer
    global page

    page = 'quiz'
    if quiz_count > 0:
        print(f'the length of the quiz_list is {len(quiz_list)} in /progress[GET] and quiz count is {quiz_count}')
        next_quiz = quiz_list[quiz_count -1] # obj
        current_quiz_answer = next_quiz['correct_answer']
        # next_quiz.pop()
        print(str(quiz_count) + " quiz count")
        next_quiz = {
            'id' : next_quiz['_id'],
            'question' : next_quiz['question'],
            'answers' : next_quiz['answers'],
        }
        quiz_count -= 1
        return render_template('quiz-main.html', quiz = next_quiz, options_list = options_list, page=page)
    else:
        quiz_count = 10
        return redirect('/finish')




@app.route('/progress', methods=['POST'])
def check_answer():
    global correct_count
    chosen_answer = request.form.get('chosen-answer')

    # check whether the chosen answer was correct
    checked_answer = check(current_quiz_answer, chosen_answer)
    if checked_answer == True:
        correct_count += 1
    print('correct count is ' + str(correct_count))
    print(f'the length of the quiz_list is {len(quiz_list)} in /progress[POST] and quiz count is {quiz_count}')
    return redirect('/progress')


QandA_list = []

@app.route('/finish')
def show_answers():
    global quiz_list
    global QandA_list
    global page
    global current_category
    global correct_count

    page = 'quiz'

    # insert the game data into result table
    userID = session.get('user_id')
    current_date = datetime.datetime.now()

    # if the user has logged in, insert data and redirect to user page
    if userID != None:
        conn, cur = connectToDB()
        try:
            cur.execute(f"INSERT INTO results(player_id, all_quiz, correct_answers, category, date) VALUES(%s,%s,%s,%s,%s)",
                        (userID, 10, correct_count, current_category, current_date))
            conn.commit()
            print('Successfully inserted new game record into result table.')

        except  (Exception, psycopg2.Error) as error:
            if (conn):
                print("Failed to insert new game data into result table.", error)

        finally:
            if (conn):
                closeDB(conn,cur)


    # render all the questions and correct answers
    quiz_list.reverse()

    for item in quiz_list:
        answer_char = item['correct_answer']
        answer = item['answers'][answer_char]
        obj = {
            'question' : item['question'],
            'answer' : answer
        }
        QandA_list.append(obj)

    return render_template('finish.html', QandA_list = QandA_list, page=page)



#----------------------------- quiz request -----------------------------------

@app.route('/quiz_request')
def show_request():
    return render_template('quiz-request.html', category_list=category_list, options=options_list)

@app.route('/quiz_request', methods=['POST'])
def save_request():
    question = request.form.get('question')
    answer_a = request.form.get('answer_a')
    answer_b = request.form.get('answer_b')
    answer_c = request.form.get('answer_c')
    answer_d = request.form.get('answer_d')
    correct_answer = request.form.get('correct-answer')
    category = request.form.get('category')
    print(question, answer_a, answer_b, answer_c, answer_d, correct_answer, category)

    # insert the game data into result table
    conn, cur = connectToDB()
    try:
        cur.execute(f"INSERT INTO requests(question, answer_a, answer_b, answer_c, answer_d, correct_answer, category) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (question, answer_a, answer_b, answer_c, answer_d, correct_answer, category))
        conn.commit()
        print('Successfully inserted new request into requests table.')
        text = 'We received your request. Thank you for your idea!'
        return render_template('success-fail/success.html', text=text)

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to insert new request into requests table.", error)
            text = 'There was an error. Please try again.'
            return render_template('success-fail/fail.html', text=text)

    finally:
        if (conn):
            closeDB(conn,cur)



#----------------------------- admin -----------------------------------

@app.route('/admin')
def show_admin():
    init_quiz()
    userID = session.get('user_id')
    print(userID)
    # check whether the user is admin
    conn, cur = connectToDB()
    try:
        cur.execute(f"SELECT is_admin FROM users WHERE id='{userID}'")
        is_admin = cur.fetchone()[0]

        # if the password is correct, set user-id to session
        if is_admin:
            print('This user is admin.')

            return render_template('admin.html', category_list = category_list)

        else:
            print('This user is not admin.')
            return redirect('/')

    except TypeError as error:
        print('No such user.')

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to search the data.", error)

    finally:
        if (conn):
            closeDB(conn,cur)



@app.route('/admin_add_quiz', methods=['POST'])
def add_quiz():
    question = request.form.get('question')
    answer_a = request.form.get('answer_a')
    answer_b = request.form.get('answer_b')
    answer_c = request.form.get('answer_c')
    answer_d = request.form.get('answer_d')
    correct_answer = request.form.get('correct_answer')
    category = request.form.get('category')


    # send
    # url = 'http://localhost:3000/add-quiz'
    url = 'https://project2-node-express.herokuapp.com/add-quiz'
    data = {
        'question': question,
        'answer_a' : answer_a,
        'answer_b' : answer_b,
        'answer_c' : answer_c,
        'answer_d': answer_d,
        'correct_answer' : correct_answer,
        'category' : category
    }

    # res = requests.post(url).json() # list
    res = requests.post(url = url, data = data)

    if res.status_code == 200:
        print('Status code 200')
    else:
        print('Status code NOT 200')

    return redirect('/')




#----------------------------- user page -----------------------------------

@app.route('/account')
def show_account():
    init_quiz()
    userID = session.get('user_id')
    print(userID)
    return render_template('account.html')


#----------------------------- error handler -----------------------------------

@app.errorhandler(404)
def error404(error):
    return render_template('error/error404.html')

@app.errorhandler(500)
def error500(error):
    return render_template('error/error500.html')


@app.route('/error')
def errortest():
    return render_template('success-fail/success.html')


if __name__ == '__main__':
    app.run(debug=True)