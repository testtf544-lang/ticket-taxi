from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter
import io, os

app = Flask(__name__)

# ── Font registration ──────────────────────────────────────────
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OCR-B.ttf')
try:
    pdfmetrics.registerFont(TTFont('OCRB', FONT_PATH))
except:
    pass

# ⚠️ LES NOUVELLES COORDONNÉES EXACTES (Calculées grâce à ta capture) ⚠️
Y_DATE     = 625
Y_HEURE    = 610
Y_DISTANCE = 595

Y_CHARGE   = 495
Y_TTC      = 470
Y_TVA      = 445
Y_HT       = 430

def build_ticket_overlay(date, depart, arrivee, distance, prix_ttc):
    ht  = prix_ttc / 1.10
    tva = prix_ttc - ht

    original_path = os.path.join(os.path.dirname(__file__), 'original.pdf')
    reader = PdfReader(original_path)
    page = reader.pages[0]
    
    page_w = float(page.mediabox.width)
    page_h = float(page.mediabox.height)

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    def hide_and_write(text, x, y, width, height=12, font='OCRB', size=6.5, align='right'):
        """Dessine un rectangle gris très clair (pour cacher) puis le texte thermique"""
        c.saveState()
        
        # 1. Rectangle pour cacher les anciens chiffres (plus large pour être sûr)
        c.setFillColorRGB(0.98, 0.98, 0.98) 
        c.rect(x, y - 2, width, height, fill=1, stroke=0)
        
        # 2. Couleur Gris Thermique
        c.setFillColorRGB(0.22, 0.22, 0.22) 
        
        has_euro = '\u20AC' in text
        base_text = text.replace(' \u20AC', '')
        
        c.setFont(font, size)
        tw_base = c.stringWidth(base_text, font, size)
        tw_euro = 0
        
        if has_euro:
            c.setFont('Helvetica', size)
            tw_euro = c.stringWidth(' \u20AC', 'Helvetica', size)
            
        total_w = tw_base + tw_euro
        
        start_x = x
        if align == 'right':
            # On colle tout bien à droite du rectangle blanc
            start_x = x + width - total_w
            
        # Effet gras thermique (double tracé avec micro décalage)
        c.setFont(font, size)
        c.drawString(start_x, y, base_text)
        c.drawString(start_x + 0.15, y, base_text) 
        
        if has_euro:
            c.setFont('Helvetica', size)
            c.drawString(start_x + tw_base, y, ' \u20AC')
            c.drawString(start_x + tw_base + 0.15, y, ' \u20AC')
            
        c.restoreState()

    # --- CACHER ET REMPLACER ---
    
    # Bloc du Haut (Date, Heure, Distance) - x reculé à 70 et width augmenté à 85 pour couvrir largement
    hide_and_write(date, x=70, y=Y_DATE, width=85)
    
    hide_and_write(depart, x=45, y=Y_HEURE, width=30, align='left')
    hide_and_write(arrivee, x=115, y=Y_HEURE, width=40, align='right')
    
    hide_and_write(f"{distance} km", x=70, y=Y_DISTANCE, width=85)
    
    # Bloc du Bas (Prix)
    hide_and_write(f"2.94 \u20AC", x=90, y=Y_CHARGE, width=65)
    
    # TOTAL TTC (Font plus grand)
    c.setFont('OCRB', 11)
    hide_and_write(f"{prix_ttc:.2f} \u20AC", x=70, y=Y_TTC, width=85, size=11)
    # Effet Extra-Gras pour le TTC
    hide_and_write(f"{prix_ttc:.2f} \u20AC", x=70.4, y=Y_TTC, width=0, size=11, align='left') 
    
    # TVA & HT
    hide_and_write(f"{tva:.2f} \u20AC", x=90, y=Y_TVA, width=65)
    hide_and_write(f"{ht:.2f} \u20AC", x=90, y=Y_HT, width=65)

    c.save()
    packet.seek(0)

    # Fusion des calques
    new_pdf = PdfReader(packet)
    overlay_page = new_pdf.pages[0]
    page.merge_page(overlay_page)
    
    output = PdfWriter()
    output.add_page(page)
    
    buf = io.BytesIO()
    output.write(buf)
    buf.seek(0)
    return buf


HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ticket Taxi — Overlay Mod</title>
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
  <h1>🧾 Ticket Taxi (Overlay)</h1>
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
    <button type="submit">⬇ Télécharger</button>
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

    buf = build_ticket_overlay(
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
