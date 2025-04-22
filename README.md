# Space Trace Plugin for QGIS

## Installation

### Dependencies
To use the Space Trace plugin, you need to install the following Python libraries:
- `pyorbital` – for orbital calculations.
- `spacetrack` – for fetching orbital data from the SpaceTrack API.

### Installation of Dependencies
1. Open the **OSGeo4W Shell** (included with QGIS installation).
2. Run the following commands to install the required libraries:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
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

- **Advanced SpaceTrack Search**: 
  - A new dialog interface (`SpaceTrackDialog`) allows users to search for satellite data via the SpaceTrack API using multiple criteria: satellite name, country code, NORAD ID (single, range, or list), or all active satellites.
  - Results are displayed in a sortable table with key parameters like NORAD ID, name, country, launch date, eccentricity, perigee, apogee, and inclination.
  - Users can set a result limit (1 to 1000) to control the number of returned satellites.
  - A custom query dialog (`CustomQueryDialog`) enables advanced searches by combining multiple conditions (e.g., field, operator, and value) for precise filtering of satellite data.
  - All search actions are logged for transparency and debugging.

  - Click **Search via SpaceTrack API** to open the **SpaceTrack Search** dialog.
     - In the **SpaceTrack Search** dialog:
       - Choose a **Search Type**:
         - **By Name**: Enter a satellite name (e.g., "STARLINK").
         - **All Active**: Retrieve all active satellites (no input required).
         - **By Country**: Enter a country code (e.g., "US").
         - **By NORAD ID**: Enter a single NORAD ID (e.g., "25544"), a range (e.g., "25544-25550"), or a comma-separated list (e.g., "25544,25545").
       - Specify a **Result Limit** (1, 5, 10, 25, 50, 100, 500, or 1000) to control the number of results.
       - Click **Search** to fetch and display results in a table.
       - Select a satellite from the table to use its NORAD ID for track generation.
       - (Optional) Click **Custom Query** to open the **Custom Query** dialog for advanced searches:
         - Add conditions by selecting a field (e.g., "NORAD_CAT_ID", "SATNAME"), an operator (e.g., "=", "LIKE"), and a value.
         - Combine multiple conditions for precise filtering (e.g., satellites with inclination > 90° and country = "US").
         - Click **Search** to execute the custom query and display results.
     - Once a satellite is selected, click **OK** to proceed with track generation.

## Notes
- If no output file path is provided, temporary in-memory layers are created.
- Ensure SpaceTrack API credentials are valid for online data retrieval.
- The plugin supports both TLE (Two-Line Element) and OMM (Orbit Mean Elements) formats.

---

# Space Trace Plugin для QGIS (Русский)

## Установка

### Зависимости
Для работы плагина Space Trace необходимо установить следующие Python-библиотеки:
- `pyorbital` – для орбитальных расчетов.
- `spacetrack` – для получения данных с SpaceTrack API.

### Установка зависимостей
1. Откройте **OSGeo4W Shell** (поставляется с QGIS).
2. Выполните следующие команды для установки библиотек:
   ```bash
   python3 -m pip install pyorbital -U --user
   python3 -m pip install spacetrack -U --user
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

- **Расширенный поиск через SpaceTrack**:
  - Новый диалог (`SpaceTrackDialog`) позволяет искать данные о спутниках через SpaceTrack API по различным критериям: имя спутника, код страны, NORAD ID (одиночный, диапазон или список), или все активные спутники.
  - Результаты отображаются в сортируемой таблице с ключевыми параметрами: NORAD ID, имя, страна, дата запуска, эксцентриситет, перигей, апогей и наклонение.
  - Пользователь может установить лимит результатов (от 1 до 1000) для контроля количества возвращаемых спутников.
  - Диалог пользовательского запроса (`CustomQueryDialog`) позволяет выполнять сложные поиски, комбинируя несколько условий (например, поле, оператор и значение) для точной фильтрации данных.
  - Все действия поиска логируются для прозрачности и отладки.
       - Нажмите **Поиск через SpaceTrack API**, чтобы открыть диалог **Поиск SpaceTrack**.
     - В диалоге **Поиск SpaceTrack**:
       - Выберите **Тип поиска**:
         - **По имени**: Введите имя спутника (например, "STARLINK").
         - **Все активные**: Получите все активные спутники (ввод не требуется).
         - **По стране**: Введите код страны (например, "US").
         - **По NORAD ID**: Введите одиночный NORAD ID (например, "25544"), диапазон (например, "25544-25550") или список через запятую (например, "25544,25545").
       - Укажите **Лимит результатов** (1, 5, 10, 25, 50, 100, 500 или 1000) для контроля количества результатов.
       - Нажмите **Поиск**, чтобы получить и отобразить результаты в таблице.
       - Выберите спутник из таблицы, чтобы использовать его NORAD ID для генерации траектории.
       - (Опционально) Нажмите **Пользовательский запрос**, чтобы открыть диалог **Пользовательский запрос** для сложных поисков:
         - Добавляйте условия, выбирая поле (например, "NORAD_CAT_ID", "SATNAME"), оператор (например, "=", "LIKE") и значение.
         - Комбинируйте несколько условий для точной фильтрации (например, спутники с наклонением > 90° и страной = "US").
         - Нажмите **Поиск**, чтобы выполнить пользовательский запрос и отобразить результаты.
     - После выбора спутника нажмите **ОК**, чтобы продолжить генерацию траектории.

## Примечания
- Если путь к файлу вывода не указан, создаются временные слои в памяти.
- Убедитесь, что учетные данные SpaceTrack API верны для загрузки данных онлайн.
- Плагин поддерживает форматы TLE (Two-Line Element) и OMM (Orbit Mean Elements).
