from flask import Flask, request, send_file, render_template_string
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

app = Flask(__name__)

# ── Font registration ──────────────────────────────────────────
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OCR-B.ttf')
pdfmetrics.registerFont(TTFont('OCRB', FONT_PATH))

# ── Ticket dimensions (58mm paper) ────────────────────────────
W       = 58 * mm          # page width
MARGIN  = 3 * mm           # left/right margin
TW      = W - 2 * MARGIN   # text width = 52mm

# ── Sizes ──────────────────────────────────────────────────────
FS      = 6.5              # body font size (pt)
FS_TTL  = 11               # TOTAL TTC font size (pt)
LH      = FS * 1.35        # line height (pt)

# ── Gaps between sections (pt) ────────────────────────────────
G_BIG   = 5.5   # major section gap
G_MED   = 3.5   # medium gap
G_SML   = 1.5   # small gap (before/after dots)
G_TINY  = 1.0   # tiny gap


def build_ticket(date, depart, arrivee, distance, prix_ttc):
    """Generate the ticket PDF, return bytes."""
    ht  = prix_ttc / 1.10
    tva = prix_ttc - ht

    # ── Pre-calculate total height ─────────────────────────────
    # Count lines + gaps to set exact page height
    PAGE_H = (
        MARGIN              # top
        + LH * 1.5          # TAXI (2 lines, tighter)
        + G_BIG
        + LH * 4            # stat/immat/commune/mantes
        + G_BIG
        + LH * 4            # date/depart/distance/lieu depart
        + G_SML + LH        # dots
        + G_SML + LH        # lieu arrivée
        + G_SML + LH        # dots
        + G_MED + LH        # prise en charge
        + G_TINY + LH*1.6   # TOTAL TTC (taller)
        + LH * 2            # TVA / HT
        + G_BIG
        + LH * 4            # tarif minimum
        + G_BIG
        + LH * 6            # adresse
        + G_BIG
        + LH                # nom client
        + G_MED + LH        # dots
        + LH                # adresse client
        + G_SML + LH        # dots
        + LH                # signature client
        + LH * 2            # signature space
        + G_BIG
        + LH                # exemplaire chauffeur
        + MARGIN            # bottom
    )

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, PAGE_H))
    c.setAuthor('Taxi Elidrissi Hicham')

    # cursor starts from TOP, we subtract as we go down
    y = PAGE_H - MARGIN

    def font(size=FS, bold=False):
        c.setFont('OCRB', size)

    def center(text, size=FS, y_pos=None):
        nonlocal y
        pos = y_pos if y_pos is not None else y
        c.setFont('OCRB', size)
        tw = c.stringWidth(text, 'OCRB', size)
        c.drawString((W - tw) / 2, pos, text)

    def left(text, size=FS, x=None, y_pos=None):
        nonlocal y
        pos = y_pos if y_pos is not None else y
        c.setFont('OCRB', size)
        c.drawString(x if x is not None else MARGIN, pos, text)

    def right(text, size=FS, y_pos=None):
        nonlocal y
        pos = y_pos if y_pos is not None else y
        c.setFont('OCRB', size)
        tw = c.stringWidth(text, 'OCRB', size)
        c.drawString(W - MARGIN - tw, pos, text)

    def row(label, value, size=FS):
        """Left label + right value on same line."""
        left(label, size)
        right(value, size)

    def dots():
        """Draw a full-width dots line."""
        c.setFont('OCRB', FS)
        # fill width with dots spaced ~2.2pt apart
        dot_w = c.stringWidth('. ', 'OCRB', FS)
        x = MARGIN
        while x + dot_w < W - MARGIN:
            c.drawString(x, y, '.')
            x += dot_w

    def nl(gap=LH):
        nonlocal y
        y -= gap

    # ── ① HEADER ──────────────────────────────────────────────
    center('TAXI');                 nl()
    center('ELIDRISSI HICHAM');     nl(G_BIG + LH)

    # ── ② STATION INFO ────────────────────────────────────────
    row('N\u00B0 Stat.:',  '1');           nl(LH)
    row('N\u00B0 Immat.:', 'FK-309-AA');   nl(LH)
    left('Commune de rattachement:');       nl(LH)

    c.setFont('OCRB', FS)
    # MANTES LA JOLIE — bold simulation: draw twice offset by 0.2pt
    text_mantes = 'MANTES LA JOLIE'
    tw = c.stringWidth(text_mantes, 'OCRB', FS)
    xm = (W - tw) / 2
    c.drawString(xm,       y, text_mantes)
    c.drawString(xm + 0.3, y, text_mantes)  # bold effect
    nl(G_BIG + LH)

    # ── ③ DATE BLOCK ──────────────────────────────────────────
    row('Date:', date);                             nl(LH)
    left(f'D\u00e9part:{depart}');
    right(f'Arriv\u00e9e:{arrivee}');               nl(LH)
    row('Distance:', f'{distance} km');             nl(LH)
    left('Lieu d\u00e9part:');                      nl(G_SML + LH)

    # ── ④ DOTS DÉPART ─────────────────────────────────────────
    dots();                                         nl(G_SML + LH)

    # ── ⑤ LIEU ARRIVÉE ────────────────────────────────────────
    left('Lieu arriv\u00e9e:');                     nl(G_SML + LH)

    # ── ⑥ DOTS ARRIVÉE ────────────────────────────────────────
    dots();                                         nl(G_MED + LH)

    # ── ⑦ PRISE EN CHARGE ────────────────────────────────────
    row('Prise en charge', f'2.94 \u20AC');         nl(G_TINY + LH)

    # ── ⑧ TOTAL TTC — larger, bold ───────────────────────────
    c.setFont('OCRB', FS_TTL)
    label_ttc = 'TOTAL TTC'
    value_ttc = f'{prix_ttc:.2f} \u20AC'
    # bold effect by drawing twice
    c.drawString(MARGIN,       y, label_ttc)
    c.drawString(MARGIN + 0.4, y, label_ttc)
    tw_ttc = c.stringWidth(value_ttc, 'OCRB', FS_TTL)
    c.drawString(W - MARGIN - tw_ttc,       y, value_ttc)
    c.drawString(W - MARGIN - tw_ttc + 0.4, y, value_ttc)
    nl(G_TINY + LH * 1.55)

    # ── ⑨ TVA / HT ───────────────────────────────────────────
    row('Total TVA 10.00%', f'{tva:.2f} \u20AC');  nl(LH)
    row('Total HT',          f'{ht:.2f} \u20AC');  nl(G_BIG + LH)

    # ── ⑩ TARIF MINIMUM ──────────────────────────────────────
    left('Le tarif minimum, suppl.');               nl(LH)
    left("inclus, susceptible d'\u00eatre");        nl(LH)
    left('per\u00e7u pour une course est');         nl(LH)
    left('fix\u00e9 \u00e0  8.00 \u20AC');          nl(G_BIG + LH)

    # ── ⑪ ADRESSE ────────────────────────────────────────────
    left('Adresse de r\u00e9clamation:');           nl(LH)
    left('  Prefecture des Yvelines');              nl(LH)
    left('Bureau de la reglementation');            nl(LH)
    left('    General 1rue jean');                  nl(LH)
    left('  Houdon 78010 Versailles');              nl(LH)
    left('       Cedex');                           nl(G_BIG + LH)

    # ── ⑫ NOM CLIENT ─────────────────────────────────────────
    left('Nom client:');                            nl(G_MED + LH)
    dots();                                         nl(LH)

    # ── ⑬ ADRESSE CLIENT ─────────────────────────────────────
    left('Adresse client:');                        nl(G_SML + LH)
    dots();                                         nl(LH)

    # ── ⑭ SIGNATURE ──────────────────────────────────────────
    left('Signature client:');                      nl(LH * 2.5)

    # ── ⑮ FOOTER ─────────────────────────────────────────────
    center('Exemplaire chauffeur')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ticket Taxi — Elidrissi Hicham</title>
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
        border-radius:8px;font-size:14px;transition:border-color .2s;}
  input:focus{border-color:#6366f1;outline:none;box-shadow:0 0 0 3px rgba(99,102,241,.15);}
  .full{margin-bottom:20px;}
  button{background:#4f46e5;color:white;font-weight:700;width:100%;
         padding:14px;border:none;border-radius:10px;cursor:pointer;font-size:15px;
         letter-spacing:.3px;transition:background .2s;}
  button:hover{background:#4338ca;}
  .note{margin-top:12px;font-size:11px;color:#9ca3af;text-align:center;}
</style>
</head>
<body>
<div class="card">
  <h1>🧾 Ticket Taxi (58mm)</h1>
  <p>Remplissez les informations de la course et téléchargez le reçu PDF.</p>

  <form method="POST" action="/generate">
    <div class="grid">
      <div>
        <label>Date</label>
        <input name="date" type="date" value="2026-02-23" required>
      </div>
      <div>
        <label>Distance (km)</label>
        <input name="distance" type="number" step="0.1" value="64.8" required>
      </div>
    </div>
    <div class="grid">
      <div>
        <label>Heure Départ</label>
        <input name="depart" type="time" value="12:54" required>
      </div>
      <div>
        <label>Heure Arrivée</label>
        <input name="arrivee" type="time" value="13:52" required>
      </div>
    </div>
    <div class="full">
      <label>Prix Total TTC (€)</label>
      <input name="prix" type="number" step="0.01" value="135.24" required>
    </div>
    <button type="submit">⬇ Télécharger le Ticket PDF</button>
  </form>
  <p class="note">PDF généré directement en Python — rendu pixel-perfect.</p>
</div>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/generate', methods=['POST'])
def generate():
    # Parse form
    raw_date = request.form['date']          # "2026-02-23"
    y, m, d  = raw_date.split('-')
    date_str = f'{d}/{m}/{y}'

    depart   = request.form['depart']
    arrivee  = request.form['arrivee']
    distance = request.form['distance']
    prix_ttc = float(request.form['prix'])

    buf = build_ticket(date_str, depart, arrivee, distance, prix_ttc)

    filename = f'Ticket_{d}-{m}-{y}.pdf'
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
