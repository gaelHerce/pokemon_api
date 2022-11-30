import sqlite3
import requests

DB_PATH = "player_api/db/database.db"
PORT_AUTH = 3001

def responseHttp(port, query):
    response = requests.post("http://0.0.0.0:"+str(port)+"/graphql", json={'query':query})
    dataResponse = response.json()
    return dataResponse["data"]

# ----------------- AUTH API REQUESTS -----------------------------

def getPlayerId(_token):
    query = "query{getId(_token:\""+_token+"\")}"
    response = responseHttp(PORT_AUTH, query)
    return response["getId"]

def isConnected(_token):
    query = "query{isConnected(_token:\""+_token+"\")}"
    response = responseHttp(PORT_AUTH, query)
    return response["isConnected"]

# ----------------- GENERAL FUNCTION  -----------------------------

def isPlayer(_token):
    if isConnected(_token):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT players.id FROM players INNER JOIN users ON players.id=users.id WHERE users.token = ?""", (_token,))
        if cursor.fetchone() is None:
            db.close()
            return (False, "Unknown Player")
        else:
            db.close()
            return (True, "")
    else:
        return (False, "Not connected")

# ----------------- PLAYER API RESOLVER  -----------------------------

def playerExist(_,info,_token):
    playerExist, errorMessage = isPlayer(_token)
    return {"response": playerExist, "error": errorMessage}

def getPlayerList(_,info, _token):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT players.id, users.username, players.credits FROM players INNER JOIN users ON players.id=users.id""")
        all_players = cursor.fetchall()
        print(all_players)
        db.close()
        players = []
        for player in all_players:
            id, userName, credits = player
            players.append({"userName": userName, "credits": credits, "badges": getBadges(id)["badges"]})
        return {"players":players}
    else:
        return {"error": errorMessage}

def getPersonalInformation(_,info,_token):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT players.id, users.username, players.credits FROM players INNER JOIN users ON players.id=users.id WHERE users.token = ?""", (_token,))
        player = cursor.fetchone()
        db.close()
        id, userName, credits = player
        player = {"player":{"id": id, "userName": userName, "credits": credits, "badges": getBadges(id)["badges"], "pokemons": getPokemons(_token)["pokemons"]}}
        return player
    else:
        return {"error": errorMessage}

def getPokemonInfo(_,info, _token, _pokemonId):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT pokemon_owners.id, pokemons.name, pokemons.type, pokemons.att, pokemons.pv FROM pokemons INNER JOIN pokemon_owners ON pokemons.id = pokemon_owners.pokemon WHERE pokemon_owners.id = ?""", (_pokemonId,))
        pokemon = cursor.fetchone()
        return {"id": pokemon[0], "name": pokemon[1], "type": pokemon[2], "pv": pokemon[3], "att": pokemon[4]}
    else:
        return {"error": errorMessage}

def getPokemons(_token):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT pokemons.id, pokemons.name, pokemons.type, pokemons.att, pokemons.pv FROM pokemons INNER JOIN pokemon_owners ON pokemons.id = pokemon_owners.pokemon WHERE pokemon_owners.owner = ?""", (playerId,))
        pokemonOwned = cursor.fetchall()
        db.close()
        pokemonsData = []
        for pokemon in pokemonOwned:
            id, name, type, att, pv = pokemon
            pokemonsData.append({"id": id, "name": name, "type": type, "att": att, "pv": pv})
        return {"pokemons":pokemonsData}
    else:
        return {"error": errorMessage}

def getBadges(_id):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT badges.id, badges.description FROM badges INNER JOIN badges_owners ON badges.id = badges_owners.badge WHERE badges_owners.owner = ?""", (_id,))
    badgesOwned = cursor.fetchall()
    db.close()
    badgesData = []
    for badge in badgesOwned:
        id, description = badge
        badgesData.append({"id": id, "description": description})
    return {"badges": badgesData}

