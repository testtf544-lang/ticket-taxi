from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io, os

app = Flask(__name__)

# ── Font setup ──────────────────────────────────────────
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OCR-B.ttf')

# ⚠️ ZONES DE MASQUAGE ET D'ÉCRITURE (Pour template.png 739x2000) ⚠️
# Format: (X_debut, Y_debut, Largeur, Hauteur)
BOX_DATE     = (420, 390, 260, 45)  # Cache l'ancienne date
BOX_DEP      = (230, 440, 110, 45)  # Cache l'ancienne heure de départ
BOX_ARR      = (530, 440, 110, 45)  # Cache l'ancienne heure d'arrivée
BOX_DIST     = (500, 490, 140, 45)  # Cache l'ancienne distance

BOX_CHARGE   = (500, 785, 160, 45)  # Cache le prix de prise en charge
BOX_TTC      = (450, 860, 210, 60)  # Cache le grand prix TTC
BOX_TVA      = (500, 940, 160, 45)  # Cache la TVA
BOX_HT       = (500, 990, 160, 45)  # Cache le HT

def build_ticket_image(date_str, depart, arrivee, distance, prix_ttc):
    ht  = prix_ttc / 1.10
    tva = prix_ttc - ht

    # 1. Ouvrir l'image PNG
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

    # Couleurs
    COLOR_INK = (40, 40, 40)         # Gris thermique pour le texte
    COLOR_PAPER = (255, 255, 255)    # Blanc pour masquer l'ancien texte

    def hide_and_write(text, box, fnt=font, align='right'):
        x, y, w, h = box
        
        # 1. Masquer l'ancien texte avec un rectangle blanc
        draw.rectangle([x, y, x + w, y + h], fill=COLOR_PAPER)

        # 2. Mesurer la taille du nouveau texte
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        
        # 3. Calculer l'alignement
        start_x = x
        if align == 'right':
            start_x = x + w - tw 

        # 4. Écrire le texte (avec effet gras)
        draw.text((start_x, y), text, font=fnt, fill=COLOR_INK)
        draw.text((start_x + 1, y), text, font=fnt, fill=COLOR_INK)

    # --- REMPLACEMENT AUTOMATIQUE SUR L'IMAGE ---
    
    hide_and_write(date_str, BOX_DATE, align='right')
    hide_and_write(depart, BOX_DEP, align='left')
    hide_and_write(arrivee, BOX_ARR, align='right')
    hide_and_write(f"{distance}", BOX_DIST, align='right') 
    
    hide_and_write("2.94", BOX_CHARGE, align='right')
    hide_and_write(f"{prix_ttc:.2f}", BOX_TTC, fnt=font_ttc, align='right')
    hide_and_write(f"{tva:.2f}", BOX_TVA, align='right')
    hide_and_write(f"{ht:.2f}", BOX_HT, align='right')

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
<title>Ticket Taxi — Générateur</title>
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
  <h1>🧾 Ticket Taxi</h1>
  <p>Veuillez entrer les informations de la course.</p>
  <form method="POST" action="/generate">
    <div class="grid">
      <div><label>Date</label><input name="date" type="date" required></div>
      <div><label>Distance (km)</label><input name="distance" type="number" step="0.1" placeholder="Ex: 64.8" required></div>
    </div>
    <div class="grid">
      <div><label>Départ</label><input name="depart" type="time" required></div>
      <div><label>Arrivée</label><input name="arrivee" type="time" required></div>
    </div>
    <div class="full">
      <label>Prix Total TTC (€)</label><input name="prix" type="number" step="0.01" placeholder="Ex: 135.24" required>
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
    date_str = f'{d}/{m}/{y}'

    buf = build_ticket_image(
        date_str, 
        request.form['depart'], 
        request.form['arrivee'], 
        request.form['distance'], 
        float(request.form['prix'])
    )

    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f'Ticket_{d}-{m}-{y}.pdf')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
