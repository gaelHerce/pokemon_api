CREATE TABLE IF NOT EXISTS store(
    pokemon INTEGER NOT NULL UNIQUE,
    price INTEGER DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    FOREIGN KEY (pokemon) REFERENCES pokemons(id)
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
    
INSERT INTO store (pokemon, price, quantity) VALUES
    (1, 0, 4),
    (2, 0, 4),
    (3, 0, 0),
    (4, 150, 1),
    (5, 300, 3),
    (6, 400, 1);