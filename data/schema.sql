CREATE TABLE deck (
    id integer primary key autoincrement,
    title text,
    requests int
);
CREATE TABLE card (
    id integer primary key autoincrement,
    deck_id integer,
    front text,
    back text
);
CREATE TABLE deck_tag (
    deck_id integer,
    tag text
);