# 🚀 Быстрый старт

## Вариант 1: Автоматический поиск + загрузка

```bash
# Шаг 1: Поиск источников (10-15 минут)
chmod +x run_search.sh
./run_search.sh

# Шаг 2: Загрузка учебников
python3 downloader.py

# Результат: SSR_books.zip 📦
```

---

## Вариант 2: Локально на машине

```bash
# 1. Клонируй репо
git clone https://github.com/burgutcha01-beep/ssr-textbooks-downloader.git
cd ssr-textbooks-downloader

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Запусти поиск
python3 search_sources.py

# 4. Запусти загрузку
python3 downloader.py
```

---

## Вариант 3: В облаке (GitHub Actions)

1. Перейди в репо: https://github.com/burgutcha01-beep/ssr-textbooks-downloader
2. Нажми **Actions**
3. Выбери workflow **SSR Textbooks Downloader**
4. Нажми **Run workflow**
5. Жди завершения (~30 минут)
6. Скачай результат в **Artifacts** или **Releases**

---

## 📁 Структура проекта

```
ssr-textbooks-downloader/
├── downloader.py           # Основной скрипт загрузки
├── search_sources.py       # Поиск источников на Archive.org
├── sources.json            # База данных найденных URL
├── requirements.txt        # Python зависимости
├── SOURCES.md             # Справочник по источникам
├── QUICK_START.md         # Этот файл
└── .github/workflows/
    └── download.yml       # GitHub Actions workflow
```

---

## 📊 Что будет загружено

- **15 стран**: Россия, Украина, Беларусь, Казахстан, Узбекистан, Кыргызстан, Таджикистан, Туркменистан, Азербайджан, Армения, Грузия, Молдова, Литва, Латвия, Эстония
- **4 предмета**: История, Всемирная история, Язык, Литература
- **3 класса**: 9, 10, 11
- **~180 PDF файлов** (если найдутся)

---

## ⚙️ Опции

### Только поиск (без загрузки)
```bash
python3 search_sources.py
# Результат: sources.json обновлён
```

### Только загрузка (если sources.json готов)
```bash
python3 downloader.py
# Результат: SSR_books.zip
```

### Посмотреть логи
```bash
cat search.log      # Логи поиска
cat download.log    # Логи загрузки
cat textbooks/DOWNLOAD_LOG.md  # Таблица результатов
```

---

## 🔧 Требования

- Python 3.7+
- Интернет (для Archive.org и других источников)
- ~2GB свободного места (для ZIP архива)
- ~15 минут времени (для поиска)
- ~30 минут времени (для загрузки)

---

## 📋 Статусы загрузки

| Статус | Значение |
|--------|----------|
| `OK` | Успешно загружено |
| `NOT_FOUND` | Источник не найден |
| `FAILED` | Ошибка при загрузке |

---

## 🆘 Помощь

**Если поиск не находит источники:**
1. Проверь интернет
2. Посмотри `search.log`
3. Обнови `SOURCES.md` с новыми ссылками вручную
4. Запусти снова

**Если загрузка падает:**
1. Проверь, что `sources.json` имеет валидные URL
2. Посмотри `download.log`
3. Попробуй перезапустить

---

## 💾 Результаты

- **SSR_books.zip** — архив со всеми учебниками
- **textbooks/DOWNLOAD_LOG.md** — таблица результатов
- **download.log** — подробный лог процесса
- **search.log** — лог поиска источников

---

## 📝 Лицензия

MIT

---

**Автор:** GitHub Copilot
**Дата:** 2026-08-26
