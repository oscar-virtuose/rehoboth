"""Tests de non-régression du site Rehoboth.

Lancer depuis le dossier du projet, avant chaque publication :
    python tests/test_site.py

Le script crée une base temporaire : il ne touche jamais data/inscriptions.db.
"""
import base64
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

os.environ["DATABASE"] = tempfile.mktemp(suffix=".db")
os.environ["ADMIN_PASSWORD"] = "secret"
os.environ["SECRET_KEY"] = "test-key"
os.environ["SITE_URL"] = "https://rehoboth.example"

import app as A  # noqa: E402

# ---------- Partie 1 : pages, formulaire, administration ----------
c = A.app.test_client()

for url in ["/", "/a-propos", "/formations", "/entrainement", "/contact", "/confidentialite",
            "/tuteur-frappe.html", "/robots.txt", "/sitemap.xml", "/api/formations", "/formations?x=1"]:
    r = c.get(url); print(url, r.status_code)
    assert r.status_code == 200, url

h = c.get("/tuteur-frappe.html").get_data(as_text=True)
assert 'href="/">← Retour au site</a>' in h
print("lien retour du tuteur OK")

r = c.get("/formations"); h = r.get_data(as_text=True)
assert "Bases de données et Microsoft Access" in h and "wa.me/2250103730014" in h
assert 'id="conseil"' in h and "Initiation à l’intelligence artificielle" in h
print("contenu formations OK")

h = c.get("/contact?formation=ia").get_data(as_text=True)
assert re.search(r'value="ia"\s+selected', h), "preselection"
print("preselection OK")

h = c.get("/contact").get_data(as_text=True)
assert "Du lundi au vendredi de 8 h à 18 h" in h
assert "le samedi de 8 h à 16 h" in h
assert "WhatsApp :</b> disponible 24 h/24" in h
print("horaires de contact OK")

r = c.get("/404-inexistant"); assert r.status_code == 404 and "Page introuvable" in r.get_data(as_text=True)
print("404 OK")

r = c.get("/robots.txt").get_data(as_text=True); assert "Sitemap: https://rehoboth.example/sitemap.xml" in r
r = c.get("/sitemap.xml").get_data(as_text=True); assert "https://rehoboth.example/a-propos" in r
print("seo OK")

# formulaire invalide
r = c.post("/inscription", data={"nom": "A", "tel": "abc", "formation": "x"})
assert r.status_code == 400
h = r.get_data(as_text=True)
assert "Indiquez votre nom" in h and "numéro WhatsApp valide" in h
assert "adresse e-mail valide" in h and "Sélectionnez une formation" in h
print("validation erreurs OK")

# honeypot
r = c.post("/inscription", data={"nom": "Bot Bot", "tel": "0102030405", "formation": "access", "website": "spam"})
assert r.status_code == 302 and r.headers["Location"].endswith("/")
print("honeypot OK")

# inscription valide
demande = {"nom": "Awa Koné", "tel": "+225 01 02 03 04 05", "email": "awa@example.com",
    "formation": "access", "formule": "Collective", "niveau": "Débutant", "mode": "Présentiel",
    "dispo": "le soir", "objectif": "Gérer mes clients"}
with patch.object(A, "envoyer_copie_inscription", side_effect=RuntimeError("SMTP indisponible")), \
        patch.object(A.app.logger, "exception") as log_erreur:
    r = c.post("/inscription", data=demande)
log_erreur.assert_called_once()
assert r.status_code == 503
assert "n’a pas été enregistrée" in r.get_data(as_text=True)
with A.app.app_context():
    assert A.connexion().execute("SELECT COUNT(*) FROM inscriptions").fetchone()[0] == 0
print("échec d’envoi signalé sans enregistrer la demande")

with patch.object(A, "envoyer_copie_inscription") as envoyer:
    r = c.post("/inscription", data=demande)
envoyer.assert_called_once()
assert envoyer.call_args.args[0]["email"] == "awa@example.com"
assert r.status_code == 302, r.status_code
loc = r.headers["Location"]; print("redirection", loc)
m = c.get(loc); h = m.get_data(as_text=True)
assert m.status_code == 200 and "Demande n° 1" in h
assert "Une copie a été envoyée à l’adresse e-mail de l’Académie" in h
wa = re.search(r'href="(https://wa\.me/[^"]+)"', h).group(1)
from urllib.parse import unquote
txt = unquote(wa)
assert "Awa Koné" in txt and "awa@example.com" in txt
assert "Bases de données et Microsoft Access" in txt and "Gérer mes clients" in txt
print("merci + WhatsApp OK")

