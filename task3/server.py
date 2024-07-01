import mysql.connector

DATABASE_CONFIG = {
    'user': 'u67349',
    'password': '2433632',
    'host': 'localhost',
    'database': 'u67349'
}

if __name__ == '__main__':
    connection = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = connection.cursor

    cursor.execute('SELECT * FROM users')