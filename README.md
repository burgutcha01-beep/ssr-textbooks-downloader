# SSR Textbooks Downloader 📚

Автоматическая загрузка учебников для 15 стран бывшего СССР.

## Страны

- 🇷🇺 Россия (Russian)
- 🇺🇦 Украина (Ukrainian)
- 🇧🇾 Беларусь (Belarusian)
- 🇰🇿 Казахстан (Kazakh)
- 🇺🇿 Узбекистан (Uzbek)
- 🇰🇬 Кыргызстан (Kyrgyz)
- 🇹🇯 Таджикистан (Tajik)
- 🇹🇲 Туркменистан (Turkmen)
- 🇦🇿 Азербайджан (Azerbaijani)
- 🇦🇲 Армения (Armenian)
- 🇬🇪 Грузия (Georgian)
- 🇲🇩 Молдова (Romanian)
- 🇱🇹 Литва (Lithuanian)
- 🇱🇻 Латвия (Latvian)
- 🇪🇪 Эстония (Estonian)

## Предметы (Subjects)

1. **history** — История страны / National History
2. **world_history** — Всемирная история / World History
3. **native_language** — Родной язык / Native Language
4. **reading** — Литература / Literature

## Классы (Grades)

- Grade 9
- Grade 10
- Grade 11

## Установка (Installation)

```bash
# Clone repository
git clone https://github.com/burgutcha01-beep/ssr-textbooks-downloader.git
cd ssr-textbooks-downloader

# Install dependencies
pip install -r requirements.txt
```

## Использование (Usage)

```bash
# Run downloader
python3 downloader.py
```

Транс успешно загруженных файлов будут распределены в папки по странам:

```
textbooks/
├── Russia/
│   ├── grade_9_history.pdf
│   ├── grade_9_world_history.pdf
│   ├── grade_9_native_language.pdf
│   ├── grade_9_reading.pdf
│   ├── grade_10_history.pdf
│   └── ...
├── Ukraine/
├── Belarus/
├── Kazakhstan/
└── ...
```

## Выходные файлы (Output Files)

- `SSR_books.zip` — Архив со всеми учебниками
- `textbooks/DOWNLOAD_LOG.md` — Лог загрузок
- `download.log` — Детальный лог процесса

## Источники (Sources)

Основные источники для поиска учебников:

### Россия
- archive.org (сканы учебников)
- elibrary.ru (российские издания)
- Просвещение (Prosveshchenie), Дрофа (Drofa)

### Украина
- archive.org
- mon.gov.ua (Министерство образования)

### Казахстан
- **OKULYK.KZ** — Основной источник (Official repository)
- archive.org
- bilimland.kz

### Беларусь
- Национальный образовательный портал
- archive.org

### Прочие страны
- Internet Archive (archive.org)
- Google Scholar
- Национальные министерства образования

## Структура sources.json

```json
{
  "Country": {
    "subject": {
      "grade": [
        "url1",
        "url2_alternative"
      ]
    }
  }
}
```

**Важно:** Добавьте реальные URL адреса в `sources.json` перед запуском скрипта.

## Логирование (Logging)

- Консоль — INFO уровень
- `download.log` — DEBUG уровень
- `textbooks/DOWNLOAD_LOG.md` — Таблица результатов

## Статус загрузок

| Статус | Значение |
|--------|----------|
| OK | Успешно загружено |
| NOT_FOUND | Источник не найден |
| FAILED | Ошибка при загрузке |

## Требования (Requirements)

- Python 3.7+
- requests
- zipfile (встроен в Python)

## Лицензия

MIT

## Помощь по поиску источников

### Как найти PDF учебников

1. **Archive.org** — сканы старых учебников
   - Поиск: `"учебник История России 9 класс"`
   - Язык поиска: cyrrilic search works

2. **Google Scholar** — научные статьи и материалы
   - filetype:pdf

3. **Национальные порталы:**
   - Россия: mob-edu.ru
   - Казахстан: bilimland.kz, okulyk.kz
   - Украина: mon.gov.ua
   - Беларусь: e-asveta.by

4. **Z-Library** (zlibrary.org) — книги на местных языках

## Поддержка

Если нашли рабочий источник — создайте Issue или PR с обновлением `sources.json`.
