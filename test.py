import sqlite3

sqlite = sqlite3.connect('identifier.sqlite')
cursor = sqlite.cursor()

query = "select * from accounts"
cursor.execute(query)

rows = cursor.fetchall()

print(rows)

for row in rows:
    print(row)
