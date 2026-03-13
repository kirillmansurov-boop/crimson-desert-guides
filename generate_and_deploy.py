# generate_and_deploy.py
import os
import subprocess
import datetime
import argparse
import sys

# pip install python-slugify
try:
    from slugify import slugify
except ImportError:
    print("Ошибка: нужна библиотека 'python-slugify'")
    print("Установи: pip install python-slugify")
    sys.exit(1)

OLLAMA_MODEL = "qwen2.5:14b"
CONTENT_DIR = "content/posts"


def run(cmd_list, cwd=".", capture=True):
    print(f"> {' '.join(cmd_list)} (в {cwd})")
    try:
        result = subprocess.run(
            cmd_list,
            check=True,
            cwd=cwd,
            capture_output=capture,
            text=True,
            encoding="utf-8"
        )
        if result.stdout and result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr and result.stderr.strip():
            print("stderr:", result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"ОШИБКА: {' '.join(cmd_list)} → код {e.returncode}")
        if e.stdout: print("stdout:", e.stdout.strip())
        if e.stderr: print("stderr:", e.stderr.strip())
        raise


def generate_guide(title: str, prompt_suffix: str = "", strict: bool = True) -> str | None:
    os.makedirs(CONTENT_DIR, exist_ok=True)

    slug_base = slugify(title, max_length=60, lowercase=True, separator="-")
    if not slug_base:
        slug_base = "guide-" + datetime.date.today().strftime("%Y%m%d")
    slug = slug_base

    md_filename = f"{slug}.md"
    md_path = os.path.join(CONTENT_DIR, md_filename)

    if os.path.exists(md_path):
        print(f"Файл существует → пропуск: {md_path}")
        return None

    cover_image = f"/images/{slug}.jpg"
    today = datetime.date.today().isoformat()

    # СТРОГИЙ ПРОМПТ — минимизация галлюцинаций
    strict_rules = """
СТРОГО ЗАПРЕЩЕНО:
- Выдумывать любые локации, названия зон, боссов, NPC, предметов или механик, которых нет в реальной игре.
- Придумывать "Темные Туннели", "Пустоши", "Молоко и Мед", любые вымышленные названия.
- Говорить о бесконечном фарме мобов в одной зоне как в MMO.
- Если факт не подтверждён ниже — пиши "Информация по этому аспекту пока отсутствует в доступных источниках" вместо выдумывания.

СТРОГО РЕАЛЬНЫЕ ФАКТЫ о Crimson Desert (релиз 19 марта 2026, Pearl Abyss):
- Действие происходит на континенте Pywel.
- Нет классической системы уровней и XP-гринда.
- Прогресс идёт ТОЛЬКО через Abyss Artifacts (фрагменты Абисса).
- Abyss Artifacts дают:
  - Увеличение базовых статов (health, stamina, attack, defense и т.д.).
  - Разблокировку и улучшение узлов в уникальном skill tree персонажа.
  - Иногда новые активные/пассивные способности или улучшение skill chaining.
- Способы получения Abyss Artifacts (реальные в первые часы/дни):
  - Исследование открытого мира Pywel: hidden locations, landmarks, разрушаемые объекты, подозрительные элементы окружения.
  - Выполнение квестов (основной сюжет и побочные).
  - Победа над боссами и элитными врагами.
  - Находки в мире (в т.ч. связанные с Traces of the Abyss — следы Абисса, которые дают fast travel и часто рядом награды).
  - Другие способы exploration (без спойлеров).
- Статы артефактов могут быть положительными и отрицательными (RNG).
- Основной фокус в первые 10–20 часов: исследование Pywel, активация Traces of the Abyss, выполнение ранних квестов, поиск скрытых наград.
- Нет NPC по имени Virelia / Dome / Geodes в подтверждённых источниках на 13 марта 2026 — если это появится позже, обнови промпт.
"""

    prompt = f"""
Ты — эксперт по Crimson Desert (релиз 19 марта 2026 от Pearl Abyss). 
Отвечай ТОЛЬКО на основе реальных механик игры. Используй только факты из раздела СТРОГО РЕАЛЬНЫЕ ФАКТЫ выше.

{strict_rules}

Заголовок гайда: {title}
Объём: 1800–3000 слов (или меньше, если информации мало — лучше короче, но правдиво).
Структура: ## Введение → ## Основные механики Abyss Artifacts → ## Лучшие способы получения в первые 10 часов → ## Советы по оптимизации → ## Подводные камни и ошибки новичков → ## Итог.
Используй markdown: ##, ###, нумерованные/маркированные списки, **жирный**, *курсив*, > цитаты.
{prompt_suffix}

Обязательно начни ответ с front matter в формате YAML (--- ... ---), без любого текста перед ним. Поля ровно такие:
slug: "{slug}"
title: "{title}"
date: {today}
draft: false
description: Короткое описание 1–2 предложения на русском, без выдумок.
tags: ["crimson-desert", "гайд", "abyss-artifacts", "первые-часы", "прогресс"] — добавь 1–3 релевантных тега
cover:
  image: "{cover_image}"
  alt: "Иллюстрация к гайду {title}"
  hiddenInList: false
  hiddenInSingle: false

Сразу после front matter (без пустых строк!) пиши полный текст гайда на русском языке.
"""

    print(f"Генерация: {title}")
    print(f"Slug: {slug}")

    try:
        process = subprocess.Popen(
            ["ollama", "run", OLLAMA_MODEL],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            text=True
        )

        stdout, stderr = process.communicate(input=prompt, timeout=900)  # 15 мин — для длинных гайдов

        if process.returncode != 0:
            print("Ollama ошибка:", stderr or "<нет stderr>")
            return None

        full_output = (stdout or "").strip()

        if not full_output or len(full_output) < 800:
            print("Ответ слишком короткий или пустой.")
            return None

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full_output)

        print(f"Готово → {md_path} ({len(full_output):,} символов)")
        return md_path

    except subprocess.TimeoutExpired:
        print("Таймаут 15 мин — процесс убит.")
        process.kill()
        return None
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Генератор гайдов Crimson Desert + деплой")
    parser.add_argument("title", nargs="?", default=None, help="Заголовок гайда")
    parser.add_argument("--suffix", default="", help="Доп. инструкция в промпт")
    parser.add_argument("--strict", action="store_true", help="Максимально строгий режим (анти-галлюцинации)")
    args = parser.parse_args()

    if not args.title:
        title = "Где и как получать Abyss Artifacts в первые 10 часов Crimson Desert"
        suffix = "Опирайся только на реальное исследование Pywel, квесты, боссов и скрытые находки. Без выдуманных зон."
        print(f"Без заголовка → пример: {title}")
    else:
        title = args.title
        suffix = args.suffix

    generated = generate_guide(title, suffix, strict=args.strict)

    if not generated:
        print("Генерация провалилась → билд/деплой отменены.")
        return

    run(["hugo", "--minify"])

    run(["git", "add", "."])

    status = subprocess.run(["git", "status", "--porcelain=v1"], capture_output=True, text=True)

    if status.stdout.strip():
        commit_msg = f"Auto: гайд «{title}» ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
        run(["git", "commit", "-m", commit_msg])
        run(["git", "push", "origin", "main"])
        print("Запушено!")
    else:
        print("Нет изменений → commit/push пропущен.")


if __name__ == "__main__":
    main()