# notification SMTP sans connexion réelle
A.app.config.update(SMTP_HOST="smtp.example.com", SMTP_PORT=587, SMTP_USER="academy@example.com",
    SMTP_PASSWORD="test-password", SMTP_SENDER="academy@example.com", SMTP_USE_SSL=False)
smtp = MagicMock()
smtp.__enter__.return_value = smtp
with patch.object(A.smtplib, "SMTP", return_value=smtp) as creer_smtp:
    A.envoyer_copie_inscription(demande, "Bases de données et Microsoft Access")
creer_smtp.assert_called_once_with("smtp.example.com", 587, timeout=15)
smtp.starttls.assert_called_once()
courriel = smtp.send_message.call_args.args[0]
assert courriel["To"] == "rehobothskillsacademy@gmail.com"
assert courriel["Reply-To"] == "awa@example.com"
assert "E-mail : awa@example.com" in courriel.get_content()
assert "Gérer mes clients" in courriel.get_content()
print("notification e-mail SMTP OK")

# jeton inconnu
assert c.get("/merci/faux-jeton").status_code == 404
print("jeton inconnu OK")

# admin
assert c.get("/admin").status_code == 401
assert c.get("/admin", headers={"Authorization": "Basic " + base64.b64encode(b"admin:mauvais").decode()}).status_code == 401
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:secret").decode()}
h = c.get("/admin", headers=auth).get_data(as_text=True)
assert "Awa Koné" in h and "awa@example.com" in h and "wa.me/225" in h
print("admin liste OK")
jeton = re.search(r'name="csrf_token" value="([^"]+)"', c.get("/admin", headers=auth).get_data(as_text=True)).group(1)
r = c.post("/admin/1/statut", data={"statut": "inscrit", "csrf_token": jeton}, headers=auth); assert r.status_code == 302
r = c.post("/admin/1/statut", data={"statut": "hack", "csrf_token": jeton}, headers=auth); assert r.status_code == 400
assert "inscrit" in c.get("/admin?statut=inscrit", headers=auth).get_data(as_text=True)
csv_ = c.get("/admin/export.csv", headers=auth).get_data(as_text=True)
assert "Awa Koné" in csv_ and "awa@example.com" in csv_ and "email" in csv_
assert csv_.startswith("\ufeffid") or "Awa Koné" in csv_
print("statut + export OK")

# admin désactivée sans mot de passe
A.app.config["ADMIN_PASSWORD"] = ""
assert c.get("/admin", headers=auth).status_code == 404
print("admin désactivable OK")

# rechargement dynamique du contenu
p = A.CONTENU_FICHIER
d = json.loads(p.read_text(encoding="utf-8"))
d["contact"]["telephone"] = "+225 TEST 00"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
assert "+225 TEST 00" in c.get("/contact").get_data(as_text=True)
d["contact"]["telephone"] = "+225 01 03 73 00 14"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("contenu dynamique OK")
print("TOUS LES TESTS PASSENT")

# ---------- Partie 2 : protection CSRF ----------
A.app.config["ADMIN_PASSWORD"] = "secret"
c = A.app.test_client()
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:secret").decode()}

with patch.object(A, "envoyer_copie_inscription"):
    c.post("/inscription", data={"nom": "Awa Koné", "tel": "0102030405", "email": "awa@example.com",
        "formation": "access", "formule": "Collective", "niveau": "Débutant", "mode": "Présentiel"})

# 1. Sans jeton : refusé
r = c.post("/admin/1/statut", data={"statut": "inscrit"}, headers=auth)
assert r.status_code == 400, r.status_code; print("sans jeton -> 400 OK")

# 2. Jeton faux : refusé
r = c.post("/admin/1/statut", data={"statut": "inscrit", "csrf_token": "faux"}, headers=auth)
assert r.status_code == 400; print("jeton faux -> 400 OK")

# 3. Jeton présent dans la page admin : accepté
page = c.get("/admin", headers=auth).get_data(as_text=True)
jeton = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
r = c.post("/admin/1/statut", data={"statut": "inscrit", "csrf_token": jeton}, headers=auth)
assert r.status_code == 302; print("jeton valide -> 302 OK")
assert "inscrit" in c.get("/admin?statut=inscrit", headers=auth).get_data(as_text=True)

# 4. Attaque CSRF simulée : un autre client (sans session) avec les identifiants en cache
attaquant = A.app.test_client()
r = attaquant.post("/admin/1/statut", data={"statut": "clos"}, headers=auth)
assert r.status_code == 400; print("attaque CSRF simulée -> 400 OK")
assert "inscrit" in c.get("/admin?statut=inscrit", headers=auth).get_data(as_text=True)
print("TESTS CSRF PASSENT")

print('=== TOUS LES TESTS SONT PASSÉS ===')
