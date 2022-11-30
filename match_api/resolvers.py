import sqlite3
import requests

DB_PATH = "db/database.db"
PORT_AUTH = 3001
PORT_PLAYER = 3003

def responseHttp(port, query):
    response = requests.post("http://0.0.0.0:"+str(port)+"/graphql", json={'query':query})
    dataResponse = response.json()
    return dataResponse["data"]

# ----------------- GENERAL FUNCTION  -----------------------------

def isMyPokemon(_token, _pokemonId):
    response = getPokemons(_token)
    pokemons, errorMessage = response["player"]["pokemons"], response["error"]
    if not errorMessage:
        for pokemon in pokemons:
            if pokemon["id"] == _pokemonId:
                return (True, "")
        return (False, "Pokemon not in your team")
    else:
        return (False, errorMessage)

def isPokemonOut(rounds, _pokemonId, creatorOrReceiver):
    for round in rounds:
        if creatorOrReceiver == 0:
            if round["winner"] == 1 and round["creatorPokemon"] == _pokemonId:
                return True
        else:
            if round["winner"] == 0 and round["receiverPokemon"] == _pokemonId:
                return True     
    return False 

def needNewRound(rounds):
    if rounds != []:
        currentRound = rounds[-1]
        print(currentRound)
        if currentRound["winner"] in [0,1]:
            return True
        else:
            return False
    else:
        return True

def opponentHasChosenHisPokemon(rounds, creatorOrReceiver):
    currentRound = rounds[-1]
    if creatorOrReceiver == 0:
        if currentRound["receiverPokemon"]:
            return True
    else:
        if currentRound["creatorPokemon"]:
            return True
    return False

def createNewRound(_matchId, _pokemonId, creatorOrReceiver, newRoundIndex):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    if newRoundIndex == 0:
        cursor.execute("""UPDATE matchs SET status = 2 WHERE id = ?""",(_matchId,))
    if creatorOrReceiver == 0:
        cursor.execute("""INSERT INTO rounds(matchId, creatorPokemon, roundIndex) VALUES (?,?,?)""",(_matchId, _pokemonId, newRoundIndex)) #on crée un nouveau round
    else:
        cursor.execute("""INSERT INTO rounds(matchId, receiverPokemon, roundIndex) VALUES (?,?,?)""",(_matchId, _pokemonId, newRoundIndex)) #on crée un nouveau round
    db.commit()
    db.close()

def addPokemonToRound(matchId, round, pokemonId, creatorOrReceiver):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    if creatorOrReceiver == 0:
        cursor.execute("""UPDATE rounds SET creatorPokemon = ? WHERE matchId = ? and roundIndex = ?""",(pokemonId, matchId, round))
    else:
        cursor.execute("""UPDATE rounds SET receiverPokemon = ? WHERE matchId = ? and roundIndex = ?""",(pokemonId, matchId, round))
    db.commit()
    db.close()

def getPokemonInfo(_pokemonId):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT * FROM pokemons WHERE id = ?""", (_pokemonId,))
    pokemon = cursor.fetchone()
    db.close()
    if pokemon:
        id, name, type, att, pv = pokemon
        return {"id": id, "name": name, "type": type, "pv": pv, "att": att}
    else:
        return None

def decideWinner(senderPokemon, receiverPokemon):
    if senderPokemon[0]/receiverPokemon[1] > receiverPokemon[0]/senderPokemon[1]: #sender won
        return 0
    else: # receiver won
         return 1

def setRoundWinner(pokemon1Data, pokemon2Data, matchId, round):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    winner = decideWinner([pokemon1Data["pv"],pokemon1Data["att"]],[pokemon2Data["pv"],pokemon2Data["att"]])
    cursor.execute("""UPDATE rounds SET winner = ? WHERE matchId = ? and roundIndex = ?""",(winner, matchId, round))
    db.commit()
    db.close()
    return winner


def launchRound(matchId, round):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT creatorPokemon, receiverPokemon FROM rounds WHERE matchId = ? and roundIndex = ?""",(matchId, round))
    pokemons = cursor.fetchone()
    db.close()
    creatorPokemon, receiverPokemon = pokemons
    creatorPokemonData = getPokemonInfo(creatorPokemon)
    receiverPokemonData = getPokemonInfo(receiverPokemon)
    # on décide du gagnant et on store les infos du round en bd
    winner = setRoundWinner(creatorPokemonData, receiverPokemonData, matchId, round)
    matchFinished = True if round == 4 else False
    return (winner, matchFinished)

