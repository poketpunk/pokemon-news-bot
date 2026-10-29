import os
import random
import re
from bs4 import BeautifulSoup
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT")

SOURCES = [
    {"name": "PokeBeach", "url": "https://www.pokebeach.com/"},
    {"name": "PokeGuardian", "url": "https://www.pokeguardian.com/"},
]


def translate_text(text):
  if not text:
    return ""
  try:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "ru",
        "dt": "t",
        "q": text[:4000],
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
      data = response.json()
      return "".join([item[0] for item in data[0] if item[0]])
  except Exception as e:
    print(f"Ошибка перевода: {e}")
  return text


def get_latest_news_from_source(source):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    print(f"Проверяю источник: {source['name']} ({source['url']})")
    response = requests.get(source["url"], headers=headers, timeout=15)
    if response.status_code != 200:
      return None

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article") or soup.find("div", class_="post")
    if not article:
      return None

    title_tag = article.find("h2") or article.find("h1") or article.find("a")
    if not title_tag:
      return None

    link_tag = title_tag.find("a") if title_tag.name != "a" else title_tag
    if not link_tag or not link_tag.has_attr("href"):
      return None

    link = link_tag["href"]
    title = link_tag.get_text(strip=True)
    if not title:
      title = title_tag.get_text(strip=True)

    return {"name": source["name"], "title": title, "link": link}
  except Exception as e:
    print(f"Ошибка при парсинге {source['name']}: {e}")
    return None


def run():
  print("--- НАЧАЛО РАБОТЫ СКРИПТА (ОПРОС ВСЕХ ИСТОЧНИКОВ) ---")
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Ошибка: Не заданы секреты TG_TOKEN или TG_CHAT!")
    return

  last_link = ""
  if os.path.exists("last_news.txt"):
    with open("last_news.txt", "r", encoding="utf-8") as f:
      last_link = f.read().strip()

  target_news = None

  # Проходим по ВСЕМ источникам
  for source in SOURCES:
    news = get_latest_news_from_source(source)
    if news and news["link"]:
      print(f"Найдена последняя новость на {news['name']}: {news['link']}")
      # Если эта новость еще не публиковалась — берем её в работу!
      if news["link"] != last_link:
        target_news = news
        break
      else:
        print(f"ℹ️ Эта новость с {news['name']} уже была опубликована.")

  if not target_news:
    print("ℹ️ Новых новостей ни на одном из сайтов нет.")
    return

  title = target_news["title"]
  link = target_news["link"]

  print(f"🔥 Публикуем новую статью: {title}")
  print(f"Ссылка: {link}")

  print("Загружаю полный текст статьи...")
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  full_text = ""
  try:
    art_response = requests.get(link, headers=headers, timeout=15)
    if art_response.status_code == 200:
      art_soup = BeautifulSoup(art_response.text, "html.parser")
      content_div = (
          art_soup.find("div", class_="entry-content")
          or art_soup.find("div", class_="post-content")
          or art_soup.find("article")
      )
      if content_div:
        paragraphs = content_div.find_all("p")
        full_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
  except Exception as e:
    print(f"Ошибка загрузки текста статьи: {e}")

  if not full_text:
    full_text = "Свежие подробности читайте в источнике!"

  print("Перевожу заголовок и текст на русский язык...")
  ru_title = translate_text(title)
  ru_body = translate_text(full_text)

  if len(ru_body) > 3000:
    ru_body = ru_body[:3000] + "...\n\n*(Текст сокращен, читайте далее в источнике)*"

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

  post_text = (
      f"{random.choice(intros)}\n\n📌 **{ru_title}**\n\n{ru_body}\n\n{random.choice(outros)}\n\n🔗"
      f" [Читать полный источник]({link})"
  )

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
    print("✅ УСПЕШНО! Новость опубликована.")
    with open("last_news.txt", "w", encoding="utf-8") as f:
      f.write(link)
  else:
    print("❌ Ошибка отправки сообщения в Telegram!")


run()
