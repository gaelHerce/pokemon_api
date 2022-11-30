CREATE TABLE IF NOT EXISTS matchs (
    id INTEGER PRIMARY KEY,
    sender INTEGER NOT NULL,
    receiver INTEGER,
    status INTEGER NOT NULL CHECK (status <= 3) DEFAULT 0,  -- sent, accepted, started, finished 
    winner INTEGER CHECK (winner IN (0,1)),
    FOREIGN KEY (sender) REFERENCES players(id),
    FOREIGN KEY (receiver) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS rounds(
    id INTEGER PRIMARY KEY,
    matchId INTEGER NOT NULL,
    roundIndex INTEGER NOT NULL CHECK (roundIndex <= 4) DEFAULT 0,
    creatorPokemon INTEGER,
    receiverPokemon INTEGER,
    winner INTEGER CHECK (winner IN (0,1)),
    FOREIGN KEY (matchId) REFERENCES matchs(id)
    FOREIGN KEY (creatorPokemon) REFERENCES pokemon_owners(id)
    FOREIGN KEY (receiverPokemon) REFERENCES pokemon_owners(id)
);

CREATE TABLE IF NOT EXISTS pokemons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    att INTEGER DEFAULT 50,
    pv INTEGER DEFAULT 100
);

INSERT INTO pokemons (name, type, att, pv) VALUES 
    ("Salameche", "Feu", 123, 76),
    ("Carapuce", "Eau", 208, 53),
    ("Bulbizarre", "Plante", 192, 54),
    ("Pikachu", "Electrique", 87, 93),
    ("Miaouss", "Normal", 245, 45),
    ("Fantominus", "Spectre", 145, 64);

INSERT INTO matchs (sender, receiver) VALUES
    (1, 2),
    (1, NULL),
    (3, 2),
    (2, 3),
    (2, NULL),
    (3, 1);