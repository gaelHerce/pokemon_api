import sqlite3
from uuid import uuid4
import requests

PORT_AUTH = 3001
PORT_PLAYER = 3003
DB_PATH = "db/database.db"

def responseHttp(port, query):
    response = requests.post("http://0.0.0.0:"+str(port)+"/graphql", json={'query':query})
    dataResponse = response.json()
    return dataResponse["data"]

# ----------------- AUTH API REQUESTS -----------------------------

def getPlayerId(_token):
    queryId = "query{getId(_token:\""+_token+"\")}"
    response = responseHttp(PORT_AUTH, queryId)
    return response["getId"]

# ----------------- PLAYER API REQUESTS -----------------------------

def playerExist(_token):
    query = "query{playerExist(_token:\""+_token+"\"){ response,error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["playerExist"]

def getCredits(_token):
    query = "query{getPersonalInformation(_token:\""+_token+"\"){player{credits},error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["getPersonalInformation"]

def addCredits(_token, credits):
    query = "mutation{addCredits(_token:\""+_token+"\",_credits:"+str(credits)+"){ error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["addCredits"]["error"]

def addPokemon(_token, pokemon):
    query = "mutation{addPokemon(_token:\""+_token+"\",_pokemonId:"+str(pokemon)+"){ error}}"
    response = responseHttp(PORT_PLAYER, query)
    return response["addPokemon"]["error"]


# ----------------- STORE API RESOLVER  -----------------------------

def buyPokemon(_,info, _token, _pokemonId):
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute("""SELECT quantity, price FROM store JOIN pokemons ON store.pokemon == pokemons.id WHERE pokemons.id = ?""",(_pokemonId,))
    response = cursor.fetchone()
    quantity, price = response[0], response[1]
    playerCredits = getCredits(_token)
    errorMessage = playerCredits["error"]
    if not errorMessage:
        if quantity > 0:
            currentCredits = playerCredits["player"]["credits"]
            if currentCredits >= price:
                addCreditsError = addCredits(_token, -price)
                if not addCreditsError:
                    addPokemonError = addPokemon(_token, _pokemonId)
                    if not addPokemonError:
                        cursor.execute("""UPDATE store SET quantity = ? WHERE pokemon = ?""", (quantity-1, _pokemonId))
                        db.commit()
                        db.close()
                        return {"success": "Pokemon succesfuly bought"}
                    else:
                        addCredits(_token, price)
                        db.close()
                        return {"error": addPokemonError}
                else:
                    db.close()
                    return {"error": addCreditsError}
            else:
                db.close()
                return {"error": "Not enough credits"}
        else:
            db.close()
            return {"error": "Pokemon solded out"}
    else:
        db.close()
        return {"error": errorMessage}


def getAvailablePokemons(_, _info, _token):
    responsePlayerExist = playerExist(_token)
    isPlayer, errorMessage = responsePlayerExist["response"], responsePlayerExist["error"]
    if isPlayer:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("""SELECT pokemons.id, pokemons.name, pokemons.type, pokemons.att, pokemons.pv, store.price, store.quantity FROM store INNER JOIN pokemons ON store.pokemon = pokemons.id WHERE store.quantity > 0""")
        pokemonInStore = cursor.fetchall()
        db.close()
        pokemonsAvailable = []
        for pokemon in pokemonInStore:
            id, name, type, att, pv, price, quantity = pokemon
            pokemonsAvailable.append({"pokemon":{"id": id, "type": type, "name": name, "att": att, "pv":pv}, "price" : price, "quantity": quantity}) 
        return {"pokemons": pokemonsAvailable}
    else:
        return {"error": errorMessage}

    