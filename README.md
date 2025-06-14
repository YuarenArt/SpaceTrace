# Space Trace Plugin for QGIS

## Installation

### Dependencies
To use the Space Trace plugin, you need to install the following Python libraries:
- `pyorbital`, `poliastro` – for orbital calculations.
- `spacetrack` – for fetching orbital data from the SpaceTrack API.

### Installation of Dependencies
1. Open the **OSGeo4W Shell** (included with QGIS installation).
2. Run the following commands to install the required libraries:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
   python3 -m pip install poliastro -U --user
   ```

### Installation of the Plugin
1. Copy the plugin folder to the QGIS plugins directory:
   - Windows: `C:\Users\[YourUsername]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
   - macOS: `~/Library/QGIS/QGIS3/profiles/default/python/plugins`
2. Open QGIS.
3. Go to **Plugins** > **Manage and Install Plugins**.
4. In the plugin manager, find **Space Trace** and check the box to enable it.

## Features
The Space Trace plugin visualizes the flight path of a spacecraft over the Earth’s surface. Key features include:
- **Data Sources**: Fetch orbital data (TLE or OMM format) from the SpaceTrack API or load it from a local file.
- **Track Generation**: Create point and line layers representing the spacecraft’s orbital path for a specified date.
- **Customization**: Adjust the time step (in minutes) for track calculations.
- **Output Options**: 
  - Save layers as shapefiles (`.shp`), GeoPackages (`.gpkg`), or GeoJSON (`.geojson`).
  - Add generated layers directly to the QGIS project.
- **Data Saving**: Optionally save fetched TLE or OMM data for future use.
- **Logging**: View detailed logs of the process in the plugin’s interface.

## Usage
1. After installation, the plugin appears in the **Vector** menu in QGIS.
2. Select **Space Trace** > **Draw flight path** to open the plugin dialog.
3. Configure the settings in the dialog:
   ### Data Source
   - **Load from local file**: Use a local TLE or OMM file.
     - Click **Browse** to select the file.
     - Choose the format: **TLE** (`.txt`) or **OMM** (`.json`).
   - **Fetch from SpaceTrack API**: Retrieve data online.
     - Enter the satellite’s **NORAD ID** (e.g., 25544 for the ISS).
     - Provide your SpaceTrack account **email** and **password**.
     - Select the format: **TLE** or **OMM**.

   ### Track Settings
   - Choose the **date** for the orbital path using the calendar widget.
   - Set the **time step** (in minutes) for calculations (e.g., 0.5 for finer detail).

   ### Output Settings
   - (Optional) Specify a **file path** to save the output (`.shp`, `.gpkg`, or `.geojson`).
   - Check **Add created layer to project** to load layers into QGIS.
   - Check **Create line layer** to generate a line layer alongside points.

   ### Save Received Data
   - Check **Save TLE/OMM data** to store fetched data.
   - Specify a **file path** for saving (`.txt` for TLE, `.json` for OMM).

4. Click **Execute** to generate the orbital path.
5. Monitor the process in the **Log** tab. If successful, layers will be added to the project or saved to the specified path.

## Enhanced Satellite Search Dialog

In addition to the existing data‑fetch and track‑generation features, the plugin now includes an interactive dialog for discovering satellites via the SpaceTrack API:

- **Multi‑Mode Search**  
  A unified dialog lets you choose among four search modes:
  1. **By Name** – lookup satellites by partial or full name.  
  2. **All Active** – list all currently active objects.  
  3. **By Country** – filter by two‑letter country code (e.g., `US`).  
  4. **By NORAD ID** – supply a single ID (e.g. `25544`), a range (`25544-25550`), or a comma‑separated list (`25544,25545`).

- **Custom Query Builder**  
  Launch a secondary dialog to craft arbitrary API queries.  
  - Choose any catalog field (International Designator, Launch Date, Eccentricity, etc.)  
  - Pick an operator (`=`, `!=`, `<`, `>`, or `LIKE` for strings)  
  - Enter a value (with context‑sensitive hints: integers, decimals, dates, enums)  
  - Combine multiple conditions into a single request  

- **Result Presentation & Selection**  
  - Results are shown in a sortable table with the following columns: NORAD ID, Name, Country, Launch Date, Eccentricity, Perigee, Apogee, Inclination.  
  - Configure the maximum number of rows via a simple dropdown (1 – 1000).  
  - Click to select a satellite; the dialog returns the chosen NORAD ID for downstream processing.  

## Notes
- If no output file path is provided, temporary in-memory layers are created.
- Ensure SpaceTrack API credentials are valid for online data retrieval.
- The plugin supports both TLE (Two-Line Element) and OMM (Orbit Mean Elements) formats.

---

# Space Trace Plugin для QGIS (Русский)

## Установка

### Зависимости
Для работы плагина Space Trace необходимо установить следующие Python-библиотеки:
- `pyorbital`, `poliastro` – для орбитальных расчетов.
- `spacetrack` – для получения данных с SpaceTrack API.

