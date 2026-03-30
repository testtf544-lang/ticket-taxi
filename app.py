from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
import io, os

app = Flask(__name__)

# ── Font setup ──────────────────────────────────────────
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OCR-B.ttf')

# ── 1. KBER L-KTABA (FONT SIZE) ─────────────────────────
SIZE_NORMAL = 30
SIZE_TTC    = 44  

# ── 2. COORDONNÉES X (Les X dyalek) ─────────────────────
X_DATE         = 707  
X_DISTANCE     = 625  
X_TTC          = 676  
X_TVA_HT       = 675  

X_DEPART       = 198  
X_ARRIVEE      = 580  

# ── 3. COORDONNÉES Y (Les Y dyalek) ─────────────────────
Y_DATE     = 350
Y_HEURE    = 385
Y_DISTANCE = 419

# ⚠️ Mola7ada: Ila bano lik l-ar9am hbtou lte7t bzaf b sbaab l-marge, n9ess mn had 823 (dir 810 matalan)
Y_TTC      = 817
Y_TVA      = 902
Y_HT       = 942

def build_ticket_image(date_str, depart, arrivee, distance, prix_ttc):
    ht  = prix_ttc / 1.10
    tva = prix_ttc - ht

    # 1. Ouvrir l'image nettoyée
    img_path = os.path.join(os.path.dirname(__file__), 'template.png')
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

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
        elif align == 'left':
            start_x = x

        draw.text((start_x, y), text, font=fnt, fill=COLOR_INK)
        draw.text((start_x + 1, y), text, font=fnt, fill=COLOR_INK)

    def write_stretched_text(text, x, y, fnt=font_ttc):
        """
        Fonction mrigla bash l-ktaba d l-TTC ma tt9te3sh mn l-te7t
        """
        bbox = draw.textbbox((0, 0), text, font=fnt)
        w = bbox[2] - bbox[0]
        
        # HNA L-7EL: Khedina l-hauteur l-kbira (bbox[3]) w zedna 25 pixels d l-marge lte7t
        safe_h = bbox[3] + 25 
        
        # Créer une image temporaire kbeeera bash mayt9te3 walo
        temp_img = Image.new('RGBA', (w + 10, safe_h), (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Écrire le texte (N9i w lissé)
        temp_draw.text((0, 0), text, font=fnt, fill=COLOR_INK)
        
        # ÉTIRER L'IMAGE (1.3)
        new_h = int(safe_h * 1.3) 
        stretched_img = temp_img.resize((w + 10, new_h), resample=Image.Resampling.LANCZOS)
        
        # Coller l'image étirée sur le ticket
        start_x = x - w
        img.paste(stretched_img, (start_x, y), mask=stretched_img)

    # --- ÉCRITURE DIRECTE SUR L'IMAGE ---
    write_text(date_str, X_DATE, Y_DATE, align='right')
    write_text(depart, X_DEPART, Y_HEURE, align='left')
    write_text(arrivee, X_ARRIVEE, Y_HEURE, align='left')
    write_text(f"{distance}", X_DISTANCE, Y_DISTANCE, align='right') 
    
    write_stretched_text(f"{prix_ttc:.2f}", X_TTC, Y_TTC)
    
    write_text(f"{tva:.2f}", X_TVA_HT, Y_TVA, align='right')
    write_text(f"{ht:.2f}", X_TVA_HT, Y_HT, align='right')

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
    port = int(os.environ.get('PORT', 5001)) 
    app.run(host='0.0.0.0', port=port)
