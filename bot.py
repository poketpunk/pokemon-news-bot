import os
import random
import re
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT")

MAIN_URL = "https://www.pokebeach.com/"


def translate_to_russian(text):
  if not text:
    return ""
  try:
    # Переводим текст с английского на русский
    translated = GoogleTranslator(source="en", target="ru").translate(text)
    return translated
  except Exception as e:
    print(f"Ошибка перевода: {e}")
    return text  # Если вдруг сбой, возвращаем оригинал


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

  # Переводим заголовок и сам текст на русский язык
  ru_title = translate_to_russian(title)
  ru_summary = translate_to_russian(summary)

  if not ru_summary:
    ru_summary = "Свежие подробности читайте в источнике!"
  if len(ru_summary) > 300:
    ru_summary = ru_summary[:300] + "..."

  return (
      f"{intro}\n\n📌 **{ru_title}**\n\n{ru_summary}\n\n{outro}\n\n🔗 [Читать"
      f" полный источник]({link})"
  )


def run():
  print("--- НАЧАЛО РАБОТЫ СКРИПТА (ПЕРЕВОДЧИК) ---")
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
    print(f"Загружаю сайт: {MAIN_URL}")
    response = requests.get(MAIN_URL, headers=headers, timeout=15)
    if response.status_code != 200:
      print("❌ Сайт не отдал страницу.")
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
    title = title_tag.get_text(strip=True)

    excerpt_tag = article.find("div", class_="entry-content") or article.find(
        "p"
    )
    summary = excerpt_tag.get_text(strip=True) if excerpt_tag else ""

  except Exception as e:
    print(f"❌ Ошибка при парсинге сайта: {e}")
    return

  print(f"Найдена новость: {title}")
  print(f"Ссылка: {link}")

  if link == last_link:
    print("ℹ️ Эта новость уже публиковалась ранее. Пропускаем.")
    return

  # Генерируем пост (тут внутри происходит автоматический перевод)
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
    print("✅ УСПЕШНО! Новость переведена и отправлена в Telegram.")
    with open("last_news.txt", "w", encoding="utf-8") as f:
      f.write(link)
  else:
    print("❌ Ошибка отправки сообщения в Telegram!")


run()
