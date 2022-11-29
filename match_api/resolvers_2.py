import sqlite3
import requests

DB_PATH = "db/database.db"
PORT_AUTH = 3001
PORT_PLAYER = 3003


def responseHttp(port, query):
    response = requests.post("http://localhost:" + str(port) + "/graphql", json={'query': query})
    dataResponse = response.json()
    return dataResponse["data"]


# ----------------- GENERAL FUNCTION  -----------------------------

def getPokemonInfo(_pokemonId):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute(
        """SELECT pokemon_owners.id, pokemons.name, pokemons.type, pokemons.att, pokemons.pv FROM pokemons INNER JOIN pokemon_owners ON pokemons.id = pokemon_owners.pokemon WHERE pokemon_owners.id = ?""",
        (_pokemonId,))
    pokemon = cursor.fetchone()
    id, name, type, att, pv = pokemon
    return {"id": id, "name": name, "type": type, "pv": pv, "att": att}


def creatorOfMatch(rounds, playerId, sender):
    playerPokemonIdentifier = ""
    opponentPokemonIdentifier = ""
    pokemonsOut = []

    if (playerId == sender):  # on est le createur du match
        playerPokemonIdentifier = "creatorPokemon"
        pokemonsOut = [round[playerPokemonIdentifier] for round in rounds if round["winner"] == 1]
        opponentPokemonIdentifier = "receiverPokemon"
    else:
        playerPokemonIdentifier = "receiverPokemon"
        pokemonsOut = [round[playerPokemonIdentifier] for round in rounds if round["winner"] == 0]
        opponentPokemonIdentifier = "creatorPokemon"
    return (playerPokemonIdentifier, pokemonsOut, opponentPokemonIdentifier)


def startNewRoundWithPokemon(pokemonId, playerId, matchSender, matchId, roundIndex):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    if playerId == matchSender:
        cursor.execute("""INSERT INTO rounds(matchId, creatorPokemon, roundIndex) VALUES (?,?,?)""",
                       (matchId, pokemonId, roundIndex))  # on crée un nouveau round
    else:
        cursor.execute("""INSERT INTO rounds(matchId, receiverPokemon, roundIndex) VALUES (?,?,?)""",
                       (matchId, pokemonId, roundIndex))  # on crée un nouveau round
    db.commit()
    db.close()


def addPokemonToRound(round, pokemonId, playerId, sender):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    if (playerId == sender):
        cursor.execute("""UPDATE rounds SET creatorPokemon = ? WHERE id = ?""", (pokemonId, round["id"]))
    else:
        cursor.execute("""UPDATE rounds SET receiverPokemon = ? WHERE id = ?""", (pokemonId, round["id"]))
    db.commit()
    db.close()


def decideWinner(senderPokemon, receiverPokemon):
    if senderPokemon[0] / receiverPokemon[1] > receiverPokemon[0] / senderPokemon[1]:  # sender won
        return 0
    else:  # receiver won
        return 1


def setRoundWinner(pokemon1Data, pokemon2Data, round):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    winner = -1
    if pokemon1Data["id"] == round["creatorPokemon"]:
        winner = decideWinner([pokemon1Data["pv"], pokemon1Data["att"], ], [pokemon2Data["pv"], pokemon2Data["pv"]])
    else:
        winner = decideWinner([pokemon2Data["pv"], pokemon2Data["att"], ], [pokemon1Data["pv"], pokemon1Data["pv"]])
    cursor.execute("""UPDATE rounds SET winner = ? WHERE id = ?""", (winner, round["id"]))
    db.commit()
    db.close()
    return winner


def setMatchWinner(matchId, rounds):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    roundWonByCreator = 0
    for round in rounds:
        if round["winner"] == 0:
            roundWonByCreator += 1
    if roundWonByCreator == 3:
        cursor.execute("""UPDATE matchs SET winner = 0 WHERE id = ?""", (matchId,))
        db.commit()
    elif roundWonByCreator == 2:
        cursor.execute("""UPDATE matchs SET winner = 1 WHERE id = ?""", (matchId,))
        db.commit()
    else:
        return {"error": "an error occured when trying to figure who won the match, contact an admin"}


# ----------------- AUTH API REQUESTS -----------------------------

def getPlayerId(_token):
    query = "query{getId(_token:\"" + _token + "\")}"
    response = responseHttp(PORT_AUTH, query)
    return response["getId"]


# ----------------- PLAYER API REQUESTS -----------------------------

def playerExist(_token):
    query = "query{playerExist(_token:\"" + _token + "\"){ response,error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["playerExist"]


# ----------------- MATCH API RESOLVER  -----------------------------

