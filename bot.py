import os
import random
import re
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT")

RSS_FEEDS = [
    "https://www.pokebeach.com/feed",
    "https://www.pokeguardian.com/feed",
]


def clean_html(raw_html):
  cleanr = re.compile("<.*?>")
  return re.sub(cleanr, "", raw_html).strip()


def generate_blogger_post(title, summary, link):
  intros = [
      "🚨 **НАРОД, ТУТ ЖЕСТЬ В МИРЕ ПОКЕМОНОВ!**",
      "🔥 **СВЕЖИЙ ИНФОПОВОД ПОДЪЕХАЛ!**",
      "⚡ **СРОЧНО В НОМЕР: ВЫ ВИДЕЛИ ЭТИ НОВОСТИ?!**",
      "😱 **СРАЗУ К ДЕЛУ — ТУТ ТАКОЕ ПРОИЗОШЛО...**",
  ]
  outros = [
      (
          "💬 **Что думаете по этому поводу?** Обсуждаем в комментариях под этим"
          " постом! 👇"
      ),
      (
          "👇 **Пишите свое мнение в чате:** это полный зашквар или жесткий"
          " хайп?"
      ),
      (
          "🔥 Ставьте реакцию, если следите за этими новостями вместе со мной!"
      ),
  ]

  intro = random.choice(intros)
  outro = random.choice(outros)

  clean_summary = clean_html(summary)
  if len(clean_summary) > 300:
    clean_summary = clean_summary[:300] + "..."

  return (
      f"{intro}\n\n📌 **{title}**\n\n{clean_summary}\n\n{outro}\n\n🔗 [Читать"
      f" полный источник]({link})"
  )


def run():
  print("--- НАЧАЛО РАБОТЫ СКРИПТА ---")
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print(
        "❌ Ошибка: Не заданы секреты TG_TOKEN или TG_CHAT в Settings ->"
        " Secrets!"
    )
    return

  # Читаем историю
  last_link = ""
  if os.path.exists("last_news.txt"):
    with open("last_news.txt", "r", encoding="utf-8") as f:
      last_link = f.read().strip()

  latest_entry = None
  for feed_url in RSS_FEEDS:
    try:
      feed = feedparser.parse(feed_url)
      if feed.entries:
        latest_entry = feed.entries[0]
        break
    except Exception as e:
      print(f"Ошибка парсинга {feed_url}: {e}")

  if not latest_entry:
    print("❌ Не удалось получить новости из RSS.")
    return

  title = latest_entry.title
  summary = latest_entry.get("summary", "")
  link = latest_entry.link

  print(f"Найдена новость: {title}")
  print(f"Ссылка: {link}")

  if link == last_link:
    print("ℹ️ Эта новость уже публиковалась ранее. Пропускаем.")
    return

  post_text = generate_blogger_post(title, summary, link)

  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": post_text,
      "parse_mode": "Markdown",
      "disable_web_page_preview": False,
  }

  response = requests.post(url, json=payload)
  print(f"Ответ Telegram API: {response.status_code}")
  print(f"Текст ответа: {response.text}")

  if response.status_code == 200:
    print("✅ УСПЕШНО! Новость отправлена в Telegram.")
    with open("last_news.txt", "w", encoding="utf-8") as f:
      f.write(link)
  else:
    print("❌ Ошибка отправки сообщения в Telegram!")


run()
