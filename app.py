
from unicodedata import category
import psycopg2
from flask import Flask, request, redirect, render_template, session, flash
import requests
import bcrypt
## ------------ other files --------------
from db_settings import DB_URL, connectToDB, closeDB, fetchData, fetchAll, insertData, updateData
from user import get_name, check_is_admin
from check_answer import check
## ------------ options --------------
import random
import json
import os



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
            cur.execute(f"SELECT id, hashed_password, is_admin FROM users WHERE email='{email}'")
            result = cur.fetchone()
            print(result)
            ## check whether the password is correct or not
            hashed_password = result[1]
            is_admin = result[2]
            is_valid = bcrypt.checkpw(req_password.encode(), hashed_password.encode())
            print(is_valid)
            # if the password is correct, set user-id to session
            if is_valid:
                found_id = result[0]
                print(f'User found. {found_id}')
                session['user_id'] = found_id
                session['is_admin'] = is_admin
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

# def init_quiz():
#     global quiz_list
#     global quiz_count
#     global correct_count
#     global QandA_list

#     quiz_list = []
#     QandA_list = []
#     quiz_count = 10
#     correct_count = 0

#--------------------------------


@app.route('/')
def index():
    global page
    page = 'top'
    # init_quiz()
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
    # init_quiz()
    return render_template('contact.html', page='contact')


@app.route('/about')
def showAbout():
    global page
    page = 'about'
    # init_quiz()
    return render_template('about.html', page=page)


#----------------------------- API -----------------------------------

current_category = ''


@app.route('/quiz')
def quiz_top():
    global page
    page = 'quiz'
    userID = session.get('user_id')
    if userID == None:
        return redirect('/')

    return render_template('quiz-start.html', page=page)


@app.route('/quiz/<categoryName>')
def quiz_main(categoryName):
    userID = session.get('user_id')
    if userID == None:
        return redirect('/')

    # insert a game into games table
    conn, cur = connectToDB()
    try:
        cur.execute(f"INSERT INTO games(player_id, correct_count, category, quiz_count) VALUES({userID}, 0, '{categoryName}', 10) RETURNING id;")
        conn.commit()
        game_id = cur.fetchone()[0]
        session['game_id'] = game_id
        print('Successfully inserted new game data into table.')
        print(f'DBから取得したgame idは{game_id}')

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to insert new game data", error)
            text = 'Sorry we could not get data, please try again.'
            return render_template('success-fail/fail.html', text=text)
    finally:
        if (conn):
            closeDB(conn,cur)

    return redirect('/progress')
    return 'ok'






#----------------------------Quiz control ------------------------------------

##------------ variable ---------------

options_list = ['a', 'b', 'c', 'd']

##-------------------------------------


@app.route('/progress')
def handle_quiz():
    global page
    page = 'quiz'

    userID = session.get('user_id')
    game_id = session.get('game_id')
    results = fetchData(f'SELECT category, quiz_count FROM games WHERE id={game_id}')
    categoryName = results[0]
    quiz_count = results[1]

    if userID == None:
        return redirect('/')

    print('quiz_count: ' + str(quiz_count))
    if quiz_count > 0:
    ##########################################################
        url = f'http://localhost:3000/quiz/{categoryName}'
        # url = f'https://project2-node-express.herokuapp.com/quiz/{categoryName}'
    ##########################################################

        foundQuiz = requests.get(url).json() # obj

        quizID = foundQuiz['_id']
        question = foundQuiz['question']
        answers = foundQuiz['answers']
        correct_answer = foundQuiz['correct_answer']
        answer_text = answers[correct_answer]

        next_quiz = {
            'id' : quizID,
            'question' : question,
            'answers' : answers,
        }
        insert = insertData(
            f"""
            INSERT INTO each_game(player_id, game_id, quiz_id, question, correct_answer, answer_text) VALUES
            ({userID},{game_id},'{quizID}','{question}','{correct_answer}','{answer_text}');
            """
            )

        if insert:
            is_admin = session.get('is_admin')
            return render_template('quiz-main.html', quiz = next_quiz, options_list = options_list, page=page, is_admin=is_admin)
        else:
            text = 'Sorry, we counlt not insert data.'
            return render_template('success-fail/fail.html', text=text)
    else:
        return redirect('/finish')





@app.route('/progress', methods=['POST'])
def check_answer():
    chosen_answer = request.form.get('chosen-answer')
    game_id = session.get('game_id')

    #get data from DB
    results = fetchData(f'SELECT correct_count, quiz_count FROM games Where id={game_id}')
    correct_count = results[0]
    quiz_count = results[1]
    current_quiz_answer = fetchData(f'SELECT answer_text FROM each_game WHERE id={game_id}')

    # check whether the chosen answer was correct
    checked_answer = check(current_quiz_answer, chosen_answer)
    if checked_answer == True:
        updateData(f'UPDATE games set correct_count = {correct_count +1} WHERE id={game_id}')
    updateData(f'UPDATE games set quiz_count = {quiz_count -1} WHERE id={game_id}')

    return redirect('/progress')