def getConversation(_,info,_token, _otherPlayerId):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT id FROM players WHERE id = ?""",(_otherPlayerId,))
        otherPlayerExist = cursor.fetchone()
        if otherPlayerExist:
            playerId = getPlayerId(_token)
            db = sqlite3.connect(DB_PATH)
            cursor = db.cursor()
            cursor.execute("""SELECT sender, receiver, message FROM messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)""", (playerId,_otherPlayerId,_otherPlayerId,playerId))
            messagesWithPlayer = cursor.fetchall()
            messagesData = []
            for message in messagesWithPlayer:
                sender, receiver, text = message
                messagesData.append({"sender": sender, "receiver": receiver, "text": text})
            db.close()
            return {"messages": messagesData}
        return {"error": "Unknown other player"} 
    else:
        return {"error": errorMessage}   

def getReceivedMessages(_,info,_token):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT sender, receiver, message FROM messages WHERE receiver = ?""", (playerId,))
        senders = cursor.fetchall()
        messagesData = []
        for message in senders:
            sender, receiver, text = message
            messagesData.append({"sender": sender, "receiver": receiver, "text": text})
        db.close()
        return {"messages": messagesData}
    else:
        return {"error": errorMessage}   

def getInvitations(_,info,_token):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT sender, receiver, id FROM matchs WHERE status = 0 AND (receiver = ? OR ((receiver is NULL) AND sender != ?)) ORDER BY receiver DESC""", (playerId,playerId))
        allInvitations = cursor.fetchall()
        invitationsData = []
        for invitation in allInvitations:
            sender, receiver, id = invitation
            invitationsData.append({"sender": sender, "receiver": receiver, "matchId": id})
        return {"invitations": invitationsData}
    else:
        return {"error": errorMessage} 


def changeUserName(_,info,_token,_newName):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""UPDATE users SET username = ? WHERE token = ?""", (_newName, _token))
        db.commit()
        db.close()
        return {"success": "Username successfuly changed"}
    else:
        return {"error": errorMessage}     

def changePwd(_,info,_token,_newPwd):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""UPDATE users SET pwd = ? WHERE token = ?""", (_newPwd, _token))
        db.commit()
        db.close()
        return {"success": "Password successfuly changed"}
    else:
        return {"error": errorMessage}

def addCredits(_,info,_token,_credits):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT credits FROM players WHERE id = ?""",(playerId,))
        currentCredits = cursor.fetchone()
        _credits += currentCredits[0]
        cursor.execute("""UPDATE players SET credits = ? WHERE id = ?""", (_credits, playerId))
        db.commit()
        db.close()
        return {"success": "Credits successfuly added"}
    else:
        return {"error": errorMessage}
    
def addPokemon(_,info,_token, _pokemonId):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT id FROM pokemons WHERE id = ?""", (_pokemonId,))
        pokemon = cursor.fetchone()
        if pokemon:
            pokemonId = pokemon[0]
            cursor.execute("""SELECT pokemon, owner FROM pokemon_owners WHERE pokemon = ? AND owner = ?""", (pokemonId, playerId))
            alreadyOwn = cursor.fetchone()
            if alreadyOwn:
                db.close()
                return {"error":"Player already own this pokemon"}
            else:
                cursor.execute("""INSERT INTO pokemon_owners (pokemon, owner) VALUES (?, ?)""",(pokemonId, playerId))
                db.commit()
                db.close()
                return {"success": "Pokemon successfuly added in your team"}
        else:
            db.close()
            return {"error": "Unknown pokemon"}
    else:
        return {"error": errorMessage}

def sendMessage(_,info,_token,_message,_receiverId):
    playerExist, errorMessage = isPlayer(_token)
    if playerExist:
        playerId = getPlayerId(_token)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT id FROM players WHERE id = ?""",(_receiverId,))
        receiverExist = cursor.fetchone()
        if receiverExist:
            cursor.execute("""INSERT INTO messages (sender, receiver, message) VALUES (?,?,?)""",(playerId, _receiverId, _message))
            db.commit()
            db.close()
            return {"success": "Message successfuly sent"}  
        else:
            return {"error": "Unknown receiver"}
    else:
        return {"error": errorMessage}



