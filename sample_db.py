import sqlite3

conn = sqlite3.connect("demo.db")


cur = conn.cursor()

cur.execute("""
                CREATE TABLE Student(
                    ID INTEGER PRIMARY KEY,
                    NAME TEXT,
                    STD INTEGER
                )
                """)

cur.execute(
        "INSERT INTO Student(ID,NAME,STD) VALUES (?,?,?)",
        (1,"riyon",10)
    )

conn.commit()

conn.close()