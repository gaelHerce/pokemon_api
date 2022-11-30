CREATE TABLE IF NOT EXISTS players (
    id INTEGER NOT NULL,
    credits INTEGER DEFAULT 0,
    FOREIGN KEY (id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS pokemons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    att INTEGER DEFAULT 50,
    pv INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS pokemon_owners (
    pokemon INTEGER NOT NULL,
    owner INTEGER NOT NULL,
    FOREIGN KEY (pokemon) REFERENCES pokemons(id),
    FOREIGN KEY (owner) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS badges_owners (
    badge INTEGER NOT NULL,
    owner INTEGER NOT NULL,
    FOREIGN KEY (badge) REFERENCES badges(id),
    FOREIGN KEY (owner) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    sender INTEGER NOT NULL,
    receiver INTEGER NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (sender) REFERENCES players(id),
    FOREIGN KEY (receiver) REFERENCES players(id)
);

INSERT INTO players (id, credits) VALUES 
    (1, 0),
    (2, 300),
    (3, 3000);

INSERT INTO pokemons (name, type, att, pv) VALUES 
    ("Salameche", "Feu", 123, 76),
    ("Carapuce", "Eau", 208, 53),
    ("Bulbizarre", "Plante", 192, 54),
    ("Pikachu", "Electrique", 87, 93),
    ("Miaouss", "Normal", 245, 45),
    ("Fantominus", "Spectre", 145, 64);
INSERT INTO badges (description) VALUES 
    ("Gagne ton premier combat"),
    ("Bat un pokemon de type Feu"),
    ("Bat un pokemon de type Eau"),
    ("Bat un pokemon de type Plante"),
    ("Gagne deux matchs d'affiles"),
    ("Bat un pokemon avec une meilleure attaque que ton pokemon");
INSERT INTO badges_owners (badge, owner) VALUES
    (1, 1),
    (4, 1);

INSERT INTO pokemon_owners (pokemon, owner) VALUES
    (4,1),
    (6,1),
    (1,1),
    (3,1),
    (5,1),
    (1,2),
    (2,2),
    (3,2),
    (4,2),
    (6,2);

INSERT INTO messages (sender, receiver, message) VALUES
    (1,2,"Hello Max t'es chaud pour un match ?"),
    (2,1, "Ouais pourquoi pas ?"),
    (1,2, "Tu veux faire ça quand ?"),
    (2,1, "Vers 15h ?");