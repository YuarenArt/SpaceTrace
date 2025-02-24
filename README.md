# Space Trace Plugin for QGIS

## Description
This plugin draws the spacecraft's flight path over the Earth's surface.

## Dependencies
To use this plugin, the following Python libraries are required:
- pyorbital
- spacetrack
- shapefile

## Installation of Dependencies
Open OSGeo4W Shell and run the following commands:

```
python3 -m pip install pyorbital -U --user
python3 -m pip install spacetrack -U --user
python3 -m pip install pyshp -U --user
```

## Installation of the Plugin
1. Copy the plugin folder to the QGIS plugins directory.
2. Open QGIS.
3. Go to **Plugins**.

## Usage
1. After installation, the plugin will appear in the **Vector** menu.
2. Click on **Draw flight path lines** to open the dialog.
3. In the dialog:
   - Enter the satellite's NORAD ID.
   - Select the date for which the path is to be drawn.
   - Set the calculation step in minutes.
   - (Optional) Specify the path to save the shapefile.
   - Check **Add created layer to project** to load the layer into QGIS.
4. Click **OK** to generate the orbital path.

## Notes
- If the shapefile path is left empty, the plugin will create temporary layers in memory.
- The **Add created layer to project** checkbox automatically adds the created layers to the QGIS project.

---

# Space Trace Plugin для QGIS (Русский)

## Описание
Этот плагин отображает траекторию полёта космического аппарата над поверхностью Земли.

## Зависимости
Для работы плагина необходимо установить следующие Python-библиотеки:
- pyorbital
- spacetrack
- shapefile

## Установка зависимостей
Откройте OSGeo4W Shell и выполните следующие команды:

```
python3 -m pip install pyorbital -U --user
python3 -m pip install spacetrack -U --user
python3 -m pip install pyshp -U --user
```

## Установка плагина
1. Скопируйте папку плагина в каталог плагинов QGIS.
2. Откройте QGIS.
3. Перейдите в меню **Плагины**.

## Использование
1. После установки плагин появится в меню **Вектор**.
2. Нажмите на **Draw flight path lines** (нарисовать линии траектории полёта), чтобы открыть диалоговое окно.
3. В диалоговом окне:
   - Введите NORAD ID спутника.
   - Выберите дату, для которой строится траектория.
   - Установите шаг расчёта в минутах.
   - (Опционально) Укажите путь для сохранения shapefile.
   - Установите флажок **Добавить созданный слой в проект**, чтобы загрузить слой в QGIS.
4. Нажмите **OK** для генерации траектории орбиты.

## Примечания
- Если путь к shapefile оставить пустым, плагин создаст временные слои в памяти.
- Флажок **Добавить созданный слой в проект** автоматически добавляет созданные слои в проект QGIS.
