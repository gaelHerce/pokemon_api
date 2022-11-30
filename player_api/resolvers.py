import sqlite3
import requests

DB_PATH = "database.db"
PORT_AUTH = 3001

def responseHttp(port, query):
    response = requests.post("http://auth:"+str(port)+"/graphql", json={'query':query})
    dataResponse = response.json()
    print(dataResponse)
    return dataResponse["data"]

# ----------------- GENERAL FUNCTIONS -----------------------------

def getPokemons(_token):
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

# ----------------- AUTH API REQUESTS -----------------------------

def getPlayerId(_token):
    query = "query{getId(_token:\""+_token+"\")}"
    response = responseHttp(PORT_AUTH, query)
    return response["getId"]

def playerExist(_token):
    query = "query{playerExist(_token:\""+_token+"\"){response,error}}"
    response = responseHttp(PORT_AUTH, query)
    return response["playerExist"]

def getUser(_token):
    query = "query{getUser(_token:\""+_token+"\"){user{id,userName},error}}"
    response = responseHttp(PORT_AUTH, query)
    return response["getUser"]

def getPlayers(_token):
    query = "query{getPlayers(_token:\""+_token+"\"){players{id,userName},error}}"
    response = responseHttp(PORT_AUTH, query)
    print(response)
    return response["getPlayers"]
    

# ----------------- PLAYER API RESOLVER  -----------------------------

def getPlayerList(_,info, _token):
    response = playerExist(_token)
    isPlayer, errorMessage = response["response"], response["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        players = getPlayers(_token)
        playersData, errorPlayersMessage = players["players"], players["error"]
        all_players = []
        if not errorPlayersMessage:
            for player in playersData:
                cursor.execute("""SELECT credits FROM players where id = ?""", (player["id"],))
                credits = cursor.fetchone()
                all_players.append({"id":player["id"], "userName":player["userName"], "credits": credits[0]})
            db.close()
            players = []
            for player in all_players:
                id, userName, credits = player["id"], player["userName"], player["credits"]
                players.append({"userName": userName, "credits": credits, "badges": getBadges(id)["badges"]})
            return {"players":players}
        else:
            return {"error": errorPlayersMessage}
    else:
        return {"error": errorMessage}

def getPersonalInformation(_,info,_token):
    response = playerExist(_token)
    isPlayer, errorMessage = response["response"], response["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        user = getUser(_token)
        userData, errorUserMessage = user["user"], user["error"]
        if not errorUserMessage:
            cursor.execute("""SELECT credits FROM players where id = ?""", (userData["id"],))        
            credits = cursor.fetchone()
            db.close()
            player = {"player":{"id": userData["id"], "userName": userData["userName"], "credits": credits[0], "badges": getBadges(userData["id"])["badges"], "pokemons": getPokemons(_token)["pokemons"]}}
            return player
        else:
            return {"error": errorUserMessage}
    else:
        return {"error": errorMessage}

def getConversation(_,info,_token, _otherPlayerId):
    isPlayer, errorMessage = playerExist(_token)
    if isPlayer:
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
    isPlayer, errorMessage = playerExist(_token)
    if isPlayer:
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

def addCredits(_,info,_token,_credits):
    isPlayer, errorMessage = playerExist(_token)
    if isPlayer:
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
    isPlayer, errorMessage = playerExist(_token)
    if isPlayer:
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
    isPlayer, errorMessage = playerExist(_token)
    if isPlayer:
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