### Установка зависимостей
1. Откройте **OSGeo4W Shell** (поставляется с QGIS).
2. Выполните следующие команды для установки библиотек:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
   python3 -m pip install poliastro -U --use
   ```

### Установка плагина
1. Скопируйте папку плагина в каталог плагинов QGIS:
   - Windows: `C:\Users\[ВашеИмя]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
   - macOS: `~/Library/QGIS/QGIS3/profiles/default/python/plugins`
2. Откройте QGIS.
3. Перейдите в **Плагины** > **Управление и установка плагинов**.
4. В менеджере плагинов найдите **Space Trace** и включите его, установив галочку.

## Функциональность
Плагин Space Trace визуализирует траекторию полета космического аппарата над поверхностью Земли. Основные возможности:
- **Источники данных**: Загрузка орбитальных данных (формат TLE или OMM) из SpaceTrack API или локального файла.
- **Создание трассы**: Создание слоев точек и линий, представляющих орбитальный путь для заданной даты.
- **Настройка**: Установка шага времени (в минутах) для расчетов.
- **Вывод данных**:
  - Сохранение слоев в форматах shapefiles (`.shp`), GeoPackages (`.gpkg`) или GeoJSON (`.geojson`).
  - Добавление сгенерированных слоев в проект QGIS.
- **Сохранение данных**: Возможность сохранить полученные TLE или OMM данные.
- **Логирование**: Подробные журналы процесса доступны в интерфейсе плагина.

## Использование
1. После установки плагин появится в меню **Вектор** в QGIS.
2. Выберите **Space Trace** > **Draw flight path** (Нарисовать траекторию полета), чтобы открыть диалог.
3. Настройте параметры в диалоговом окне:
   ### Источник данных
   - **Загрузить из локального файла**: Используйте локальный файл TLE или OMM.
     - Нажмите **Обзор** для выбора файла.
     - Выберите формат: **TLE** (`.txt`) или **OMM** (`.json`).
   - **Получить из SpaceTrack API**: Загрузка данных онлайн.
     - Введите **NORAD ID** спутника (например, 25544 для МКС).
     - Укажите **email** и **пароль** учетной записи SpaceTrack.
     - Выберите формат: **TLE** или **OMM**.

   ### Настройки трассы
   - Выберите **дату** для построения траектории с помощью календаря.
   - Установите **шаг времени** (в минутах) для расчетов (например, 0.5 для большей детализации).

   ### Настройки вывода
   - (Опционально) Укажите **путь к файлу** для сохранения (`.shp`, `.gpkg`, или `.geojson`).
   - Установите флажок **Добавить созданный слой в проект**, чтобы загрузить слои в QGIS.
   - Установите флажок **Создать слой линий**, чтобы сгенерировать линии в дополнение к точкам.

   ### Сохранение полученных данных
   - Установите флажок **Сохранить данные TLE/OMM**, чтобы сохранить полученные данные.
   - Укажите **путь** для сохранения (`.txt` для TLE, `.json` для OMM).

4. Нажмите **Выполнить** для генерации траектории.
5. Следите за процессом на вкладке **Журнал**. При успехе слои будут добавлены в проект или сохранены по указанному пути.

## Расширенный поиск спутников через SpaceTrack

В дополнение к существующим возможностям загрузки данных и построения траектории, плагин теперь включает интерактивный диалог для поиска спутников через API SpaceTrack:

- **Многофункциональный поиск**  
  Унифицированный интерфейс позволяет выбрать один из четырех режимов поиска:
  1. **По имени** – поиск спутников по полному или частичному имени.  
  2. **Все активные** – отображение всех активных объектов на орбите.  
  3. **По стране** – фильтрация по двухбуквенному коду страны (например, `US`).  
  4. **По NORAD ID** – указание одного ID (например, `25544`), диапазона (`25544-25550`) или списка через запятую (`25544,25545`).  

- **Конструктор пользовательских запросов**  
  Отдельное окно позволяет формировать произвольные запросы к API.  
  - Выбор любого поля каталога (международный идентификатор, дата запуска, эксцентриситет и др.)  
  - Выбор оператора (`=`, `!=`, `<`, `>`, или `LIKE` для строк)  
  - Ввод значения с подсказками по типу (целые числа, десятичные, даты, перечисления)  
  - Объединение нескольких условий в один запрос  

- **Отображение и выбор результатов**  
  - Результаты выводятся в сортируемой таблице с колонками: NORAD ID, Название, Страна, Дата запуска, Эксцентриситет, Перигей, Апогей, Наклонение.  
  - Установка максимального количества строк через выпадающий список (от 1 до 1000).  
  - Щелчок по строке выбирает спутник; диалог возвращает соответствующий NORAD ID для дальнейшей обработки.


## Примечания
- Если путь к файлу вывода не указан, создаются временные слои в памяти.
- Убедитесь, что учетные данные SpaceTrack API верны для загрузки данных онлайн.
- Плагин поддерживает форматы TLE (Two-Line Element) и OMM (Orbit Mean Elements).
