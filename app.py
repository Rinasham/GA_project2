
from distutils import core
from unicodedata import category
import psycopg2
from flask import Flask, request, redirect, render_template, session, flash
import requests
import bcrypt
## ------------ other files --------------
from db_settings import DB_URL, connectToDB, closeDB, deleteData, fetchData, fetchAll, insertData, updateData, deletefrom_each_game
from user import get_user, check_is_admin
from check_answer import check
## ------------ options --------------
import random
import math
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
    return render_template('registration/signup.html')

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
        cur.execute("INSERT INTO users(email, name, hashed_password,is_admin) VALUES(%s,%s,%s,%s)", (req_email, req_name, hashed_req_password, False))
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
    return render_template('registration/login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    req_password = request.form.get('password1')

    # flash for empty input
    if email =='' or req_password =='':
        flash('Please enter your email and password.','ng')
        return redirect('/login')
    else:
        conn, cur = connectToDB()
        try:
            cur.execute(f"SELECT id, hashed_password, is_admin FROM users WHERE email='{email}'")
            result = cur.fetchone()
            ## check whether the password is correct or not
            hashed_password = result[1]
            is_admin = result[2]
            is_valid = bcrypt.checkpw(req_password.encode(), hashed_password.encode())
            # if the password is correct, set user-id to session
            if is_valid:
                found_id = result[0]
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



#------------------------------- main --------------------------------------


@app.route('/')
def index():
    global page
    page = 'top'
    # init_quiz()
    userId = session.get('user_id')
    if userId == None:
        return render_template('home.html', user=None)
    userID, userName = get_user(userId)

    # game_id = session.get('game_id')
    # deletefrom_each_game(game_id)

    return render_template('home.html', user=userName, userID=userID, page=page)



@app.route('/contact')
def showContact():
    global page
    page = 'contact'
    userId = session.get('user_id')
    userID, userName = get_user(userId)
    # game_id = session.get('game_id')
    # deletefrom_each_game(game_id)
    return render_template('contact.html', user=userName, userID=userID, page='contact')


@app.route('/contact', methods=['POST'])
def saveContact():
    name = request.form.get('userName')
    email = request.form.get('userEmail')
    phone_num = request.form.get('userTel')
    message = request.form.get('userMessage')
    # remove white space from the message text
    message = message.strip()
    userID = session.get('user_id')

    # if any of the required column is empty, prompt the user to fill it in
    if name =='' or email =='' or message =='':
        userID, userName = get_user(userID)
        return render_template('contact.html', name=name, email=email, phone_num=phone_num, message=message, user=userName, userID=userID)
    else:
        if userID != None:
            if phone_num != '':
                insert = insertData(f"INSERT INTO contacts(user_id, name, email, phone_number, message) VALUES({userID},'{name}','{email}','{phone_num}','{message}');")
            else:
                insert = insertData(f"INSERT INTO contacts(user_id, name, email, message) VALUES({userID}, '{name}', '{email}', '{message}');")
            if insert:
                text = 'We received your message. Thank you!'
                return render_template('success-fail/success.html', text=text)
            else:
                text = 'Sorry, we could not save data. Please try again.'
                return render_template('success-fail/fail.html', text=text)
        else:
            redirect('/')



@app.route('/about')
def showAbout():
    global page
    page = 'about'
    userId = session.get('user_id')
    userID, userName = get_user(userId)
    return render_template('about.html', user=userName, userID=userID, page=page)


#----------------------------- API -----------------------------------

current_category = ''


@app.route('/quiz')
def quiz_top():
    global page
    page = 'quiz'
    userID = session.get('user_id')
    if userID == None:
        return redirect('/login')

    game_id = session.get('game_id')
    deletefrom_each_game(game_id)

    userID, userName = get_user(userID)
    return render_template('quiz-start.html', page=page, user=userName, userID=userID)


@app.route('/quiz/<categoryName>')
def quiz_main(categoryName):
    userID = session.get('user_id')
    if userID == None:
        return redirect('/')

    # insert a game into games table
    conn, cur = connectToDB()
    try:
    ##########################################################
        # url = f'http://localhost:3000/quiz/{categoryName}'
        url = f'https://project2-node-express.herokuapp.com/quiz/{categoryName}'
    ##########################################################

        foundQuiz = requests.get(url).json() # obj -> list
        list = random.sample(foundQuiz, 10)
        quizzes_list = []
        for index, item in enumerate(list):
            quiz = []
            quizID = item['_id']
            question = item['question']
            answers = item['answers']
            answer_a = answers['a']
            answer_b = answers['b']
            answer_c = answers['c']
            answer_d = answers['d']
            correct_answer = item['correct_answer']
            answer_text = answers[correct_answer]
            quiz.append(quizID)
            quiz.append(question)
            quiz.append(answer_a)
            quiz.append(answer_b)
            quiz.append(answer_c)
            quiz.append(answer_d)
            quiz.append(correct_answer)
            quiz.append(answer_text)
            quiz.append(index +1)
            quizzes_list.append(quiz)

        cur.execute(f"INSERT INTO games(player_id, correct_count, category) VALUES({userID}, 0, '{categoryName}') RETURNING id;")
        conn.commit()
        game_id = cur.fetchone()[0]
        session['game_id'] = game_id

#-------------- insert 10 quizzes ------------------
        conn, cur = connectToDB()
        try:
            for item in quizzes_list:
                cur.execute(f"""
                            INSERT INTO each_game(player_id, game_id, quiz_id, question,answer_a,answer_b,answer_c,answer_d, correct_answer, answer_text, quiz_count) VALUES
                            ({userID},{game_id},'{item[0]}','{item[1]}','{item[2]}','{item[3]}','{item[4]}','{item[5]}','{item[6]}','{item[7]}', '{item[8]}')
                            """);
            conn.commit()
            print('Successfully inserted data.')
            session['count'] = 1
        except  (Exception, psycopg2.Error) as error:
            if (conn):
                print("Failed to insert data.", error)
            text = 'Sorry we could not get data, please try again.'
            return render_template('success-fail/fail.html', text=text)
        finally:
            if (conn):
                closeDB(conn,cur)

    except  (Exception, psycopg2.Error) as error:
        if (conn):
            print("Failed to insert new game data", error)
            text = 'Sorry we could not get data, please try again.'
            return render_template('success-fail/fail.html', text=text)
    finally:
        if (conn):
            closeDB(conn,cur)

    return redirect('/progress')







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
    count = session.get('count')

    if userID == None:
        return redirect('/')
    userID, userName = get_user(userID)

    if count < 11:
        print(f'game_idは{game_id}, quiz_countは{count}')
        get_quiz = fetchData(f"SELECT * FROM each_game WHERE game_id='{game_id}' and quiz_count={count}")

        next_quiz = {
            'id' : get_quiz[3],
            'question' : get_quiz[4],
            'answers' : {
                'a': get_quiz[8],
                'b': get_quiz[9],
                'c': get_quiz[10],
                'd': get_quiz[11],
                }
        }
        correct_answer = get_quiz[5]

        is_admin = session.get('is_admin')
        return render_template('quiz-main.html', quiz = next_quiz, correct_answer=correct_answer, options_list = options_list, page=page, is_admin=is_admin, user=userName, userID=userID)
    else:
        return redirect('/finish')





@app.route('/progress', methods=['POST'])
def check_answer():
    chosen_answer = request.form.get('chosen-answer')
    game_id = session.get('game_id')
    count = session.get('count')

    #get data from DB
    correct_count = fetchData(f'SELECT correct_count FROM games Where id={game_id}')[0]

    current_quiz_answer = fetchData(f'SELECT correct_answer FROM each_game WHERE game_id={game_id} AND quiz_count={count}')[0]
    print(f"chosen_answer : {chosen_answer},  correct_answer:  {current_quiz_answer}")
    # check whether the chosen answer was correct
    checked_answer = check(current_quiz_answer, chosen_answer)

    if checked_answer == True:
        updateData(f'UPDATE games set correct_count = {correct_count +1} WHERE id={game_id}')
    session['count'] += 1
    correct_count = fetchData(f'SELECT correct_count FROM games Where id={game_id}')[0]


    return redirect('/progress')




@app.route('/finish')
def show_answers():
    global page
    page = 'quiz'
    game_id = session.get('game_id')
    userId = session.get('user_id')
    userID, userName = get_user(userId)

    # get all questions and correct answers of the game
    quiz_list = fetchAll(f'SELECT question, answer_text FROM each_game WHERE game_id={game_id}')

    QandA_list = []
    for item in quiz_list:
        obj = {
            'question' : item[0],
            'answer' : item[1]
        }
        QandA_list.append(obj)
    # insert record of the current game into histories table
    data = fetchData(f"SELECT correct_count, category FROM games WHERE id={game_id}")
    correct_count = data[0]
    category = data[1]

    insert = insertData(f"""
                        INSERT INTO histories(player_id, correct_count, quiz_count, category) VALUES
                        ({userID}, {correct_count}, 10, '{category}')
                        """)
    if insert == False:
        text = 'Sorry it seems like there was an error.'
        return render_template('success-fail/fail.html', text=text)
    # # delete data from each_game table
    # deletefrom_each_game(game_id)

    return render_template('finish.html', QandA_list = QandA_list, page=page, user=userName, userID=userID)


#----------------------------- quiz request -----------------------------------

@app.route('/quiz_request')
def show_request():
    userId = session.get('user_id')
    userID, userName = get_user(userId)
    return render_template('quiz-request.html', category_list=category_list, options=options_list, user=userName, userID=userID)



@app.route('/quiz_request', methods=['POST'])
def save_request():
    question = request.form.get('question')
    answer_a = request.form.get('answer_a')
    answer_b = request.form.get('answer_b')
    answer_c = request.form.get('answer_c')
    answer_d = request.form.get('answer_d')
    correct_answer = request.form.get('correct-answer')
    category = request.form.get('category')


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
    userID = session.get('user_id')

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
    # url = 'http://localhost:3000/add-quiz'
    url = 'https://project2-node-express.herokuapp.com/add-quiz'
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
        # url = f'http://localhost:3000/get/{id}'
        url = f'https://project2-node-express.herokuapp.com/get/{id}'
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
    # url = f'http://localhost:3000/update'
    url = f'https://project2-node-express.herokuapp.com/update'
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

##########################################################
    # url = f'http://localhost:3000/delete/{reqID}'
    url = f'https://project2-node-express.herokuapp.com/delete/{reqID}'
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
    userid = session.get('user_id')
    if userid == None:
        return redirect('/')
    user = fetchData(f"SELECT id, email, name FROM users WHERE id={userid}")
    userID = user[0]
    email = user[1]
    name = user[2]
    # get the number of quizzes the user has played
    game_counts_byCategory = fetchAll(f"SELECT category, sum(quiz_count) FROM histories WHERE player_id={userID} GROUP BY category;")
    correct_counts_byGame = fetchAll(f"SELECT category, sum(correct_count) FROM histories WHERE player_id={userID} GROUP BY category;")
    all_game_count = fetchData(f"SELECT count(player_id={userID} OR NULL) FROM histories WHERE player_id={userID};")[0]

    all_game_count *= 10

    print(correct_counts_byGame)
    # dictionary for percentages of each category played
    game_percentage_list = []  #[{'nane' : category, 'percentage' : percentage}, {}...]
    # dictionary for percentages of correct quizzes at each category
    correct_percentage_list = []
    item = {}
    for index, category in enumerate(game_counts_byCategory):
        percentage = math.floor((category[1] / all_game_count) * 100)
        if category[0] == 'css' or category[0] == 'html':
            item = {
                'name' : category[0].upper(),
                'percentage' : percentage
            }
        else:
            item = {
                'name' : category[0].capitalize(),
                'percentage' : percentage
            }
        game_percentage_list.append(item)

        correct_per = math.floor((correct_counts_byGame[index][1] / category[1]) * 100)
        if category[0] == 'css' or category[0] == 'html':
            item = {
                'name' : category[0].upper(),
                'percentage' : correct_per
            }
        else:
            item = {
                'name' : category[0].capitalize(),
                'percentage' : correct_per
            }
        correct_percentage_list.append(item)
    print(correct_percentage_list)
    return render_template('account.html', user=name, userID=userID, email=email, games_list=game_percentage_list, correct_list=correct_percentage_list)




@app.route('/account', methods=['POST'])
def edit_profile():
    userID = session.get('user_id')
    name = request.form.get('name')
    email = request.form.get('email')
    current_password =request.form.get('current_pass')
    new_password =request.form.get('new_pass')

    if name =='' or email == '' or current_password =='' or new_password == '':
        flash('Please fill in all the fields.','ng')
        return redirect('/account')


    # check the current password is correct
    hashed_password = fetchData(f"SELECT hashed_password FROM users WHERE id={userID}")[0]
    is_valid = bcrypt.checkpw(current_password.encode(), hashed_password.encode())
    if is_valid:
        hashed_new_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        update = updateData(f"UPDATE users set hashed_password='{hashed_new_password}' WHERE id={userID}")
        if update == True:
            text = 'Successfully updated your data.'
            return render_template('success-fail/success.html', text=text)
        else:
            text = 'We could not update your data. Please try again.'
            return render_template('success-fail/fail.html', text=text)
    else:
        text = 'We could not update your data. Please try again.'
        return render_template('success-fail/fail.html', text=text)

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