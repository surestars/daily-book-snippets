import json, random, os, smtplib, ssl
from email.message import EmailMessage

# --- CONFIGURATION ---
SENDER_EMAIL = "rabioul.andriod@gmail.com"  # <--- CHANGE THIS to your Gmail address
RECEIVER_EMAIL = "sk.rabioul@gmail.com" # <--- CHANGE THIS to where you want the email
DATA_FILE = "markets-in-profile.jsonl"

# --- LOAD SNIPPETS ---
snippets = []
with open(DATA_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            snippets.append(json.loads(line))

if not snippets:
    raise SystemExit("No snippets found in file.")

# --- PICK ONE ---
s = random.choice(snippets)
email_body = f"""
📖 {s['book']}
✍️ {s['author']}

“{s['text']}”

— Page {s['page']} of {s['total_pages']}
"""

# --- SEND EMAIL ---
msg = EmailMessage()
msg.set_content(email_body)
msg["Subject"] = f"Today's snippet: {s['book']}"
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL

password = os.environ["GMAIL_APP_PASSWORD"]
context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(SENDER_EMAIL, password)
    server.send_message(msg)

print(f"Email sent with snippet from page {s['page']}.")
