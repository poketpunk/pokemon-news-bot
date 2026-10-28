import os
import re
import random
import requests
import feedparser

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT")

RSS_FEEDS = [
    "https://www.pokebeach.com/feed",
    "https://www.pokeguardian.com/feed"
]

LAST_NEWS_FILE = "last_news.txt"


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()


def get_last_posted_link():
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_last_posted_link(link):
    with open(LAST_NEWS_FILE, "w", encoding="utf-8") as f:
        f.write(str(link))


def generate_blogger_post(title, summary, link):
    intros = [
        "🚨 **НАРОД, ТУТ ЖЕСТЬ В МИРЕ ПОКЕМОНОВ!**",
        "🔥 **СВЕЖИЙ ИНФОПОВОД ПОДЪЕХАЛ!**",
        "⚡ **СРОЧНО В НОМЕР: ВЫ ВИДЕЛИ ЭТИ НОВОСТИ?!**",
        "😱 **СРАЗУ К ДЕЛУ — ТУТ ТАКОЕ ПРОИЗОШЛО...**"
    ]
    
    outros = [
        "💬 **Что думаете по этому поводу?** Обсуждаем в комментариях под этим постом! 👇",
        "👇 **Пишите свое мнение в чате:** это полный зашквар или жесткий хайп?",
        "🔥 Ставьте реакцию, если следите за этими новостями вместе со мной!"
    ]
    
    intro = random.choice(intros)
    outro = random.choice(outros)
    
    clean_summary = clean_html(summary)
    if len(clean_summary) > 300:
        clean_summary = clean_summary[:300] + "..."
        
    return (
        f"{intro}\n\n"
        f"📌 **{title}**\n\n"
        f"{clean_summary}\n\n"
        f"{outro}\n\n"
        f"🔗 [Читать полный источник]({link})"
    )


def check_and_post_news():
    last_link = get_last_posted_link()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue
                
            latest = feed.entries[0]
            link = latest.link
            
            if link == last_link:
                continue
                
            title = latest.title
            summary = latest.get("summary", latest.get("description", ""))
            
            post_text = generate_blogger_post(title, summary, link)
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": post_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            
            res = requests.post(telegram_url, json=payload)
            if res.status_code == 200:
                print(f"✅ Новость опубликована: {title}")
                save_last_posted_link(link)
                return True
            else:
                print(f"❌ Ошибка отправки: {res.text}")
                
        except Exception as e:
            print(f"Ошибка RSS: {e}")
            
    return False


if __name__ == "__main__":
    check_and_post_news()