def getMatchWinner(matchId):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT SUM(winner) FROM rounds WHERE matchId = ?""",(matchId,))
    winsByReceiver = cursor.fetchone()
    db.close()
    if winsByReceiver[0] < 3:
        return 0
    else:
        return 1

def setMatchWinner(matchId):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    winner = getMatchWinner(matchId)
    cursor.execute("""UPDATE matchs SET winner = ?, status = 3 WHERE id = ?""",(winner, matchId))
    db.commit()
    db.close()
    return winner



# ----------------- AUTH API REQUESTS -----------------------------

def getPlayerId(_token):
    query = "query{getId(_token:\""+_token+"\")}"
    response = responseHttp(PORT_AUTH, query)
    return response["getId"]

# ----------------- PLAYER API REQUESTS -----------------------------

def playerExist(_token):
    query = "query{playerExist(_token:\""+_token+"\"){ response,error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["playerExist"]

def getPokemons(_token):
    query = "query{getPersonalInformation(_token:\""+_token+"\"){player{pokemons{id}},error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["getPersonalInformation"]

# ----------------- MATCH API RESOLVER  -----------------------------

def getMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM matchs WHERE id = ?""",(_matchId,))
        matchData = cursor.fetchone()
        if matchData:
            id, sender, receiver, statusInt, winner = matchData
            status = ["sent", "accepted", "started", "finished"][statusInt]
            match = {"id":id,"status":status, "sender":sender, "receiver":receiver, "winner": winner}
            return {"match": match}
        else:
            return {"error": "Unknown match, maybe deleted"}
    else:
        return {"error": errorMessage}

def getMatchList(_, info, _token):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM matchs""")
        matchs = cursor.fetchall()
        db.close()
        matchList = []
        for matchData in matchs:
            id, sender, receiver,status, winner = matchData
            matchList.append({"id":id,"status":status, "sender":sender, "receiver":receiver, "winner": winner} )
        return {"matchs": matchList}
    else:
        return {"error": errorMessage}

def getRoundsFromMatchId(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        matchExist = getMatch(_, info, _token, _matchId)
        if matchExist["match"]:
            db = sqlite3.connect(DB_PATH)
            cursor = db.cursor()
            cursor.execute("""SELECT * FROM rounds WHERE matchId = ? ORDER BY roundIndex""",(_matchId,))
            roundsInfo = []
            roundsData = cursor.fetchall()
            for round in roundsData:
                _, _, roundIndex, creatorPokemon, receiverPokemon, winner = round
                roundsInfo.append({"roundIndex": roundIndex, "creatorPokemon":creatorPokemon, "receiverPokemon": receiverPokemon, "winner":winner})
            db.close()
            return {"rounds": roundsInfo}
        else:
            return {"error": matchExist["error"]}
    else:
        return {"error": errorMessage}

def createMatch(_,info, _token, _receiverId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        senderId = getPlayerId(_token)
        cursor.execute("""INSERT INTO matchs( sender, receiver) VALUES (?, ?)""",(senderId, _receiverId))
        db.commit()
        db.close()
        return {"success":"Match created"}
    else:
        return {"error": errorMessage}

def deleteMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT sender, status FROM matchs WHERE id = ?""",(_matchId,))
        match = cursor.fetchone()
        if match:
            sender, status = match
            playerId = getPlayerId(_token)
            if(sender == playerId):
                if(status == 0):
                    cursor.execute("""DELETE FROM matchs WHERE id = ?""",(_matchId,))
                    db.commit()
                    db.close()
                    return {"success":"Match deleted !"}
                else:
                    return {"error":"This match was already accepted, it's too late to delete it"}
            else:
                return {"error":"You can't delete this match, you're not its creator"}
        else:
            return {"error": "Unknown match, maybe deleted"}
    else:
        return {"error": errorMessage}

def acceptMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT sender, receiver, status FROM matchs WHERE id = ?""",(_matchId,))
        match = cursor.fetchone()
        if match:
            sender, receiver, status = match
            playerId = getPlayerId(_token)
            if sender != playerId:
                if (receiver is None) or receiver == playerId:
                    if status == 0:
                        cursor.execute("""UPDATE matchs SET receiver = %s, status = %s WHERE id = %s"""%(playerId, 1, _matchId))
                        db.commit()
                        db.close()
                        return {"success":"Match accepted!"}
                    else:
                        return {"error":"Somedbody has already accepted this match"}
                else:
                    return {"error":"You can't accept this match, you're not the player it's destined to"}
            else:
                return {"error":"You have created the match, you cannot accept it"}
        else:
            return {"error": "Unknown match, maybe deleted"}
    else:
        return {"error": errorMessage}


def playerAddsPokemon(_, info,_token, _matchId, _pokemonId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        print("step 1")
        match = getMatch(_, info, _token, _matchId)
        if match["match"]:
            matchData = match["match"]
            print("step 2")
            playerId = getPlayerId(_token)
            sender, receiver, status = matchData["sender"], matchData["receiver"], matchData["status"]
            if playerId == sender or playerId == receiver:
                print("step 3")
                creatorOrReceiver = 0 if playerId == sender else 1
                if status != 0:
                    print("step 4")
                    if status != 3:
                        print("step 5")
                        pokemonInMyTeam, errorPokemonMessage = isMyPokemon(_token, _pokemonId)
                        if pokemonInMyTeam:
                            print("step 6")
                            responseRounds = getRoundsFromMatchId(_, info, _token, _matchId)
                            rounds = responseRounds["rounds"]
                            if rounds or rounds == []:
                                print("step 7")
                                if not isPokemonOut(rounds, _pokemonId, creatorOrReceiver):
                                    print("step 8")
                                    print(needNewRound(rounds))
                                    if needNewRound(rounds):
                                        print("step 9")
                                        newRoundIndex = 0 if rounds == [] else rounds[-1]["roundIndex"] + 1 
                                        createNewRound(_matchId, _pokemonId, creatorOrReceiver, newRoundIndex)
                                        return {"success": "START ROUND "+str(newRoundIndex)+": Waiting for your opponent"}
                                    else:
                                        if opponentHasChosenHisPokemon(rounds, creatorOrReceiver):
                                            RoundIndex = rounds[-1]["roundIndex"]
                                            addPokemonToRound(_matchId, RoundIndex, _pokemonId, creatorOrReceiver)
                                            roundWinner, matchFinished = launchRound(_matchId, RoundIndex)
                                            successMessage = ""
                                            if roundWinner == creatorOrReceiver:
                                                successMessage += "ROUND "+str(RoundIndex)+": You win"
                                            else:
                                                successMessage += "ROUND "+str(RoundIndex)+": You lose"

                                            if matchFinished:
                                                matchWinner = setMatchWinner(_matchId)
                                                if matchWinner == creatorOrReceiver:
                                                    successMessage += ", You win the match"
                                                else:
                                                    successMessage += ", You lose the match"
                                            return {"success": successMessage}
                                        else:
                                            return {"error": "Waiting for your opponent..."}
                                else:
                                    return {"error": "Pokemon out"}
                            else:
                                return {"error": responseRounds["error"]}
                        else:
                            return {"error": errorPokemonMessage}
                    else:
                        return {"error":"Match finished"}
                else:
                    return {"error":"You have to accept the match first"}
            else:
                return {"error":"You're not playing in this match"}
        else:
            return {"error": match["error"]}
    else:
        return {"error": errorMessage}