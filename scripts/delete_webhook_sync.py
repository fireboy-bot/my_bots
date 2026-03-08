import urllib.request
import sys, os
# Ensure project root is in sys.path
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
from dotenv import load_dotenv
load_dotenv(os.path.join(proj_root, ".env"))
from config import BOT_TOKEN
def main():
    if not BOT_TOKEN:
        print("No BOT_TOKEN configured")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            print(r.read().decode('utf-8'))
    except Exception as e:
        print("ERR", e)

if __name__ == '__main__':
    main()

