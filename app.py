import datetime
from functools import wraps
from io import BytesIO
from pathlib import Path
from flask import Flask, json, jsonify, render_template, redirect, send_file, send_from_directory, session, url_for, request
from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import hashlib
from bson import json_util
from datetime import datetime
from docxtpl import DocxTemplate


static_dir = Path(__file__).parent / 'static'

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
            result = func(client['UnimaticTools'], *args, **kwargs)
        finally:
            client.close()
        return result
    return wrapper

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@with_connection
def get_tool_byId(db, id):
    doc = db['Tools'].find_one({'_id': ObjectId(id)})
    if not doc:
        raise ValueError('Деталь не найдена')
    return doc

@app.route('/api/images/<id_tool>')
def get_image(id_tool):
    try:
        doc = get_tool_byId(id_tool)
        image_path = Path('static/img') / (doc['image_name'])
        if not image_path.exists():
            return jsonify({'error': 'Файл не найден на диске'}), 404
        base_path = str(static_dir)
        return send_from_directory(
            base_path,
            'img/' + doc['image_name'],
            mimetype='image/jpeg'
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 405
    
@app.route('/api/upload-image/<tool_id>', methods=['POST'])
def upload_image(tool_id):
    # Используем полученный ID для сохранения файла
    try:

        # Получаем файл из запроса
        file = request.files.get('image')

        if not file:
            return jsonify({'error': 'Файл не предоставлен'}), 400
            
        # Проверяем тип файла
        if not file.filename.lower().endswith('.jpg'):
            return jsonify({'error': 'Только JPG формат разрешен'}), 400
        

        
        # Создаем путь для сохранения
        new_file_name = f'data_tool_{tool_id}.jpg'
        save_path = Path(static_dir) / 'img' / new_file_name
        
        data = { 'id': tool_id, 'image_name': new_file_name }
        print(data)
        update_detail(data)

        # Сохраняем файл
        file.save(save_path)
        
        return jsonify({
            'success': True,
            'message': 'Изображение успешно загружено'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# @app.route('/api/images/<id_tool>')
# def get_image(id_tool):
#     try:
#         doc = find_image_doc(id_tool)
#         return doc
#     except ValueError as e:
#         return jsonify({'error': str(e)}), 405

@with_connection
def get_user_by_username(db, username):
    return db['Users'].find_one({'username': username})

@with_connection
def get_users(db):
    return list(db.Users.find())

@with_connection
def get_user_by_id(db, id):
    return db['Users'].find_one({'_id': ObjectId(id)})


@with_connection
def get_detail_by_id(db, id):
    return db['Tools'].find_one({'_id': ObjectId(id)})


@with_connection
def get_deal_by_id(db, id):
    return db['Deals'].find_one({'_id': ObjectId(id)})

def get_field_name(param):
    """Извлекает название поля из параметра (например, 'TPN_min' -> 'TPN')"""
    return param.split('_')[0] if '_' in param else param


@with_connection
def get_details(db, *args, **kwargs):
    # Обработка параметра name с частичным поиском

    filter_query = {}
    base_filter = {
        "$and": [
            {"details": {"$exists": True}}
        ]
    }

    if 'name' in request.args:
        search_term = request.args.get('name')
        
        # Разбиваем запрос на отдельные слова
        words = search_term.lower().split()
        
        # Создаем условия поиска для каждого слова
        designation_filters = []
        for word in words:
            designation_filters.append({
                "designation": {
                    "$regex": f"(?i).*{word}.*",
                    "$options": "i"
                }
            })
        
        # Если есть несколько слов, объединяем их через $or
        if len(designation_filters) > 1:
            base_filter["$and"].append({"$or": designation_filters})
        else:
            base_filter["$and"].extend(designation_filters)
    
    # Остальной код остается без изменений...
    if any(param in request.args for param in request.args if param.endswith(('_min', '_max'))):
        for param in request.args:
            if param.endswith(('_min', '_max')):
                value = request.args.get(param)
                if value:
                    try:
                        float_value = float(value)
                        field = get_field_name(param)
                        
                        base_filter["$and"].append({
                            f"details.{field}": {"$exists": True}
                        })
                        
                        if param.endswith('_min'):
                            base_filter["$and"].append({
                                f"details.{field}": {"$gte": float_value}
                            })
                        elif param.endswith('_max'):
                            base_filter["$and"].append({
                                f"details.{field}": {"$lte": float_value}
                            })
                    except ValueError:
                        print(f"Ошибка: {value} не является числом")
    
    filter_query = base_filter if len(base_filter["$and"]) > 1 else {}
    return list(db.Tools.find(filter_query))

@with_connection
def get_managers(db, *args, **kwargs):
    managers = list(db.Users.find({"role": "manager"}))
    return managers

@with_connection
def get_deals(db, *args, **kwargs):
    print (request.args)
    final_filter = {}
        # Обработка параметра name с частичным поиском
    if 'deal_number' in request.args:
        deal_numbers = request.args.get('deal_number')
        # Разбиваем запрос на отдельные номера сделок
        number_list = deal_numbers.lower().split()
        
        # Создаем фильтр для поиска сделок по номерам
        deal_filters = []
        for num in number_list:
            try:
                deal_number = int(num)
                deal_filters.append({"number": deal_number})
            except ValueError:
                continue  # Пропускаем некорректные номера
            
        # Формируем финальный фильтр
        if len(deal_filters) > 1:
            final_filter["$and"] = [{"$or": deal_filters}]
        elif deal_filters:
            final_filter["$and"] = deal_filters
        
    # Получаем список сделок
    deals = list(db.Deals.find(final_filter))
    
    # Получаем FIO всех менеджеров в одном запросе
    manager_ids = [deal['manager'] for deal in deals]
    managers = db.Users.find({'_id': {'$in': manager_ids}})
    manager_fio = {str(m['_id']): m['fio'] for m in managers}
    
    # Получаем designation всех инструментов в одном запросе
    tool_ids = []
    for deal in deals:
        tool_ids.extend(deal['related_tools'])
    tools = db.Tools.find({'_id': {'$in': tool_ids}})
    tool_designations = {str(t['_id']): t['designation'] for t in tools}
    
    # Преобразуем каждый документ
    result = []
    for deal in deals:
        transformed_deal = {
            '_id': deal['_id'],
            'number': deal['number'],
            'date': deal['date'],
            'fio': manager_fio.get(str(deal['manager']), 'Не указано'),
            'related_tools': [
                tool_designations.get(str(tool_id), 'Не найден')
                for tool_id in deal['related_tools']
            ]
        }
        result.append(transformed_deal)
    
    return result

@with_connection
def add_detail(db, ids):
    new_tool_id = ObjectId(ids[1])
    deal_id = ObjectId(ids[0])

    deal = db.Deals.find_one(
        {"_id": deal_id, "related_tools": new_tool_id}
    )
    
    if deal:
        print("Инструмент уже есть в списке")
        return 100

    result = db.Deals.update_one(
        {"_id": deal_id},
        {"$push": {"related_tools": new_tool_id}}
    )
    # Проверяем результат
    if result.modified_count == 1:
        print("Инструмент успешно добавлен")
        return 1
    else:
        print("Ошибка при добавлении инструмента")

@with_connection
def update_detail(db, updated_data):
    id = ObjectId(updated_data['id'])
    if 'id' in updated_data:
        del updated_data['id']

    try:
        result = db.Tools.update_one(
            {'_id': id},
            {'$set': updated_data},
            upsert=True
        )
        if result.modified_count == 0:
            return {'success': False, 'message': 'Документ не найден'}
        return {'success': True, 'message': 'Данные обновлены'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
    
@with_connection
def update_deal(db, updated_data):

    try:
        id = ObjectId(updated_data['_id'])
        if '_id' in updated_data:
            del updated_data['_id']
        updated_data['manager'] = ObjectId(updated_data['manager'])
        for i, tool in enumerate(updated_data['related_tools']):
            updated_data['related_tools'][i] = ObjectId(tool)
        updated_data['date'] = datetime.strptime(updated_data['date'], "%Y-%m-%d")

        print(updated_data)

        result = db.Deals.update_one(
            {'_id': id},
            {'$set': updated_data},
            upsert=True
        )
        if result.modified_count == 0:
            return {'success': True, 'message': 'Документ не найден'}
        return {'success': True, 'message': 'Данные обновлены'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
    

def authorization_is_succsess(username, password):
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    user = get_user_by_username(username)
    if user and user['password'] == hashed_password:
        # в случае успеха создаем сессию в которую записываем id пользователя
        session['user_id'] = str(user['_id'])
        # обратно: user = db['users'].find_one({'_id': ObjectId(session['user_id'])}) from bson import ObjectId
        return True
    return False

@with_connection
def get_deal_number(db, id):
    deal = db.Deals.find_one({"_id": ObjectId(id)})
    return str(deal["number"]) if deal else None

@with_connection
def get_role(db, id):
    deal = db.Users.find_one({"_id": ObjectId(id)})
    return str(deal["role"]) if deal else None

@app.route('/api/get_actual_deal', methods=['GET'])
def get_actual_deal():
    try:
        deal_id = session.get('deal_id')
        deal_numder = get_deal_number(deal_id)
        return jsonify({
            'deal_id': deal_numder
        })
    except Exception as e:
        print(f"Ошибка при получении текущей сделки: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def get_selected_deal():
    if 'deal_id' not in session:
        return None
    return session['deal_id']

# страница формы логина в админ панель  
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(username, password)
        
        if authorization_is_succsess(username, password):
            print(1)
            return {'success': True, 'redirect': url_for('details')}
        else:
            error = 'Неправильное имя пользователя или пароль'
            
        return {'success': False, 'error': error}
    return render_template('login_adm.html', error=error)

@app.route('/logout')
def logout():
    # Удаление данных пользователя из сессии
    session.clear()
    # Перенаправление на главную страницу или страницу входа
    return redirect(url_for('admin_login'))

@app.route('/deals')
@require_login
def deals():
    role = get_role(session.get('user_id'))
    if (role == 'engineer'): 
        return render_template('noAccess.html')
    json_data = get_deals()
    return render_template('deals.html', items=json_data)

@app.route('/users')
@require_login
def users():
    role = get_role(session.get('user_id'))
    if (role != 'admin'): 
        return render_template('noAccess.html')
    json_data = get_users()
    print(json_data)
    return render_template('users.html', users=json_data)

@app.route('/api/deals')
def api_deals():
    try:
        json_data = get_deals()
        json_data = json.loads(json_util.dumps(json_data))
        if json_data is None:
            return jsonify({"error": "No deals found"}), 404
        return jsonify(json_data)
    except Exception as e:
        # Логирование ошибки для отладки
        print(f"Ошибка при получении сделок: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/set_deal/<id>', methods=['POST'])  # Добавляем methods=['POST']
def api_set_deal(id):
    try:
        session['deal_id'] = str(id)
        return jsonify({
            'success': True
        })
    except Exception as e:
        print(f"Ошибка при получении сделок: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/add_tool_to_deal', methods=['POST'])  # Добавляем methods=['POST']
def add_tool_to_deal():
    try:
        id_deal = session.get('deal_id')
        data = request.get_json()
        id_tool = data['id']
        print (id_deal)
        ids = [id_deal, id_tool]
        result = add_detail(ids)
        if result == 100:
            return jsonify({
            'success': False,
            'mes': "Инструмент уже есть в сделке"
            })
        return jsonify({
            'success': True
        })
    except Exception as e:
        print(f"Ошибка при получении сделок: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500







@app.route('/')
@app.route('/details')
@require_login
def details():
    json_data = get_details()
    print(json_data)
    return render_template('details.html', items=json_data)


@app.route('/index')
def index():
    items = [
        {
            "_id": "671e1664844277f06ee0bcca",
            "designation": "PICCO R-MFT60 6-4 L08",
            "details": {
                "DCONMS": "6.00",
                "DMIN": "4.00",
                "LU": "8.00",
                "TPN": "0.500",
                "TPX": "0.750",
                "TPIN": "32.00",
                "TPIX": "48.00",
                "t": "0.46",
                "a": "3.90",
                "CF": "0.06",
                "THL": "7.3",
                "OAL": "30.00",
                "PDY": "1.30",
                "RE": "0.10",
                "HAND": "R"
            }
        }
    ]
    return render_template('index.html', items=items)

                    
@app.route('/detail/<id>', methods=['GET', 'POST'])
def edit_document(id):
    try:
        if request.method == 'GET':
            result = get_detail_by_id(id)
            
            if result is None:
                return jsonify({
                    'success': False,
                    'message': 'Инструмент не найден'
                }), 404
                
            # Преобразуем ObjectId в строку для корректной сериализации JSON
            result['_id'] = str(result['_id'])
            
            return jsonify({
                'success': True,
                'data': result
            })
        elif request.method == 'POST':
            data = request.get_json()

            result = update_detail(data)

            if result.success == False:
                return jsonify({
                    'success': False,
                    'message': 'Инструмент не найден'
                }), 404
            elif result.success == True:
                return jsonify({
                    'success': False})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка при обработке запроса'
        }), 500

def convert_to_serializable(data):
    # Если данные являются словарём
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = convert_to_serializable(value)
        return result
    
    # Если значение является списком или кортежем
    elif isinstance(data, (list, tuple)):
        return [convert_to_serializable(item) for item in data]
    
    # Конвертируем ObjectId в строку
    elif isinstance(data, ObjectId):
        return str(data)
    
    # Для остальных типов возвращаем значение как есть
    else:
        return data

@app.route('/deal/<id>', methods=['GET', 'POST'])
def edit_deal(id):
    try:
        if request.method == 'GET':
            result = get_deal_by_id(id)
            if result is None:
                return jsonify({
                    'success': False,
                    'message': 'Инструмент не найден'
                }), 404
            
            # Преобразуем все ObjectId в строки
            result = convert_to_serializable(result)
            return jsonify({
                'success': True,
                'data': result
            })
        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Отсутствуют данные для обновления'
                }), 400
            
            result = update_deal(data)
            if result.success == False:
                return jsonify({
                    'success': False,
                    'message': 'Сделка не найдена'
                }), 404
            elif result.success == True:
                return jsonify({
                    'success': True,
                    'message': 'Сделка успешно обновлена'
                })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка при обработке запроса'
        }), 500

@app.route('/api/managers', methods=['GET'])
def api_managers():
    m = get_managers()
    json_data = json.loads(json_util.dumps(m))
    return json_data

@app.route('/api/user/<id>', methods=['GET'])
def api_user(id):
    m = get_user_by_id(id)
    json_data = json.loads(json_util.dumps(m))
    return json_data

@app.route('/api/tools/batch', methods=['POST'])
def get_tools_batch():
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({
                'success': False,
                'message': 'Необходимо предоставить список ID'
            }), 400
        
        # details = get_details() # get detail by id для каждого ids
        tools = [get_detail_by_id(id) for id in data['ids']]
        
        
        result = []
        for tool in tools:
            result.append({
                '_id': str(tool['_id']),
                'designation': tool['designation']
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка при обработке запроса'
        }), 500

@app.route('/download_word', methods=['POST'])
def download_word():
    try:
        data = request.get_json()
        id_tool = data.get('id_tool')
        id_user = session.get('user_id')

        print(id_tool)
        user = get_user_by_id(id_user)
        tool = get_tool_byId(id_tool)
        tool['fio'] = user['fio']
        
        tpl = DocxTemplate('template.docx')
        tpl.render(tool)
        
        # Сохраняем в память
        doc_buffer = BytesIO()
        tpl.save(doc_buffer)
        doc_buffer.seek(0)
        
        # Отправляем файл клиенту
        return send_file(
            doc_buffer,
            as_attachment=True,
            download_name='document.doc',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        print(str(e))
        return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
