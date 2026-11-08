import json, os, smtplib, ssl, glob
from email.message import EmailMessage

SENDER_EMAIL = "rabioul.andriod@gmail.com"  
RECEIVER_EMAIL = "sk.rabioul@gmail.com" 

PROGRESS_FILE = "progress.json"

# 1. Load the bookmark tracker (or start fresh if it doesn't exist)
progress = {}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

# 2. Find all .jsonl files inside the books folder and its subfolders
filepaths = glob.glob("books/**/*.jsonl", recursive=True)
filepaths.sort() # Keeps order consistent

email_body = "Here are your daily book snippets!\n\n"
updated_progress = {}

# 3. Loop through every file and pick the current snippet
for filepath in filepaths:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
        
    if not lines:
        continue # Skip empty files
        
    # Get the last index we used for this file, or 0 if it's a new file
    current_index = progress.get(filepath, 0)
    
    # If we reached the end of the file, loop back to the beginning
    if current_index >= len(lines):
        current_index = 0
        
    # Pick the snippet
    s = json.loads(lines[current_index])
    
    # Add to email body
    email_body += f"📖 {s['book']}\n"
    email_body += f"“{s['text']}”\n"
    email_body += f"— Page {s['page']} of {s['total_pages']}\n"
    email_body += "-" * 40 + "\n\n"
    
    # Save the NEXT index for tomorrow
    updated_progress[filepath] = current_index + 1

# 4. Save the new progress bookmarks
with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
    json.dump(updated_progress, f, indent=2)

# 5. Send Email
if len(updated_progress) == 0:
    raise SystemExit("No snippets found in any files.")

msg = EmailMessage()
msg.set_content(email_body)
msg["Subject"] = f"Your Daily Book Mix ({len(updated_progress)} books)"
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL

password = os.environ["GMAIL_APP_PASSWORD"]
context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(SENDER_EMAIL, password)
    server.send_message(msg)

print(f"Email sent with {len(updated_progress)} snippets!")
