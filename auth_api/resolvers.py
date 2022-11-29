import sqlite3
from uuid import uuid4

DB_PATH = "db/database.db"

CONNECTED = False

def createAccount(_,info,_role,_userName,_pwd):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    try:
        cursor.execute("""INSERT INTO users (username, pwd, role) VALUES (?,?,?);""", (_userName, _pwd, _role))
        if _role == 'player':
            newUserId = str(cursor.lastrowid)
            cursor.execute("""INSERT INTO players (id) VALUES (?);""", (newUserId))
    except sqlite3.IntegrityError:
        return {"error": "userName already exists"}
    db.commit()
    db.close()
    return {"success": "Account successfuly created"}

def connect(_,info,_userName, _pwd):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT id, token FROM users WHERE username = ? AND pwd = ?""", (_userName, _pwd))
    id, token = cursor.fetchone()
    if id:
        if token:
            return {"token": token, "error": "Already connected"}       
        else:
            token = str(uuid4().int)
            cursor.execute("""UPDATE users SET token = ? WHERE id = ?""", (token, id))
            db.commit()
            db.close()
            return {"token": token}
    else:
        db.close()
        return {"error": "Wrong username or password"}

def disconnect(_,info,_token):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT id FROM users WHERE token = ?""",(_token,))
    id = cursor.fetchone()
    if id:
        cursor.execute("""UPDATE users SET token = NULL WHERE token = ?""", (_token,))
        db.commit()
        db.close()
        return {"success": "Disconnected with success"}
    else:
        return {"error": "Unknown token"}

def getId(_,info,_token):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT id FROM users WHERE token = ?""", (_token,))
    id = cursor.fetchone()
    return id[0]

def isConnected(_,info,_token):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT id FROM users WHERE token = ?""", (_token,))
    return (cursor.fetchone() is not None)