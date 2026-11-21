"""Rehoboth Skills Academy : site dynamique.

Le contenu vit dans content/site.json (modifiable sans toucher au code).
Les demandes d'inscription sont enregistrées dans SQLite et consultables
dans l'espace d'administration protégé (/admin).
"""
import csv
import hmac
import io
import json
import os
import re
import secrets
import smtplib
import ssl
import sqlite3
from datetime import datetime
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from urllib.parse import quote

from flask import (Flask, Response, abort, g, redirect, render_template,
                   request, session, url_for)

BASE = Path(__file__).resolve().parent
CONTENU_FICHIER = BASE / "content" / "site.json"

app = Flask(__name__, static_folder=str(BASE / "static"))
app.config.update(
    SITE_URL=os.environ.get("SITE_URL", "http://localhost:5000").rstrip("/"),
    DATABASE=os.environ.get("DATABASE", str(BASE / "data" / "inscriptions.db")),
    ADMIN_USER=os.environ.get("ADMIN_USER", "admin"),
    # Sans mot de passe défini, l'administration reste désactivée (404).
    ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),
    # Doit être fixé en production : sinon chaque worker a sa propre clé.
    # Identifiant Google Analytics (ex. G-XXXXXXXXXX). Vide = aucun suivi.
    GA_MEASUREMENT_ID=os.environ.get("GA_MEASUREMENT_ID", "").strip(),
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SMTP_HOST=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
    SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
    SMTP_USER=os.environ.get("SMTP_USER", ""),
    SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
    SMTP_SENDER=os.environ.get("SMTP_SENDER", os.environ.get("SMTP_USER", "")),
    SMTP_USE_SSL=os.environ.get("SMTP_USE_SSL", "0") == "1",
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("HTTPS", "0") == "1",
    SESSION_COOKIE_HTTPONLY=True,
)

STATUTS = ["nouveau", "contacté", "inscrit", "clos"]
_cache = {"mtime": None, "data": None}


# ---------------------------------------------------------------- contenu

def contenu():
    """Lit site.json et le relit seulement s'il a été modifié."""
    mtime = CONTENU_FICHIER.stat().st_mtime
    if _cache["mtime"] != mtime:
        _cache["data"] = json.loads(CONTENU_FICHIER.read_text(encoding="utf-8"))
        _cache["mtime"] = mtime
    return _cache["data"]


def lien_whatsapp(texte=None):
    numero = contenu()["contact"]["whatsapp"]
    url = f"https://wa.me/{numero}"
    if texte:
        url += "?text=" + quote(texte, safe="")
    return url


def ga_id_valide():
    """Renvoie l'identifiant GA4 seulement s'il a le bon format (évite toute injection dans la page)."""
    identifiant = app.config.get("GA_MEASUREMENT_ID", "")
    return identifiant if re.fullmatch(r"G-[A-Z0-9]{4,20}", identifiant or "") else ""