@app.route('/finish')
def show_answers():
    global page
    page = 'quiz'
    game_id = session.get('game_id')

    # get all questions and correct answers of the game
    quiz_list = fetchAll(f'SELECT question, answer_text FROM each_game WHERE game_id={game_id}')

    QandA_list = []
    for item in quiz_list:
        obj = {
            'question' : item[0],
            'answer' : item[1]
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
        cur.execute(f"INSERT INTO requests(question, answer_a, answer_b, answer_c, answer_d, correct_answer, category) VALUES(question, answer_a, answer_b, answer_c, answer_d, correct_answer, category);")
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
    # init_quiz()
    userID = session.get('user_id')
    print(userID)
    # check whether the user is admin
    is_admin = check_is_admin(userID)
    if is_admin == True:
        return render_template('admin/add.html', category_list = category_list)
    else:
        return redirect('/')



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
##########################################################
    url = 'http://localhost:3000/add-quiz'
    # url = 'https://project2-node-express.herokuapp.com/add-quiz'
##########################################################

    data = {
        'question': question,
        'answer_a' : answer_a,
        'answer_b' : answer_b,
        'answer_c' : answer_c,
        'answer_d': answer_d,
        'correct_answer' : correct_answer,
        'category' : category
    }

    res = requests.post(url = url, data = data)

    if res.status_code == 200:
        print('Status code 200')
    else:
        print('Status code NOT 200')

    return redirect('/')



#---------------- update ----------------------

@app.route('/update/<id>')
def show_update(id):
    # check whether the user is admin
    userID = session.get('user_id')
    is_admin = check_is_admin(userID)
    ## if admin == True, allow to access to the update page
    if is_admin == True:
        ##########################################################
        url = f'http://localhost:3000/get/{id}'
        # url = f'https://project2-node-express.herokuapp.com/get/{id}'
        ##########################################################
        res = requests.get(url).json() # list
        print(res)

        if res:
            data = {
                'id' : res['_id'],
                'question': res['question'],
                'answer_a' : res['answers']['a'],
                'answer_b' : res['answers']['b'],
                'answer_c' : res['answers']['c'],
                'answer_d': res['answers']['d'],
                'correct_answer' : res['correct_answer'],
                'category' : res['category']
            }
            print(data['id'])

            return render_template('admin/update.html', data=data, options=options_list, category_list=category_list)
        else:
            text = 'Unfortunately we could not get data.'
            return render_template('success-fail/fail.html', text=text)
    ## if the user is NOT admin, go back to the main page
    else:
        return redirect('/')



@app.route('/update', methods=['POST'])
def update_quiz():
    reqID = request.form.get('id')
    print(f'requested id is {reqID}')
    question = request.form.get('question')
    answer_a = request.form.get('answer_a')
    answer_b = request.form.get('answer_b')
    answer_c = request.form.get('answer_c')
    answer_d = request.form.get('answer_d')
    correct_answer = request.form.get('correct-answer')
    category = request.form.get('category')

    data = {
        'id' : reqID,
        'question': question,
        'answer_a' : answer_a,
        'answer_b' : answer_b,
        'answer_c' : answer_c,
        'answer_d': answer_d,
        'correct_answer' : correct_answer,
        'category' : category
    }

##########################################################
    url = f'http://localhost:3000/update'
    # url = f'https://project2-node-express.herokuapp.com/update'
##########################################################

    res = requests.put(url = url, data = data)

    if res.status_code == 200:
        print('Status code 200')
        text = 'Successfully updated quiz'
        return render_template('success-fail/success.html', text=text)
    else:
        text = 'Unfortunately we could not update data.'
        return render_template('success-fail/fail.html', text=text)




#-------------- delete --------------------------

@app.route('/delete/<id>')
def show_delete(id):
    reqID = id

    # check whether the user is admin
    userID = session.get('user_id')
    is_admin = check_is_admin(userID)
    ## if admin == True, allow to access to the delete page
    if is_admin == True:
        return render_template('admin/delete.html', id=reqID)
    else:
        return redirect('/')




@app.route('/delete', methods=['POST'])
def delete_quiz():
    reqID = request.form.get('id')
    print(reqID)
##########################################################
    url = f'http://localhost:3000/delete/{reqID}'
    # url = f'https://project2-node-express.herokuapp.com/delete/{reqID}'
##########################################################

    res = requests.delete(url = url)

    if res.status_code == 200:
        print('Status code 200')
        text = 'Successfully deleted quiz'
        return render_template('success-fail/success.html', text=text)
    else:
        text = 'Unfortunately we could not delete data.'
        return render_template('success-fail/fail.html', text=text)



#----------------------------- user page -----------------------------------

@app.route('/account')
def show_account():
    # init_quiz()
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