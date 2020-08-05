import sqlite3
from flask import g

#Database helper functions

def connect_db():
    conn=sqlite3.connect('data.db')
    conn.row_factory=sqlite3.Row
    create_table(conn)
    return conn

def get_db():
    if not hasattr(g,'sqlite_db'):
        g.sqlite_db=connect_db()
    return g.sqlite_db

#Database function to create tables in database
def create_table(conn):
    cur=conn.cursor()
    cur.executescript(""" 
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
          name TEXT NOT NULL,
          password TEXT NOT NULL,
          expert BOOLEAN NOT NULL,
          admin BOOLEAN NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions(
          id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
          question_text TEXT NOT NULL,
          answer_text TEXT,
          user_id INTEGER NOT NULL,
          expert_id INTEGER NOT NULL
        )
    """)