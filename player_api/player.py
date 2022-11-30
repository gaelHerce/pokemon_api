from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, make_response
import requests
import sqlite3
import os

import resolvers as r

PORT = 3003
HOST = '0.0.0.0'

app = Flask(__name__)

### DATABASE

SQL_PATH = "init.sql"
DB_PATH = "database.db"

def create_db(sql_path, db_path):
    os.remove(DB_PATH)
    with open(sql_path, 'r') as inp:
        sql_script = inp.read()
    inp.close()

    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.executescript(sql_script)
    db.commit()
    db.close()

####################

type_defs = load_schema_from_path('player.graphql')

query = QueryType()
query.set_field('getPlayerList', r.getPlayerList)
query.set_field('getPersonalInformation', r.getPersonalInformation)
query.set_field('getConversation', r.getConversation)
query.set_field('getReceivedMessages', r.getReceivedMessages)

mutation = MutationType()
mutation.set_field('addCredits', r.addCredits)
mutation.set_field('addPokemon', r.addPokemon)
mutation.set_field('sendMessage', r.sendMessage)


schema = make_executable_schema(type_defs, query, mutation)

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Player service!</h1>",200)

#####
# graphql entry points

@app.route('/graphql', methods=['GET'])
def playground():
    return PLAYGROUND_HTML, 200
    
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
    schema,
    data,
    context_value=None,
    debug=app.debug
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    create_db(SQL_PATH, DB_PATH)
    app.run(host=HOST, port=PORT)
