from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import sqlite3
import os

app = Flask(__name__)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
app.secret_key = os.environ.get("SECRET_KEY")

CHEMIN_BDD = os.path.join(os.path.dirname(__file__), "database.db")


def init_bdd():
    conn = sqlite3.connect(CHEMIN_BDD)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT NOT NULL,
            message TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_bdd()

@app.template_filter('date_fr')
def date_fr(valeur):
    date = datetime.strptime(valeur, "%Y-%m-%d %H:%M:%S")
    date = date.replace(tzinfo=timezone.utc)
    date = date.astimezone(ZoneInfo("Europe/Paris"))
    return date.strftime("%d/%m/%Y à %Hh%M")


@app.route('/', methods=['GET', 'POST'])
def accueil():
    # ----- Envoi du formulaire -----
    if request.method == 'POST':
        pseudo = request.form.get('pseudo', '').strip()
        message = request.form.get('message', '').strip()
        site_web = request.form.get('site_web', '')

        # Robot : on ignore sans rien dire
        if site_web:
            return redirect(url_for('accueil'))

        # Champs vides ou trop longs
        if not pseudo or not message or len(pseudo) > 50 or len(message) > 500:
            flash("Merci de remplir le pseudo (50 caractères max) et le message (500 caractères max).")
            return redirect(url_for('accueil', _anchor='reactions'))

        conn = sqlite3.connect(CHEMIN_BDD)

        # Ce pseudo a-t-il déjà écrit ?
        deja = conn.execute(
            "SELECT 1 FROM messages WHERE pseudo = ? COLLATE NOCASE",
            (pseudo,)
        ).fetchone()

        if deja:
            conn.close()
            flash("Ce pseudo a déjà laissé un message : un seul message par pseudo !")
            return redirect(url_for('accueil', _anchor='reactions'))

        conn.execute(
            "INSERT INTO messages (pseudo, message) VALUES (?, ?)",
            (pseudo, message)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('accueil', _anchor='reactions'))

    # ----- Affichage de la page -----
    conn = sqlite3.connect(CHEMIN_BDD)
    conn.row_factory = sqlite3.Row
    messages = conn.execute(
        "SELECT pseudo, message, date FROM messages ORDER BY date DESC"
    ).fetchall()
    conn.close()

    print(len(messages))
    return render_template('index.html', messages=messages)


if __name__ == '__main__':
    app.run(debug=True)