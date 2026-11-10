import json, os, smtplib, ssl, glob, html
from email.message import EmailMessage

SENDER_EMAIL = "rabioul.andriod@gmail.com"  
RECEIVER_EMAIL = "sk.rabioul@gmail.com" 

PROGRESS_FILE = "progress.json"

# 1. Load bookmark tracker
progress = {}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

# 2. Find all .jsonl files
filepaths = glob.glob("books/**/*.jsonl", recursive=True)
filepaths.sort()

if not filepaths:
    raise SystemExit("ERROR: No .jsonl files found.")

# 3. Setup the HTML email structure
html_body = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 20px; color: #333; }
    .container { max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .header { text-align: center; font-size: 20px; font-weight: bold; color: #111; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0; }
    .snippet-card { margin-bottom: 25px; padding: 20px; background: #f9fafb; border-left: 4px solid #6366f1; border-radius: 4px; }
    .book-title { font-size: 14px; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
    .quote { font-size: 16px; line-height: 1.6; color: #1f2937; font-style: italic; margin-bottom: 15px; }
    .meta { font-size: 13px; color: #6b7280; font-weight: 500; }
</style>
</head>
<body>
<div class="container">
    <div class="header">📚 Your Daily Book Mix</div>
"""

updated_progress = {}
snippets_found = 0

# 4. Loop through files and build the HTML cards
for filepath in filepaths:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
            
        if not lines:
            continue
            
        current_index = progress.get(filepath, 0)
        if current_index >= len(lines):
            current_index = 0
            
        s = json.loads(lines[current_index])
        
        # Clean up the book title if it's messy (like the Markets in Profile one)
        book_name = s.get('book', 'Unknown Book').split('_')[0].split(' - ')[0].strip()
        
        # Clean up the page info (hide it if it's None)
        page = s.get('page')
        total = s.get('total_pages')
        if page and page != "None":
            page_text = f"Page {page}" + (f" of {total}" if total and total != "None" else "")
        else:
            page_text = "Unknown Page"
            
        # Escaping quotes in case the text has HTML tags inside
        quote_text = html.escape(s.get('text', ''))
        
        # Add card to HTML
        html_body += f"""
        <div class="snippet-card">
            <div class="book-title">📖 {html.escape(book_name)}</div>
            <div class="quote">“{quote_text}”</div>
            <div class="meta">— {page_text}</div>
        </div>
        """
        
        updated_progress[filepath] = current_index + 1
        snippets_found += 1
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

# Close HTML tags
html_body += """
    <div style="text-align: center; font-size: 12px; color: #9ca3af; margin-top: 30px;">
        Sent with ❤️ from your GitHub Actions bot.
    </div>
</div>
</body>
</html>
"""

# 5. Save progress
if snippets_found > 0:
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_progress, f, indent=2)
else:
    raise SystemExit("ERROR: No valid snippets were found to email.")

# 6. Send Email (Notice we are now using add_alternative for HTML)
msg = EmailMessage()
msg["Subject"] = f"📚 Your Daily Book Mix ({snippets_found} books)"
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL

# Fallback plain text for old email clients
msg.set_content("Please enable HTML to view your daily book snippets.")
# The beautiful HTML version
msg.add_alternative(html_body, subtype='html')

password = os.environ["GMAIL_APP_PASSWORD"]
context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, password)
        server.send_message(msg)
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ FAILED TO SEND EMAIL. Error: {e}")
