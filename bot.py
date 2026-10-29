import os
import random
import re
from bs4 import BeautifulSoup
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT")

MAIN_URL = "https://www.pokebeach.com/"


def translate_text(text):
  if not text:
    return ""
  try:
    # Используем прямой общедоступный эндпоинт переводчика Google
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "ru",
        "dt": "t",
        "q": text[:4000],  # ограничение на длину куска
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
      data = response.json()
      # Собираем переведенные предложения обратно в текст
      translated_text = "".join([item[0] for item in data[0] if item[0]])
      return translated_text
  except Exception as e:
    print(f"Ошибка перевода: {e}")
  return text


def run():
  print("--- НАЧАЛО РАБОТЫ СКРИПТА (СТАБИЛЬНЫЙ ПЕРЕВОД) ---")
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Ошибка: Не заданы секреты TG_TOKEN или TG_CHAT!")
    return

  last_link = ""
  if os.path.exists("last_news.txt"):
    with open("last_news.txt", "r", encoding="utf-8") as f:
      last_link = f.read().strip()

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    print(f"Загружаю главную страницу: {MAIN_URL}")
    response = requests.get(MAIN_URL, headers=headers, timeout=15)
    if response.status_code != 200:
      print("❌ Сайт не отдал главную страницу.")
      return

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    if not article:
      print("❌ Не удалось найти статьи на странице.")
      return

    title_tag = article.find("h2") or article.find("h1")
    if not title_tag or not title_tag.find("a"):
      print("❌ Не найден заголовок статьи.")
      return

    link = title_tag.find("a")["href"]
    orig_title = title_tag.get_text(strip=True)

    print(f"Найдена свежая ссылка: {link}")

    if link == last_link:
      print("ℹ️ Эта новость уже публиковалась ранее. Пропускаем.")
      return

    print("Загружаю полный текст статьи...")
    art_response = requests.get(link, headers=headers, timeout=15)
    full_text = ""
    if art_response.status_code == 200:
      art_soup = BeautifulSoup(art_response.text, "html.parser")
      content_div = art_soup.find("div", class_="entry-content")
      if content_div:
        paragraphs = content_div.find_all("p")
        full_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])

    if not full_text:
      full_text = "Свежие подробности читайте в источнике!"

  except Exception as e:
    print(f"❌ Ошибка при парсинге: {e}")
    return

  print("Перевожу заголовок и текст на русский язык...")
  ru_title = translate_text(orig_title)
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
    print("✅ УСПЕШНО! Переведенный пост отправлен в Telegram.")
    with open("last_news.txt", "w", encoding="utf-8") as f:
      f.write(link)
  else:
    print("❌ Ошибка отправки сообщения в Telegram!")


run()
