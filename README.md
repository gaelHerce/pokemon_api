# API Pokemon by Clément DOURS, Louis GIBOIN and Gaël HERCE

<h2>To start a game, lauch auth.py, player.py, store.py and match.py</h2>

the Statistics service has not been implemented, but the others work


<h4>All endpoints are discribed in the doc folder (open index.html for each service), but here are the main endpoints you can use to play a game</h4>

> Using the auth api, you can:<br>
> 	- connect with a password and a username, endpoint ***connect(_userName:String!, _pwd:String!):ConnectResult***. If it succeeds you get a token that will be used in the other endpoints<br>
> 	- disconnect with your token, endpoint ***disconnect(_token: String!): MutationResult***.<br>

  

> Using the player api, you can:<br>
>	- sendMessages, endpoint ***sendMessage(_token: String!, _message:String!, _receiverId: Int!): MutationResult***.<br>
>	- change username and password, endpoints ***changeUserName(_token: String!, _newName: String!): MutationResult*** and ***changePwd(_token:String!,_newPwd:String!):MutationResult***.<br>
>	- see your received messages and info on other players, endpoints: ***getReceivedMessages(_token: String!): MessagesResult***,  ***getConversation(_token:String!,_otherPlayerId: Int!):MessagesResult*** and ***getPlayerList: PlayersResult***.<br>
>	- see the matchs you have been invited to, endpoint: ***getInvitations(_token: String!):InvitationsResult***<br>



>Using the store api, you can: <br>
>	- see the pokemons that are available in store, endpoint: ***getAvailablePokemons(_token:String): PokemonInStoreResult***.<br>
>	- buy a pokemon from the store, endpoint ***buyPokemon(_token: String!, _pokemonId: Int!): MutationResult***.<br>



>Using the match api, you can:<br>
>	- see the list of all matchs, or a specific match and its details using its Id, endpoints:  ***getMatchList(_token:String!): MatchsResult***  and  ***getMatch(_matchId:Int!, _token:String!): MatchResult***.<br>
>	- create, accept and delete a match, endpoints: ***createMatch(_token:String!, _receiverId:Int):MutationResult***,  ***acceptMatch(_token:String!, _matchId:Int!):MutationResult***  and  ***deleteMatch(_token:String!, _matchId:Int!):MutationResult***.<br>
>	- add one of your pokemons in the last round of one of your matchs, endpoint: ***playerAddsPokemon(_token:String!, _matchId:Int!, _pokemonId:Int!): MutationResult***.<br>


	
