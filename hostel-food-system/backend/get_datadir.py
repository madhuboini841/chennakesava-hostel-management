import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='')
cursor = conn.cursor()
cursor.execute("SHOW VARIABLES LIKE 'datadir';")
print(cursor.fetchone()[1])
