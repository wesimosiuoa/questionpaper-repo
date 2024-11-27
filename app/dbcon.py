import pymysql

# Function to connect to the database
def get_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='ntheng',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
