# Space Trace Plugin for QGIS

## Project Overview

**Space Trace** is a powerful QGIS plugin for visualizing, analyzing, and exporting satellite orbits using TLE/OMM data. It supports both SpaceTrack API and local files, advanced search and custom queries, and flexible export options. Space Trace is designed for remote sensing professionals, astronomers, engineers, educators, and anyone working with orbital data.

---

## What Can Space Trace Do?

- Fetch up-to-date orbital data (TLE/OMM) from SpaceTrack API or local files
- Generate point and line layers representing satellite orbits for any date and duration
- Export results as Shapefile, GeoPackage, GeoJSON, or as temporary QGIS layers
- Search for satellites by name, country, NORAD ID, or using advanced custom queries
- Batch process multiple satellites or files in one run
- Save raw TLE/OMM data for later use
- Log all actions and errors for transparency and troubleshooting
- Fully localized interface (English and Russian)
- Intuitive, tabbed dialog interface: Main, Log, Help

---

## Table of Contents

- [Project Overview](#project-overview)
- [What Can Space Trace Do?](#what-can-space-trace-do)
- [Feature Details](#feature-details)
  - [1. Data Retrieval (TLE/OMM)](#1-data-retrieval-tleomm)
  - [2. Track Generation](#2-track-generation)
  - [3. Export & Output Options](#3-export--output-options)
  - [4. Saving Raw Data](#4-saving-raw-data)
  - [5. Satellite Search & Custom Queries](#5-satellite-search--custom-queries)
  - [6. Advanced Options & Hidden Features](#6-advanced-options--hidden-features)
  - [7. Logging & Troubleshooting](#7-logging--troubleshooting)
  - [8. Localization](#8-localization)
- [Installation](#installation)
- [Usage Example](#usage-example)
- [Project Structure](#project-structure)
- [FAQ](#faq)
- [Feedback & Contribution](#feedback--contribution)

---

## Feature Details

### 1. Data Retrieval (TLE/OMM)

- **From SpaceTrack API:**
  - Enter your SpaceTrack credentials in the plugin dialog.
  - Supports both TLE and OMM formats.
  - Fetches the latest data for specified NORAD IDs, ranges, or lists.
  - Secure handling of credentials (not stored).
- **From Local Files:**
  - Load one or multiple TLE or OMM files from disk.
  - Multi-file support for batch processing.
  - Automatic validation of file format and content.
- **Non-obvious:**
  - You can mix and match data sources in different runs.
  - The plugin validates all input before processing and provides clear error messages.

### 2. Track Generation

- **Flexible Time Settings:**
  - Set any start date/time, duration (0.1–168 hours), and time step (0.01–60 min).
  - Quick buttons for 1 hour, 1 day, 1 week.
- **Layer Types:**
  - Generates both point and line layers for each satellite's orbit.
  - Option to add layers directly to the QGIS project or keep them temporary.
- **Technical:**
  - Uses both `pyorbital` and `skyfield` engines for accurate propagation (deep space supported).
  - Computes not just position, but also velocity, azimuth, trajectory arc, true anomaly, and inclination for each time step.

### 3. Export & Output Options

- **Formats Supported:**
  - Shapefile (`.shp`), GeoPackage (`.gpkg`), GeoJSON (`.geojson`)
  - In-memory (temporary) layers if no output path is specified
- **Batch Export:**
  - For multiple satellites, specify output as `directory|format` (e.g., `C:/output|shp`).
  - Each satellite gets its own file.
- **Non-obvious:**
  - If you leave the output path blank, layers are created in memory and can be added to your QGIS project without saving to disk.
  - The plugin checks if the output directory exists and is writable before processing.

### 4. Saving Raw Data

- **Save TLE/OMM:**
  - Optionally save the raw TLE or OMM data retrieved from SpaceTrack or loaded from files.
  - Choose the save location and format (TLE as `.txt`, OMM as `.json`).
- **Batch Save:**
  - When processing multiple satellites, each gets its own data file.
- **Tip:**
  - Saved data can be reused in future runs without needing to re-download from SpaceTrack.

### 5. Satellite Search & Custom Queries

- **Search Modes:**
  - By Name: Enter part or full satellite name.
  - By Country: Enter 2-letter country code (e.g., `US`).
  - By NORAD ID: Enter single ID, range (`25544-25550`), or list (`25544,25545`).
  - All Active: List all currently active satellites.
- **Custom Query Builder:**
  - Build complex queries using any satellite field (e.g., launch date, eccentricity, country, etc.).
  - Choose comparison operators and get input hints for each field type.
  - Combine multiple conditions for advanced filtering.
- **Result Table:**
  - Sortable, multi-selectable table with satellite info.
  - Selected NORAD IDs are automatically transferred to the main dialog for track generation.
- **Non-obvious:**
  - You can save and reuse custom query conditions within a session.
  - The search dialog validates all input and provides instant feedback on errors.

### 6. Advanced Options & Hidden Features

- **Batch Processing:**
  - Process multiple satellites or files in one run.
  - Output must be a directory with format for batch mode.
- **Temporary vs. Persistent Layers:**
  - If no output path is specified, layers are created in memory.
  - You can add these layers to your QGIS project or discard them after viewing.
- **Engines:**
  - Both `pyorbital` and `skyfield` are used for orbit propagation, supporting a wide range of satellites (including deep space).
- **Quick Duration Buttons:**
  - Instantly set duration to 1 hour, 1 day, or 1 week.
- **Data Validation:**
  - The plugin checks all paths, formats, and credentials before processing, and provides user-friendly error messages.
- **Localization:**
  - The interface language is automatically set based on your QGIS locale.

### 7. Logging & Troubleshooting

- **Log Tab:**
  - All processing steps, errors, and results are logged and viewable in the plugin’s Log tab.
- **Log File:**
  - All actions are also logged to `SpaceTracePlugin.log` in the plugin directory for debugging.
- **Error Handling:**
  - All errors are shown in the UI and logged for review.
- **Non-obvious:**
  - You can copy log messages directly from the Log tab for support or debugging.

### 8. Localization

- **Languages Supported:**
  - English and Russian (auto-detected from QGIS settings)
- **Help:**
  - Built-in help tab loads a detailed HTML manual in both languages.

---

## Installation

1. Open the **OSGeo4W Shell** (included with QGIS).
2. Install required Python libraries:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
   python3 -m pip install poliastro -U --user
   python3 -m pip install skyfield -U --user
   ```
3. Copy the plugin folder to your QGIS plugins directory or use the QGIS Plugin Manager (if distributed via repository).
4. Restart QGIS.
5. Activate Space Trace via the Plugins menu.

---

## Usage Example

1. Open via the <em>Vector</em> menu → <strong>Space Trace &gt; Draw flight path</strong>.
2. Select data source (local file or SpaceTrack API).
3. Specify satellites (NORAD ID, range, list, or use search).
4. Set date, duration, and step.
5. Choose output format and path (or leave blank for temporary layer).
6. Enable desired options (add to project, create line layer, save TLE/OMM).
7. Click <strong>Execute</strong>. Progress and logs appear in the Log tab.

---

## Project Structure

```
SpaceTrace/
  ├── src/
  │   ├── Space_trace/           # Main plugin logic, UI, QGIS integration
  │   ├── data_retriver/         # Data retrieval (local, SpaceTrack)
  │   ├── orbital_data_processor/# Orbit calculation engines
  │   ├── spacetrack_client/     # SpaceTrack API wrapper
  │   └── spacetrack_dialog/     # Search and query dialogs
  ├── assets/                    # Styles, icons
  ├── i18n/                      # Translations
  ├── test/                      # Tests and benchmarks
  ├── help.html                  # Built-in help (EN/RU)
  ├── requirements.txt           # Dependencies
  └── README.md
```

---

## FAQ

**Q: I can't install dependencies?**
A: Make sure you are using the Python environment from QGIS (OSGeo4W Shell).

**Q: Output file is not created?**
A: For multiple satellites, use a directory with format (`C:/output|shp`).

**Q: SpaceTrack login fails?**
A: Double-check your credentials and internet connection. After several failed attempts, your account may be temporarily blocked.

**Q: The interface is not in my language?**
A: The language is set by your QGIS locale. Change your locale and restart QGIS.

**Q: Where are logs saved?**
A: See the Log tab in the plugin or open `SpaceTracePlugin.log` in the plugin directory.

---

## Feedback & Contribution

- **Feedback:** Please fill out the form: [Submit Feedback](https://docs.google.com/forms/d/e/1FAIpQLSeBbJ04MGpFDky_4aFa9_UeEwnK2lI7itQFHYkwmcPIWe9giQ/viewform?usp=header)
- **Issues:** Report bugs and suggest improvements via GitHub Issues
- **Contribution:** Pull requests are welcome! Please follow PEP8 and add docstrings
- **License:** GNU LGPL v2.1

---


# Space Trace Plugin для QGIS (на русском)

## Обзор проекта

**Space Trace** — это мощный плагин для QGIS для визуализации, анализа и экспорта орбит спутников по данным TLE/OMM. Поддерживает работу с API SpaceTrack и локальными файлами, расширенный поиск, пользовательские запросы и гибкие форматы экспорта. Space Trace предназначен для специалистов по ДЗЗ, астрономов, инженеров, преподавателей и всех, кто работает с орбитальными данными.

---

## Что умеет Space Trace?

- Получать актуальные орбитальные данные (TLE/OMM) из SpaceTrack API или локальных файлов
- Генерировать точечные и линейные слои орбит спутников на любую дату и длительность
- Экспортировать результаты в Shapefile, GeoPackage, GeoJSON или как временные слои QGIS
- Искать спутники по имени, стране, NORAD ID или с помощью расширенных пользовательских запросов
- Пакетно обрабатывать несколько спутников или файлов за один запуск
- Сохранять исходные TLE/OMM для повторного использования
- Логировать все действия и ошибки для прозрачности и отладки
- Полностью локализованный интерфейс (английский и русский)
- Интуитивный диалог с вкладками: Основное, Лог, Справка

---

## Оглавление

- [Обзор проекта](#обзор-проекта)
- [Что умеет Space Trace?](#что-умеет-space-trace)
- [Описание функций](#описание-функций)
  - [1. Получение данных (TLE/OMM)](#1-получение-данных-tleomm)
  - [2. Построение траекторий](#2-построение-траекторий)
  - [3. Экспорт и вывод](#3-экспорт-и-вывод)
  - [4. Сохранение исходных данных](#4-сохранение-исходных-данных)
  - [5. Поиск спутников и пользовательские запросы](#5-поиск-спутников-и-пользовательские-запросы)
  - [6. Расширенные и скрытые возможности](#6-расширенные-и-скрытые-возможности)
  - [7. Логирование и отладка](#7-логирование-и-отладка)
  - [8. Локализация](#8-локализация)
- [Установка](#установка)
- [Пример использования](#пример-использования)
- [Структура проекта](#структура-проекта)
- [FAQ](#faq)
- [Обратная связь и вклад](#обратная-связь-и-вклад)

---

## Описание функций

### 1. Получение данных (TLE/OMM)

- **Из SpaceTrack API:**
  - Введите свои учетные данные SpaceTrack в диалоге плагина.
  - Поддерживаются форматы TLE и OMM.
  - Получение актуальных данных по указанным NORAD ID, диапазонам или спискам.
  - Безопасная работа с логином/паролем (не сохраняются).
- **Из локальных файлов:**
  - Загрузка одного или нескольких файлов TLE или OMM с диска.
  - Поддержка пакетной обработки.
  - Автоматическая проверка формата и содержимого файлов.
- **Неочевидно:**
  - Можно чередовать источники данных в разных запусках.
  - Плагин валидирует все входные данные и выдает понятные ошибки.

### 2. Построение траекторий

- **Гибкие настройки времени:**
  - Любая дата/время старта, длительность (0.1–168 ч), шаг (0.01–60 мин).
  - Быстрые кнопки: 1 час, 1 день, 1 неделя.
- **Типы слоев:**
  - Генерация точечных и линейных слоев для каждой орбиты.
  - Можно добавить слои в проект QGIS или оставить временными.
- **Технически:**
  - Используются движки `pyorbital` и `skyfield` (поддержка глубокого космоса).
  - Вычисляются не только координаты, но и скорость, азимут, дуга траектории, истинная аномалия, наклонение.

### 3. Экспорт и вывод

- **Поддерживаемые форматы:**
  - Shapefile (`.shp`), GeoPackage (`.gpkg`), GeoJSON (`.geojson`)
  - Временные (in-memory) слои, если путь вывода не указан
- **Пакетный экспорт:**
  - Для нескольких спутников укажите вывод как `папка|формат` (например, `C:/output|shp`).
  - Для каждого спутника создается отдельный файл.
- **Неочевидно:**
  - Если путь вывода пуст, слои создаются во временной памяти и могут быть добавлены в проект без сохранения на диск.
  - Плагин проверяет существование и доступность папки вывода.

### 4. Сохранение исходных данных

- **Сохранение TLE/OMM:**
  - Можно сохранить исходные TLE или OMM, полученные из SpaceTrack или файлов.
  - Выбор места и формата сохранения (TLE — `.txt`, OMM — `.json`).
- **Пакетное сохранение:**
  - Для нескольких спутников каждый получает свой файл.
- **Совет:**
  - Сохраненные данные можно использовать повторно без повторной загрузки из SpaceTrack.

### 5. Поиск спутников и пользовательские запросы

- **Режимы поиска:**
  - По имени: часть или полное имя спутника.
  - По стране: 2-буквенный код (например, `US`).
  - По NORAD ID: один, диапазон (`25544-25550`), список (`25544,25545`).
  - Все активные: список всех действующих спутников.
- **Конструктор пользовательских запросов:**
  - Гибкое построение запросов по любым полям (дата запуска, эксцентриситет, страна и др.).
  - Выбор операторов сравнения, подсказки по типу поля.
  - Комбинирование условий для сложной фильтрации.
- **Таблица результатов:**
  - Сортируемая, мультивыборная таблица со спутниковой информацией.
  - Выбранные NORAD ID автоматически подставляются в основной диалог.
- **Неочевидно:**
  - Можно сохранять и повторно использовать условия пользовательских запросов в рамках сессии.
  - Диалог поиска валидирует все поля и мгновенно сообщает об ошибках.

### 6. Расширенные и скрытые возможности

- **Пакетная обработка:**
  - Обработка нескольких спутников или файлов за один запуск.
  - Для пакетного режима вывод — только в папку с форматом.
- **Временные и постоянные слои:**
  - Если путь вывода не указан, слои создаются во временной памяти.
  - Можно добавить такие слои в проект или удалить после просмотра.
- **Движки:**
  - Используются `pyorbital` и `skyfield` для расчета орбит (поддержка глубокого космоса).
- **Быстрые кнопки длительности:**
  - Мгновенно выставляют длительность на 1 час, 1 день или 1 неделю.
- **Валидация данных:**
  - Плагин проверяет все пути, форматы и учетные данные, выдаёт понятные ошибки.
- **Локализация:**
  - Язык интерфейса определяется автоматически по локали QGIS.

### 7. Логирование и отладка

- **Вкладка Лог:**
  - Все шаги, ошибки и результаты отображаются во вкладке Лог.
- **Лог-файл:**
  - Все действия также пишутся в `SpaceTracePlugin.log` в папке плагина.
- **Обработка ошибок:**
  - Все ошибки показываются в интерфейсе и логируются.
- **Неочевидно:**
  - Сообщения из Лога можно копировать для поддержки или отладки.

### 8. Локализация

- **Поддерживаемые языки:**
  - Английский и русский (автоматически по настройкам QGIS)
- **Справка:**
  - Встроенная вкладка Help с подробным HTML-руководством на обоих языках.

---

## Установка

1. Откройте **OSGeo4W Shell** (идет в комплекте с QGIS).
2. Установите необходимые библиотеки Python:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
   python3 -m pip install poliastro -U --user
   python3 -m pip install skyfield -U --user
   ```
3. Скопируйте папку плагина в директорию QGIS plugins или используйте QGIS Plugin Manager (если распространяется через репозиторий).
4. Перезапустите QGIS.
5. Активируйте Space Trace через меню Плагины.

---

## Пример использования

1. Откройте через меню <em>Вектор</em> → <strong>Space Trace &gt; Нарисовать траекторию полета</strong>.
2. Выберите источник данных (локальный файл или SpaceTrack API).
3. Укажите спутники (NORAD ID, диапазон, список или используйте поиск).
4. Настройте дату, длительность, шаг.
5. Выберите формат и путь вывода (или оставьте пустым для временного слоя).
6. Включите нужные опции (добавить в проект, создать линейный слой, сохранить TLE/OMM).
7. Нажмите <strong>Выполнить</strong>. Прогресс и логи — во вкладке Лог.

---

## Структура проекта

```
SpaceTrace/
  ├── src/
  │   ├── Space_trace/           # Основная логика плагина, UI, интеграция с QGIS
  │   ├── data_retriver/         # Получение данных (локально, SpaceTrack)
  │   ├── orbital_data_processor/# Движки расчета орбит
  │   ├── spacetrack_client/     # Обёртка для SpaceTrack API
  │   └── spacetrack_dialog/     # Диалоги поиска и запросов
  ├── assets/                    # Стили, иконки
  ├── i18n/                      # Переводы
  ├── test/                      # Тесты и бенчмарки
  ├── help.html                  # Встроенная справка (EN/RU)
  ├── requirements.txt           # Зависимости
  └── README.md
```

---

## FAQ

**В: Не удается установить зависимости?**
О: Убедитесь, что используете Python из QGIS (OSGeo4W Shell).

**В: Не создается файл вывода?**
О: Для нескольких спутников используйте папку с форматом (`C:/output|shp`).

**В: Не удается войти в SpaceTrack?**
О: Проверьте логин/пароль и интернет. После нескольких неудачных попыток аккаунт может быть временно заблокирован.

**В: Интерфейс не на нужном языке?**
О: Язык определяется локалью QGIS. Измените локаль и перезапустите QGIS.

**В: Где хранятся логи?**
О: Смотрите вкладку Лог в плагине или откройте `SpaceTracePlugin.log` в папке плагина.

---

## Обратная связь и вклад

- **Feedback:** Пожалуйста, заполните форму: [Отправить отзыв](https://docs.google.com/forms/d/e/1FAIpQLSeBbJ04MGpFDky_4aFa9_UeEwnK2lI7itQFHYkwmcPIWe9giQ/viewform?usp=header)
- **Issues:** Сообщайте о багах и предлагайте улучшения через GitHub Issues
- **Contribution:** Pull requests приветствуются! Следуйте PEP8 и добавляйте docstring-и
- **Лицензия:** GNU LGPL v2.1

---


