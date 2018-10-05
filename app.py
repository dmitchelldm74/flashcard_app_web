from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g
from werkzeug import secure_filename
import os, sys, json, sqlite3, base64

app = Flask(__name__)

@app.before_request
def before_request():
    g.conn = sqlite3.connect(os.path.join('data', 'storage.db'))
    g.conn.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(x):
    g.conn.close()

convert_id = lambda d_id: base64.b64encode(str(d_id).encode()).decode().rstrip('=')
def add_deck(name, tags, fronts, backs):
    for f in fronts:
        if len(f) < 100:
            print
    c = g.conn.cursor()
    c.execute('INSERT INTO deck (title, requests) VALUES (?, 0)', [name])
    d_id = c.execute('SELECT id FROM deck order by id desc').fetchone()[0]
    c.executemany('INSERT INTO card (deck_id, front, back) VALUES (?, ?, ?)', [(d_id, fronts[i], backs[i]) for i in range(0, len(fronts))])
    c.executemany('INSERT INTO deck_tag VALUES (?, ?)', [(d_id, t) for t in tags.split(';')])
    g.conn.commit()
    return convert_id(d_id)

def db_get_deck(id):
    id = base64.b64decode("{}==".format(id)).decode()
    c = g.conn.cursor()
    c.execute('UPDATE deck SET requests=requests+1 WHERE id=?', [id])
    g.conn.commit()
    return c.execute('SELECT * FROM deck WHERE id=?', [id]).fetchone()

def search_decks(q):
    c = g.conn.cursor()
    return [[convert_id(d['id']), d['title'], d['requests'], d['terms']] for d in c.execute("SELECT *, (select count(*) from card where deck_id=deck.id) as terms FROM deck WHERE title LIKE ('%'||?||'%') order by requests desc", [q]).fetchall()]

def db_get_cards(id):
    id = base64.b64decode("{}==".format(id)).decode()
    c = g.conn.cursor()
    return c.execute('SELECT front, back FROM card WHERE deck_id=? order by id', [id]).fetchall()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get("name", "")
        tags = request.form.get("tags", "")
        fronts = request.form.getlist("front")
        backs = request.form.getlist("back")
        if name and fronts and backs:
            id = add_deck(name, tags, fronts, backs)
            return redirect(url_for('get_deck', id=id))
    return render_template("index.html")

@app.route('/search')
def search():
    q = request.args.get("q")
    if not q:
        return redirect(url_for('index'))
    q = q.lower()
    results = search_decks(q)
    return json.dumps(results)

@app.route('/get_deck/<id>')
def get_deck(id):
    deck = db_get_deck(id)
    if deck:
        jsonDeck = {"meta":{"token": None, "version": "0.0.1", "title": deck['title']}, "deck":[]}
        for c in db_get_cards(id):
            jsonDeck["deck"].append({"front":c['front'], "back":c['back']})
        return json.dumps(jsonDeck)
    return json.dumps({'error': "Deck %r doen\'t exist!" % (id)})

if __name__ == "__main__":
    app.run(debug=("-d" in sys.argv), host="0.0.0.0", port=80)