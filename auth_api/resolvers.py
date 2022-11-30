import sqlite3
from uuid import uuid4

DB_PATH = "database.db"

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

def getUser(_, info, _token):
    if (isConnected(None, None,_token)):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT id, username, pwd, role FROM users WHERE token = ?""",(_token,))
        user = cursor.fetchone()
        return {"user":{"id": user[0], "userName":user[1], "pwd":user[2], "role":user[3]}}
    else:
        return {"error":"you're not logged in"}

def getPlayers(_, info, _token):
    if (isConnected(None, None,_token)):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT id, username, pwd, role FROM users WHERE role = \"player\"""")
        users = cursor.fetchall()
        players = []
        for user in users:
            players.append({"id": user[0], "userName":user[1], "pwd":user[2], "role":user[3]})
        return {"players": players}
    else:
        return {"error":"you're not logged in"}

def changePwd(_, info, _token, _newPwd):
    if (isConnected(None, None,_token)):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""UPDATE users SET pwd = ? WHERE token = ?""",(_newPwd, _token))
        db.commit()
        db.close()
        return {"success":"password changed successfully"}
    else:
        return {"error":"you're not logged in"}

def changeUserName(_, info, _token, _newUserName):
    if (isConnected(None, None,_token)):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""UPDATE users SET username = ? WHERE token = ?""",(_newUserName, _token))
        db.commit()
        db.close()
        return {"success":"username changed successfully"}
    else:
        return {"error":"you're not logged in"}

def playerExist(_, info, _token):
    print(isConnected(None, info, _token))
    print(_token)
    if(isConnected(None, info, _token)):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT role FROM users WHERE token = ?""",(_token,))
        role = cursor.fetchone()[0]
        if role == "player":
            return {"response":True}
        else:
            return {"response":False}
    else:
        print("HERE")
        return {"error": "you're not logged in"}