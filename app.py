from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io, os

app = Flask(__name__)

# ── Font setup ──────────────────────────────────────────
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OCR-B.ttf')

# ⚠️ NOUVELLES COORDONNÉES AFFINÉES (D'après la dernière capture) ⚠️

# --- LA DATE --- (Entre les slashes / / )
X_DATE_J = 460   # Jour (23) - décalé à droite
X_DATE_M = 510   # Mois (02) - décalé à gauche
X_DATE_A = 595   # Année (2026) - décalé à gauche

# --- LES HEURES --- (Autour des deux points : )
X_DEP_H  = 265   # Départ Heure (12) - décalé à droite
X_DEP_M  = 305   # Départ Min (54) - décalé à gauche
X_ARR_H  = 535   # Arrivée Heure (13) - décalé à gauche
X_ARR_M  = 610   # Arrivée Min (52) - décalé à gauche

# --- LA DISTANCE --- (Juste avant le 'km')
X_DIST   = 635   # décalé à droite pour coller au 'km'

# --- LES PRIX --- (Alignés à droite avant le '€')
X_PRICE  = 645   # décalé à gauche pour ne pas toucher le €

# --- POSITIONS Y --- (Hauteur : on remonte tout !)
Y_DATE     = 375
Y_HEURE    = 410
Y_DISTANCE = 450

# J'ai aussi un peu remonté les prix au cas où
Y_CHARGE   = 770
Y_TTC      = 860
Y_TVA      = 935
Y_HT       = 985


def build_ticket_image(jour, mois, annee, depart, arrivee, distance, prix_ttc):
    ht  = prix_ttc / 1.10
    tva = prix_ttc - ht

    # 1. Ouvrir le template 739x2000
    img_path = os.path.join(os.path.dirname(__file__), 'template.png')
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 2. Tailles de police
    SIZE_NORMAL = 34
    SIZE_TTC    = 52

    try:
        font = ImageFont.truetype(FONT_PATH, SIZE_NORMAL)
        font_ttc = ImageFont.truetype(FONT_PATH, SIZE_TTC)
    except:
        font = ImageFont.load_default()
        font_ttc = font

    COLOR_INK = (40, 40, 40)

    def write_text(text, x, y, fnt=font, align='right'):
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        
        start_x = x
        if align == 'right':
            start_x = x - tw 

        draw.text((start_x, y), text, font=fnt, fill=COLOR_INK)
        draw.text((start_x + 1, y), text, font=fnt, fill=COLOR_INK)

    # --- ÉCRITURE SÉPARÉE SUR L'IMAGE ---
    
    # DATE
    write_text(jour, x=X_DATE_J, y=Y_DATE, align='left')
    write_text(mois, x=X_DATE_M, y=Y_DATE, align='left')
    write_text(annee, x=X_DATE_A, y=Y_DATE, align='left')
    
    # HEURES
    dep_h, dep_m = depart.split(':')
    arr_h, arr_m = arrivee.split(':')
    
    write_text(dep_h, x=X_DEP_H, y=Y_HEURE, align='left')
    write_text(dep_m, x=X_DEP_M, y=Y_HEURE, align='left')
    write_text(arr_h, x=X_ARR_H, y=Y_HEURE, align='left')
    write_text(arr_m, x=X_ARR_M, y=Y_HEURE, align='left')
    
    # DISTANCE
    write_text(f"{distance}", x=X_DIST, y=Y_DISTANCE, align='right') 
    
    # PRIX
    write_text(f"2.94", x=X_PRICE, y=Y_CHARGE, align='right')
    write_text(f"{prix_ttc:.2f}", x=X_PRICE, y=Y_TTC, fnt=font_ttc, align='right')
    write_text(f"{tva:.2f}", x=X_PRICE, y=Y_TVA, align='right')
    write_text(f"{ht:.2f}", x=X_PRICE, y=Y_HT, align='right')

    # 3. Sauvegarder en PDF
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=100.0)
    buf.seek(0)
    return buf

HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ticket Taxi — Pillow Mod</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:#e5e7eb;font-family:system-ui,sans-serif;display:flex;
       justify-content:center;align-items:flex-start;min-height:100vh;padding:32px 16px;}
  .card{background:white;padding:32px;border-radius:16px;
        box-shadow:0 4px 24px rgba(0,0,0,0.12);width:100%;max-width:420px;}
  h1{font-size:22px;font-weight:700;color:#111;margin-bottom:6px;}
  p{font-size:13px;color:#6b7280;margin-bottom:24px;}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}
  label{font-size:12px;font-weight:600;color:#374151;display:block;margin-bottom:5px;}
  input{border:1.5px solid #d1d5db;padding:9px 11px;width:100%;
        border-radius:8px;font-size:14px;}
  .full{margin-bottom:20px;}
  button{background:#4f46e5;color:white;font-weight:700;width:100%;
         padding:14px;border:none;border-radius:10px;cursor:pointer;font-size:15px;}
</style>
</head>
<body>
<div class="card">
  <h1>🧾 Ticket Taxi (Pillow)</h1>
  <form method="POST" action="/generate">
    <div class="grid">
      <div><label>Date</label><input name="date" type="date" value="2026-02-23" required></div>
      <div><label>Distance</label><input name="distance" type="number" step="0.1" value="64.8" required></div>
    </div>
    <div class="grid">
      <div><label>Départ</label><input name="depart" type="time" value="12:54" required></div>
      <div><label>Arrivée</label><input name="arrivee" type="time" value="13:52" required></div>
    </div>
    <div class="full">
      <label>Prix Total TTC (€)</label><input name="prix" type="number" step="0.01" value="135.24" required>
    </div>
    <button type="submit">⬇ Télécharger PDF</button>
  </form>
</div>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    raw_date = request.form['date']
    y, m, d  = raw_date.split('-')

    buf = build_ticket_image(
        d, m, y, 
        request.form['depart'], 
        request.form['arrivee'], 
        request.form['distance'], 
        float(request.form['prix'])
    )

    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f'Ticket_{d}-{m}-{y}.pdf')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
