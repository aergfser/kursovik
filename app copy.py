from flask import Flask, render_template, redirect, session, url_for, request
from pymongo import MongoClient
import os
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
# секретный ключ для хеширования данных сессии при авторизации

# Путь для сохранения изображений
path_to_save_images = os.path.join(app.root_path, 'static', 'imgs')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def with_connection(func):
    def wrapper(*args, **kwargs):
        client = MongoClient('mongodb://localhost:27017/')
        try:
            result = func(client['testdb'], *args, **kwargs)
        finally:
            client.close()
        return result
    return wrapper

@with_connection
def get_user(db, username):
    return db['users'].find_one({'username': username})

@with_connection
def get_all_data(db, collection_name='content'):
    collection = db[collection_name]
    cursor = collection.find()
    blocks_list = list(cursor)
    
    # Создаём результирующий словарь для группировки
    json_data = {}
    
    # Группируем данные по idblock
    for doc in blocks_list:
        
        # Группируем по idblock
        if doc['idblock'] not in json_data:
            json_data[doc['idblock']] = []
        json_data[doc['idblock']].append(doc)
        print(doc)

    return json_data

@with_connection
def put_data(db, variables = []):
    result = db['content'].update_one(
        {'_id': variables['_id']},
        {'$set': {
            'short_title': variables['short_title'],
            'title': variables['title'],
            "idblock": variables['idblock']
        }}
    )
    return result

@with_connection
def put_img(id, path):
    db['content'].update_one(
        {'_id': id},
        {'$set': {
            'img': path
        }}
    )

def authorization_is_succsess(username, password):
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    user = get_user(username)
    if user and user['password'] == hashed_password:
        # в случае успеха создаем сессию в которую записываем id пользователя
        session['user_id'] = str(user['_id'])
        # обратно: user = db['users'].find_one({'_id': ObjectId(session['user_id'])}) from bson import ObjectId
        return True
    return False

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# страница формы логина в админ панель  
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None # обнуляем переменную ошибок 
    if request.method == 'POST':
        username = request.form['username'] # обрабатываем запрос с нашей формы который имеет атрибут name="username"
        password = request.form['password'] # обрабатываем запрос с нашей формы который имеет атрибут name="password"
        
        # теперь проверяем если данные сходятся формы с данными БД
        if authorization_is_succsess(username, password):
            # делаем переадресацию пользователя на новую страницу -> в нашу адимнку
            return redirect(url_for('admin_panel'))
        else:
            error = 'Неправильное имя пользователя или пароль'

    return render_template('login_adm.html', error=error)

# страница админ панели
@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    json_data = get_all_data()
    return render_template('admin.html', json_data=json_data)


@app.route('/logout')
def logout():
    # Удаление данных пользователя из сессии
    session.clear()
    # Перенаправление на главную страницу или страницу входа
    return redirect(url_for('home'))

@app.route('/update_content', methods=['POST'])
def update_content():
    # Обработка загруженного файла
    if 'img' in request.files:
        file = request.files['img']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(path_to_save_images, filename)
            imgpath = "/static/imgs/"+filename
            file.save(save_path)
            put_img({request.form['id'], imgpath})



    variables = {
        '_id': request.form['id'],
        'short_title': request.form['short_title'],
        'title':  request.form['title'],
        'idblock': request.form['idblock']
    }

    res = put_data(variables)
    print (res)

    return redirect(url_for('admin_panel'))

@app.route('/')
def home():
    json_data = get_all_data()
    return render_template('lending.html', json_data=json_data)

if __name__ == '__main__':
    app.run(debug=True)