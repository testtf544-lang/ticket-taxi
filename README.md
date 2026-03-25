# 🧾 Ticket Taxi — Elidrissi Hicham

Générateur de tickets taxi 58mm — PDF pixel-perfect avec OCR-B.

## Deploy on Render.com (free)

1. Upload this folder to a GitHub repo
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click Deploy → get your URL!

## Run locally

```bash
pip install -r requirements.txt
python app.py
```
Open: http://localhost:5000
