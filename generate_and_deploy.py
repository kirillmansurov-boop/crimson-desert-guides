import os
import subprocess
import datetime

def run(cmd_list, cwd="."):
    """Универсальная функция запуска команд (без shell=True)"""
    print(f"> {' '.join(cmd_list)}")
    try:
        result = subprocess.run(
            cmd_list,
            check=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print("stderr:", result.stderr.strip())
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении {' '.join(cmd_list)}")
        print("Код выхода:", e.returncode)
        if e.stdout:
            print("stdout:", e.stdout.strip())
        if e.stderr:
            print("stderr:", e.stderr.strip())
        raise

OLLAMA_MODEL = "qwen2.5:14b"

def generate_guide(title, prompt_suffix=""):
    # Делаем slug чище
    slug = "".join(c for c in title.lower() if c.isalnum() or c in " -").replace(" ", "-")
    md_path = f"content/posts/{slug}.md"

    prompt = f"""
Ты — эксперт по Crimson Desert (игра вышла 19 марта 2026 от Pearl Abyss).
Напиши подробный гайд на русском языке в стиле игрового блога.
Заголовок: {title}
Объём: 1800–3000 слов.
Структура: введение → основные механики → советы → подводные камни → итог.
Используй markdown: ##, ###, списки, **жирный**, `код`, > цитаты.
{prompt_suffix}

Обязательно в самом начале ответа добавь front matter в формате YAML (--- ... ---), без лишнего текста перед ним. Включи:
- title: "{title}"
- date: {datetime.date.today().isoformat()}
- draft: false
- description: короткое описание 1–2 предложения
- tags: ["crimson-desert", "гайд", ...] — 3–5 тегов
- cover:
    image: "/images/{slug}.jpg"
    alt: "Иллюстрация к гайду {title}"
    hiddenInList: false
    hiddenInSingle: false

Сразу после front matter пиши полный текст гайда.
"""

    # Самый надёжный способ на Windows — использовать Popen + explicit encoding
    process = subprocess.Popen(
        ["ollama", "run", OLLAMA_MODEL, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",           # заменяет проблемные символы на ?
        text=True
    )

    stdout, stderr = process.communicate()  # ждём завершения

    if process.returncode != 0:
        print("Ollama вернула ошибку (код возврата не 0):")
        print(stderr)
        raise RuntimeError(f"Ollama failed with code {process.returncode}")

    full_output = (stdout or "").strip()

    if not full_output:
        print("Ollama вернула пустой ответ. Возможно, модель не загрузилась или промпт слишком большой.")
        return None

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_output)

    print(f"Сгенерирован → {md_path}")
    return md_path

def main():
    # Можно менять здесь для тестов
    title = "Где лучше фармить Abyss Artifacts в первые 10 часов Crimson Desert"
    suffix = "Фокус на локации, оптимальные маршруты, риски и награды."

    generate_guide(title, suffix)

    # Билд сайта
    run(["hugo", "--minify"])

    # Git-часть с проверкой изменений
    run(["git", "add", "."])

    status_result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        capture_output=True,
        text=True
    )

    if status_result.stdout.strip():
        commit_msg = f"Auto: новый гайд {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        run(["git", "commit", "-m", commit_msg])
        run(["git", "push", "origin", "main"])
        print(f"Изменения закоммичены и запушены: {commit_msg}")
    else:
        print("Нет новых изменений после генерации — commit и push пропущены.")

if __name__ == "__main__":
    main()