def jeton_csrf():
    """Jeton stocké dans la session du navigateur, à renvoyer avec chaque formulaire admin."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def verifier_csrf():
    attendu = session.get("csrf", "")
    recu = request.form.get("csrf_token", "")
    if not attendu or not hmac.compare_digest(recu.encode(), attendu.encode()):
        abort(400, description="Jeton de sécurité invalide. Rechargez la page et réessayez.")


@app.context_processor
def injecter_contenu():
    c = contenu()
    return {
        "site": c["site"],
        "contact": c["contact"],
        "navigation": c["navigation"],
        "annee": datetime.now().year,
        "niveaux": c["niveaux"],
        "formules_choix": c["formules_choix"],
        "modes_choix": c["modes_choix"],
        "lien_whatsapp": lien_whatsapp,
        "url_absolue": lambda chemin: app.config["SITE_URL"] + chemin,
        "csrf_token": jeton_csrf,
        "ga_id": ga_id_valide(),
    }


# ---------------------------------------------------------------- base de données

def connexion():
    if "db" not in g:
        Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def fermer_connexion(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialiser_base():
    with app.app_context():
        connexion().executescript("""
            CREATE TABLE IF NOT EXISTS inscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jeton TEXT UNIQUE NOT NULL,
                cree_le TEXT NOT NULL,
                nom TEXT NOT NULL,
                tel TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                formation TEXT NOT NULL,
                formule TEXT NOT NULL,
                niveau TEXT NOT NULL,
                mode TEXT NOT NULL,
                dispo TEXT,
                objectif TEXT,
                statut TEXT NOT NULL DEFAULT 'nouveau'
            );
        """)
        colonnes = {ligne["name"] for ligne in connexion().execute("PRAGMA table_info(inscriptions)")}
        if "email" not in colonnes:
            connexion().execute(
                "ALTER TABLE inscriptions ADD COLUMN email TEXT NOT NULL DEFAULT ''"
            )
        connexion().commit()


# ---------------------------------------------------------------- en-têtes HTTP

@app.after_request
def en_tetes_securite(reponse):
    reponse.headers["X-Content-Type-Options"] = "nosniff"
    reponse.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    reponse.headers["X-Frame-Options"] = "SAMEORIGIN"
    return reponse


# ---------------------------------------------------------------- pages publiques

@app.route("/")
def index():
    c = contenu()
    offres = [f for f in c["formations"] if f.get("accueil")]
    return render_template("index.html", offres=offres, promesses=c["promesses"],
                           description=c["site"]["description"])


@app.route("/a-propos")
def a_propos():
    return render_template("apropos.html", page=contenu()["apropos"],
                           raisons=contenu()["raisons"])


@app.route("/formations")
def formations():
    c = contenu()
    return render_template("formations.html", formations=c["formations"],
                           conseil=c["conseil"], formules=c["formules"],
                           modes=c["modes"], niveaux=c["niveaux"])


@app.route("/entrainement")
def entrainement():
    return render_template("entrainement.html", page=contenu()["entrainement"])


@app.route("/tuteur-frappe.html")
def tuteur():
    # Le tuteur est une application autonome : on la sert telle quelle.
    return app.send_static_file("tuteur-frappe.html")


@app.route("/contact")
def contact():
    c = contenu()
    return render_template("contact.html", erreurs=[], valeurs={},
                           preselection=request.args.get("formation", ""),
                           formations=c["formations"], faq=c["faq"],
                           formules=c["formules"], modes=c["modes"],
                           niveaux=c["niveaux"], conseil=c["conseil"])


@app.route("/confidentialite")
def confidentialite():
    return render_template("confidentialite.html", page=contenu()["confidentialite"])


# ---------------------------------------------------------------- inscription

def _choix(valeur, options, defaut):
    return valeur if valeur in options else defaut


def envoyer_copie_inscription(demande, formation):
    serveur = app.config["SMTP_HOST"]
    utilisateur = app.config["SMTP_USER"]
    mot_de_passe = app.config["SMTP_PASSWORD"]
    expediteur = app.config["SMTP_SENDER"] or utilisateur
    destinataire = contenu()["contact"]["email"]
    if not all((serveur, utilisateur, mot_de_passe, expediteur, destinataire)):
        raise RuntimeError("La configuration SMTP est incomplète.")

    courriel = EmailMessage()
    courriel["Subject"] = f"Nouvelle demande d’inscription — {formation}"
    courriel["From"] = expediteur
    courriel["To"] = destinataire
    courriel["Reply-To"] = demande["email"]
    courriel.set_content(
        f"Nouvelle demande d’inscription reçue sur le site de {contenu()['site']['nom']}.\n\n"
        f"Nom : {demande['nom']}\n"
        f"E-mail : {demande['email']}\n"
        f"WhatsApp : {demande['tel']}\n"
        f"Formation : {formation}\n"
        f"Formule : {demande['formule']}\n"
        f"Niveau : {demande['niveau']}\n"
        f"Mode : {demande['mode']}\n"
        f"Disponibilités : {demande['dispo'] or '-'}\n"
        f"Objectif : {demande['objectif'] or '-'}\n"
    )

    contexte_ssl = ssl.create_default_context()
    if app.config["SMTP_USE_SSL"]:
        with smtplib.SMTP_SSL(serveur, app.config["SMTP_PORT"], timeout=15,
                              context=contexte_ssl) as connexion_smtp:
            connexion_smtp.login(utilisateur, mot_de_passe)
            connexion_smtp.send_message(courriel)
    else:
        with smtplib.SMTP(serveur, app.config["SMTP_PORT"], timeout=15) as connexion_smtp:
            connexion_smtp.ehlo()
            connexion_smtp.starttls(context=contexte_ssl)
            connexion_smtp.ehlo()
            connexion_smtp.login(utilisateur, mot_de_passe)
            connexion_smtp.send_message(courriel)


@app.post("/inscription")
def inscription():
    c = contenu()
    f = request.form

    # Champ piège : invisible pour les humains, rempli par les robots.
    if f.get("website"):
        return redirect(url_for("index"))

    erreurs = []
    nom = f.get("nom", "").strip()[:80]
    tel = f.get("tel", "").strip()
    email = f.get("email", "").strip()
    if len(nom) < 2:
        erreurs.append("Indiquez votre nom et prénom.")
    if not re.fullmatch(r"\+?[0-9 ().-]{8,20}", tel):
        erreurs.append("Indiquez un numéro WhatsApp valide, par exemple +225 01 02 03 04 05.")
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erreurs.append("Indiquez une adresse e-mail valide.")

    formations_choisies = {x["slug"]: x["titre"] for x in c["formations"]}
    formations_choisies["conseil"] = "Je souhaite être conseillé(e)"
    slug = f.get("formation", "")
    if slug not in formations_choisies:
        erreurs.append("Sélectionnez une formation.")

    valeurs = {
        "nom": nom, "tel": tel, "email": email, "formation": slug,
        "formule": _choix(f.get("formule"), c["formules_choix"], c["formules_choix"][0]),
        "niveau": _choix(f.get("niveau"), c["niveaux"], c["niveaux"][0]),
        "mode": _choix(f.get("mode"), c["modes_choix"], c["modes_choix"][0]),
        "dispo": f.get("dispo", "").strip()[:200],
        "objectif": f.get("objectif", "").strip()[:1000],
    }

    if erreurs:
        return render_template("contact.html", erreurs=erreurs, valeurs=valeurs,
                               preselection=slug, formations=c["formations"],
                               faq=c["faq"], formules=c["formules"], modes=c["modes"],
                               niveaux=c["niveaux"], conseil=c["conseil"]), 400

    try:
        envoyer_copie_inscription(valeurs, formations_choisies[slug])
    except (OSError, RuntimeError, smtplib.SMTPException):
        app.logger.exception("L’envoi de la copie d’inscription par e-mail a échoué.")
        return render_template(
            "contact.html", erreurs=[], erreur_systeme=(
                "La copie de votre demande n’a pas pu être envoyée par e-mail. "
                "Votre demande n’a pas été enregistrée ; réessayez plus tard ou contactez-nous sur WhatsApp."
            ), valeurs=valeurs, preselection=slug, formations=c["formations"],
            faq=c["faq"], formules=c["formules"], modes=c["modes"],
            niveaux=c["niveaux"], conseil=c["conseil"]
        ), 503

    jeton = secrets.token_urlsafe(16)
    db = connexion()
    db.execute(
        """INSERT INTO inscriptions
           (jeton, cree_le, nom, tel, email, formation, formule, niveau, mode, dispo, objectif)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (jeton, datetime.now().isoformat(timespec="seconds"), valeurs["nom"],
         valeurs["tel"], valeurs["email"], formations_choisies[slug], valeurs["formule"],
         valeurs["niveau"], valeurs["mode"], valeurs["dispo"], valeurs["objectif"]),
    )
    db.commit()
    return redirect(url_for("merci", jeton=jeton))


