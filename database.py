import sqlite3
from flask import g

#Database helper functions

def connect_db():
    conn=sqlite3.connect('data.db')
    conn.row_factory=sqlite3.Row
    return conn

def get_db():
    if not hasattr(g,'sqlite_db'):
        g['sqlite_db']=connect_db()
    return g['sqlite_db']

#Database function to create tables in database
def create_table(conn):
    cur=conn.cursor()
    cur.executescript(""" 

    """)
    conn.close()