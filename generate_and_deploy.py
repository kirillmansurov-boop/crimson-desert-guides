import os
import subprocess
import datetime

def run(cmd, cwd="."):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

OLLAMA_MODEL = "qwen2.5:14b"
THEME = "PaperMod"

def generate_guide(title, prompt_suffix=""):
    md_slug = title.lower().replace(" ", "-") + ".md"
    md_path = f"content/posts/{md_slug}"

    prompt = f"""
Ты — эксперт по Crimson Desert (игра вышла 19 марта 2026 от Pearl Abyss).
Напиши подробный гайд на русском языке в стиле игрового блога.
Заголовок: {title}
Объём: 1800–3000 слов.
Структура: введение → основные механики → советы → подводные камни → итог.
Используй markdown: ##, ###, списки, **жирный**, `код`, > цитаты.
{prompt_suffix}
"""

    # Запрос к Ollama (предполагаем, что сервер ollama запущен)
    result = subprocess.run(
        f'ollama run {OLLAMA_MODEL} "{prompt}"',
        shell=True, capture_output=True, text=True
    )
    text = result.stdout.strip()

    # Добавляем front matter
    front = f"""---
title: "{title}"
date: {datetime.date.today().isoformat()}
draft: false
description: "Гайд по Crimson Desert — {title.lower()}"
tags: ["crimson-desert", "гайд", "советы"]
---
"""
    full_md = front + text

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"Сгенерирован → {md_path}")

def main():
    # Пример: генерируем новый гайд
    generate_guide(
        "Как быстро прокачать репутацию с фракциями в Crimson Desert",
        "Фокус на ранней игре, первые 10–20 часов."
    )

    # Билд
    run("hugo --minify")

    # Git + push
    run("git add .")
    run(f'git commit -m "Auto: новый гайд {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}"')
    run("git push origin main")

    print("Готово! Cloudflare Pages должен уже собирать новую версию.")

if __name__ == "__main__":
    main()