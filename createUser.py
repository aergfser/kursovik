from pymongo import MongoClient
import hashlib

def create_user(username, password, role, fio):
    # Хеширование пароля
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Подключение к MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    
    # Получение базы данных и коллекции
    db = client['UnimanicTools']
    users_collection = db['Users']

    try:
        # Добавление нового пользователя
        result = users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'fio' : fio,
            'role' : role

        })
        
        # Проверка успешности операции
        if result.acknowledged:
            print(f"Пользователь {username} успешно создан")
        else:
            print("Ошибка при создании пользователя")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        # Закрытие соединения
        client.close()

# Пример использования
create_user('ivan_admin', '123', 'admin', 'Ваня Иванов')
create_user('ivan_manager', '123', 'manager', 'Ваня Долго')
create_user('ivan_engeneer', '123', 'engeneer', 'Ваня Быстро')