def createMatch(_, info, _token, _receiverId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        senderId = getPlayerId(_token)
        cursor.execute("""INSERT INTO matchs( sender, receiver) VALUES (?, ?)""", (senderId, _receiverId))
        db.commit()
        db.close()
        return {"success": "Match created"}
    else:
        return {"error": errorMessage}


def deleteMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT sender, status FROM matchs WHERE id = ?""", (_matchId,))
        match = cursor.fetchone()
        sender, status = match
        playerId = getPlayerId(_token)
        if (sender == playerId):
            if (status == 0):
                cursor.execute("""DELETE FROM matchs WHERE id = ?""", (_matchId,))
                db.commit()
                db.close()
                return {"success": "Match deleted !"}
            else:
                return {"error": "This match was already accepted, it's too late to delete it"}
        else:
            return {"error": "You can't delete this match, you're not its creator"}

    else:
        return {"error": errorMessage}


def playerAddsPokemon(_, info, _token, _matchId, _pokemonId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        playerId = getPlayerId(_token)
        match = getMatch(_, info, _token, _matchId)
        id, sender, receiver, statusInt, winner = match
        if playerId == sender or playerId == receiver:
            if statusInt != 0:
                if (statusInt != 3):
                    rounds = getRoundsFromMatchId(None, None, _token, _matchId)
                    playerPokemonIdentifier, opponentPokemonIdentifier, pokemonsOut = creatorOfMatch(rounds, playerId,
                                                                                                     sender)
                    if not (_pokemonId in pokemonsOut):
                        if (len(rounds) > 0):  # au moins un round a été lancé
                            lastRound = [round for round in rounds if round["roundIndex"] == len(rounds) - 1][0]
                            if (lastRound[playerPokemonIdentifier] != None and lastRound[
                                opponentPokemonIdentifier] != None):  # les 2 joueurs avaient joué dans le dernier round, il faut en créer un nouveau
                                startNewRoundWithPokemon(playerId=playerId, matchId=id, matchSender=sender,
                                                         roundIndex=len(rounds), pokemonId=_pokemonId)
                                return {"success": "Your pokemon was added to the next round"}
                            elif (lastRound[
                                      playerPokemonIdentifier] == None):  # il a joué et pas moi (le round a été crée forcément avec 1 joueur qui a joué)
                                # on récupère les stats de son pokémon
                                addPokemonToRound(lastRound, _pokemonId, playerId, sender)
                                playerPokemonData = getPokemonInfo(_pokemonId)
                                opponentPokemonData = getPokemonInfo(lastRound[opponentPokemonIdentifier])
                                if playerPokemonData:
                                    if opponentPokemonData:
                                        # on décide du gagnant et on store les infos du round en bd
                                        winner = setRoundWinner(playerPokemonData, opponentPokemonData, lastRound)
                                        lastRound["winner"] = winner  # on complète la liste
                                        # si c'est le 5ème round, on compte les rounds et on update le match dans la bd
                                        if (lastRound["roundIndex"] == 4):  # c'est qu'on a 5 rounds
                                            setMatchWinner(matchId=id, playerId=playerId, rounds=rounds)
                                            return {
                                                "success": "Your pokemon was added to the round, the match is finished, you can check the result"}
                                        else:
                                            return {
                                                "success": "Your pokemon was added to the round, the round is finished, you can check the result"}
                                    else:
                                        return {"error": "An error occurred while fetching data about the pokemons"}
                                else:
                                    return {"error": "An error occurred while fetching data about the pokemons"}
                            else:  # j'ai joué et pas lui
                                return {"error": "You already played and you have to wait for your opponent's move"}
                        else:
                            startNewRoundWithPokemon(playerId=playerId, matchId=id, matchSender=sender,
                                                     roundIndex=len(rounds), pokemonId=_pokemonId)
                            return {"success": "Your pokemon was added to the first round"}
                    else:
                        return {
                            "error": "You cannot play that pokemon again because it was already defeated in this match"}
                else:
                    return {"error": "Match finished"}
            else:
                return {"error": "You have to accept the match first"}
        else:
            return {"error": "You're not playing in this match"}
    else:
        return {"error": errorMessage}


def getMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM matchs WHERE id = ?""", (_matchId,))
        match = cursor.fetchone()
        return {"match": match}
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
            print(matchData)
            (id, sender, receiver, statusInt, winner) = matchData
            status = ["sent", "accepted", "started", "finished"][statusInt]
            matchList.append(
                {"id": id, "status": status, "sender": sender, "receiver": receiver, "rounds": None, "winner": winner})
        return {"matchs": matchList}
    else:
        return {"error": errorMessage}


def acceptMatch(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM matchs WHERE id = ?""", (_matchId,))
        match = cursor.fetchone()
        print(match)
        (id, sender, receiver, statusInt, winner) = match
        playerId = getPlayerId(_token)
        if receiver is None or receiver == playerId:
            if sender != playerId:
                if statusInt == 0:
                    command = """UPDATE matchs SET receiver = %s, status = %s WHERE id = %s""" % (playerId, 1, _matchId)
                    print(command)
                    cursor.execute(command)
                    db.commit()
                    db.close()
                    return {"success": "you accepted the match !"}
                else:
                    return {"error": "somedbody already accepted this match"}
            else:
                return {"error": "you created the match, you cannot accept it"}
        else:
            return {"error": "you can't accept this match, you're not the player it's destined to"}
    else:
        return {"error": errorMessage}


def getRoundsFromMatchId(_, info, _token, _matchId):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM rounds WHERE matchId = ?""", (_matchId,))
        roundsInfo = []
        roundsData = cursor.fetchall()
        for round in roundsData:
            (id, _, roundIndex, creatorPokemon, receiverPokemon, winner) = round
            roundsInfo.append(
                {"id": id, "matchId": _matchId, "roundIndex": roundIndex, "creatorPokemon": creatorPokemon,
                 "receiverPokemon": receiverPokemon, "winner": winner})
        db.close()
        return {"rounds": roundsInfo}
    else:
        return {"error": errorMessage}