@app.route("/merci/<jeton>")
def merci(jeton):
    # Le jeton aléatoire empêche de parcourir les demandes des autres.
    r = connexion().execute("SELECT * FROM inscriptions WHERE jeton = ?", (jeton,)).fetchone()
    if r is None:
        abort(404)
    ref = r["id"]
    message = (
        f"Bonjour {contenu()['site']['nom']},\n"
        "Je souhaite m’inscrire.\n"
        f"Référence de ma demande : n° {ref}\n"
        f"Nom : {r['nom']}\n"
        f"E-mail : {r['email']}\n"
        f"WhatsApp : {r['tel']}\n"
        f"Formation : {r['formation']}\n"
        f"Formule : {r['formule']}\n"
        f"Niveau : {r['niveau']}\n"
        f"Mode : {r['mode']}\n"
        f"Disponibilités : {r['dispo'] or '-'}\n"
        f"Objectif : {r['objectif'] or '-'}"
    )
    return render_template("merci.html", ref=ref, lien=lien_whatsapp(message))


# ---------------------------------------------------------------- administration

def acces_admin(vue):
    @wraps(vue)
    def protege(*args, **kwargs):
        mot_de_passe = app.config["ADMIN_PASSWORD"]
        if not mot_de_passe:
            abort(404)
        auth = request.authorization
        ok = bool(auth) and hmac.compare_digest(
            (auth.username or "").encode(), app.config["ADMIN_USER"].encode()
        ) and hmac.compare_digest((auth.password or "").encode(), mot_de_passe.encode())
        if not ok:
            return Response("Accès réservé.", 401,
                            {"WWW-Authenticate": 'Basic realm="Administration"'})
        return vue(*args, **kwargs)
    return protege


