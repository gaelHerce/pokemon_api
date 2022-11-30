CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    pwd     TEXT NOT NULL,
    role    TEXT DEFAULT 'player' CHECK (role IN ('player', 'admin', 'reporter')),
    token   TEXT UNIQUE
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
    
INSERT INTO users (username, pwd, role) VALUES 
    ('player1','123456', 'player'),
    ('player2','123456', 'player'),
    ('player3','123456', 'player'),
    ('mainAdmin','123456', 'admin');