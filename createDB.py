from pymongo import MongoClient

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Создание базы данных (если она еще не существует)
db = client['testdb']

# Создание коллекции Content с индексами
content_collection = db['content']
content_collection.create_index('idblock', unique=False)
content_collection.create_index('timestampdata')

# Создание коллекции Users с уникальным индексом для username
users_collection = db['users']
users_collection.create_index('username', unique=True)




# Закрытие соединения
client.close()