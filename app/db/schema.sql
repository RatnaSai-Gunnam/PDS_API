CREATE TABLE IF NOT EXISTS legislators (
  govtrack_id INTEGER PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  birthday DATE,
  gender VARCHAR(10),
  type VARCHAR(5) NOT NULL,
  state VARCHAR(2) NOT NULL,
  district INTEGER,
  party VARCHAR(50) NOT NULL,
  url VARCHAR(255)
);