@app.route("/admin")
@acces_admin
def admin():
    filtre = request.args.get("statut", "")
    sql = "SELECT * FROM inscriptions"
    params = ()
    if filtre in STATUTS:
        sql += " WHERE statut = ?"
        params = (filtre,)
    sql += " ORDER BY id DESC"
    lignes = connexion().execute(sql, params).fetchall()
    return render_template("admin.html", lignes=lignes, statuts=STATUTS, filtre=filtre)


@app.post("/admin/<int:ident>/statut")
@acces_admin
def admin_statut(ident):
    verifier_csrf()
    nouveau = request.form.get("statut", "")
    if nouveau not in STATUTS:
        abort(400)
    db = connexion()
    db.execute("UPDATE inscriptions SET statut = ? WHERE id = ?", (nouveau, ident))
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/export.csv")
@acces_admin
def admin_export():
    lignes = connexion().execute("SELECT * FROM inscriptions ORDER BY id").fetchall()
    tampon = io.StringIO()
    ecrivain = csv.writer(tampon, delimiter=";")
    if lignes:
        ecrivain.writerow(lignes[0].keys())
    for ligne in lignes:
        ecrivain.writerow(list(ligne))
    return Response(
        tampon.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inscriptions.csv"},
    )


# ---------------------------------------------------------------- SEO et API

@app.route("/robots.txt")
def robots():
    texte = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        f"Sitemap: {app.config['SITE_URL']}/sitemap.xml\n"
    )
    return Response(texte, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = ["index", "a_propos", "formations", "entrainement", "contact", "confidentialite"]
    urls = [app.config["SITE_URL"] + (url_for(p) if p != "index" else "/") for p in pages]
    urls.append(app.config["SITE_URL"] + "/tuteur-frappe.html")
    corps = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{corps}</urlset>\n")
    return Response(xml, mimetype="application/xml")


@app.route("/api/formations")
def api_formations():
    return {"formations": contenu()["formations"]}


@app.template_filter("chiffres")
def chiffres(texte):
    """Ne garde que les chiffres (pour les liens wa.me)."""
    return re.sub(r"\D", "", texte or "")


@app.errorhandler(404)
def page_introuvable(_erreur):
    return render_template("404.html"), 404


initialiser_base()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
