import json, os, smtplib, ssl, glob, html
from email.message import EmailMessage

SENDER_EMAIL = "rabioul.andriod@gmail.com"  
RECEIVER_EMAIL = "sk.rabioul@gmail.com" 

PROGRESS_FILE = "progress.json"

# 1. Discover all book folders
all_files = glob.glob("books/**/*.jsonl", recursive=True)
# Extract unique book directories (e.g., 'books/Genre/Book-Name')
book_dirs = sorted(list(set(os.path.dirname(f) for f in all_files)))

if not book_dirs:
    raise SystemExit("ERROR: No .jsonl files found.")

# 2. Load or initialize the Smart Progress Tracker
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)
else:
    # If starting fresh, initialize the sliding window and book tracking
    progress = {
        "window_start_index": 0,
        "books": {}
    }

total_books = len(book_dirs)
window_size = min(10, total_books)  # Max 10 books per day
start_idx = progress.get("window_start_index", 0)

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

snippets_found = 0

# 4. Loop through the sliding window of books
for i in range(window_size):
    book_idx = (start_idx + i) % total_books
    book_dir = book_dirs[book_idx]
    
    # Get all chapters for this book, sorted alphabetically
    chapters = sorted(glob.glob(f"{book_dir}/*.jsonl"))
    
    # Filter out empty files just in case
    valid_chapters = []
    for ch in chapters:
        with open(ch, "r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
            if lines:
                valid_chapters.append((ch, lines))
                
    if not valid_chapters:
        continue
        
    # Get current state for this book, or start at Chapter 1, Snippet 1
    if book_dir not in progress["books"]:
        progress["books"][book_dir] = {"chapter": 0, "snippet": 0}
        
    state = progress["books"][book_dir]
    ch_idx = state["chapter"]
    sn_idx = state["snippet"]
    
    # Safety check: if the chapter index is somehow out of bounds, reset
    if ch_idx >= len(valid_chapters):
        ch_idx = 0
        sn_idx = 0
        
    # Extract the snippet
    current_ch_file, current_lines = valid_chapters[ch_idx]
    s = json.loads(current_lines[sn_idx])
    
    # Format the snippet for HTML
    book_name = s.get('book', 'Unknown Book').split('_')[0].split(' - ')[0].strip()
    page = s.get('page')
    total = s.get('total_pages')
    page_text = f"Page {page}" + (f" of {total}" if total and total != "None" else "") if page and page != "None" else "Unknown Page"
    quote_text = html.escape(s.get('text', ''))
    
    html_body += f"""
    <div class="snippet-card">
        <div class="book-title">📖 {html.escape(book_name)} (Ch {ch_idx + 1})</div>
        <div class="quote">“{quote_text}”</div>
        <div class="meta">— {page_text}</div>
    </div>
    """
    snippets_found += 1
    
    # --- ADVANCE THE PROGRESS ---
    sn_idx += 1
    if sn_idx >= len(current_lines):
        # Finished this chapter, move to next chapter
        sn_idx = 0
        ch_idx += 1
        
    if ch_idx >= len(valid_chapters):
        # Finished the whole book! Remove record so it starts fresh next time
        print(f"Book completed: {book_dir}. Resetting progress.")
        del progress["books"][book_dir]
    else:
        # Save the new chapter/snippet position
        progress["books"][book_dir] = {"chapter": ch_idx, "snippet": sn_idx}

# 5. Advance the sliding window for tomorrow
progress["window_start_index"] = (start_idx + 1) % total_books

# 6. Save the updated progress.json
with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
    json.dump(progress, f, indent=2)

# Close HTML
html_body += """
    <div style="text-align: center; font-size: 12px; color: #9ca3af; margin-top: 30px;">
        Sent with ❤️ from your GitHub Actions bot.
    </div>
</div>
</body>
</html>
"""

if snippets_found == 0:
    raise SystemExit("No snippets found. Check your folders.")

# 7. Send Email
msg = EmailMessage()
msg["Subject"] = f"📚 Your Daily Book Mix ({snippets_found} snippets)"
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL
msg.set_content("Please enable HTML to view your daily book snippets.")
msg.add_alternative(html_body, subtype='html')

password = os.environ["GMAIL_APP_PASSWORD"]
context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, password)
        server.send_message(msg)
    print(f"✅ Email sent successfully with {snippets_found} snippets!")
except Exception as e:
    print(f"❌ FAILED TO SEND EMAIL. Error: {e}")
