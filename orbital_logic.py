# orbital_logic.py
from datetime import datetime, date, timedelta
import spacetrack.operators as op
from spacetrack import SpaceTrackClient
from pyorbital.orbital import Orbital
from pyorbital import astronomy
import numpy as np
import shapefile
import os

# Учётные данные spacetrack (хотя в будущем рекомендуется вынести их в настройки)
USERNAME = '*****' 
PASSWORD = '*****'

def get_spacetrack_tle(sat_id, start_date, end_date, latest=False):
    st = SpaceTrackClient(identity=USERNAME, password=PASSWORD)
    if not latest:
        daterange = op.inclusive_range(start_date, end_date)
        data = st.tle(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle', epoch=daterange)
    else:
        data = st.tle_latest(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle')

    if not data:
        raise Exception('Не удалось получить TLE для спутника с ID {}'.format(sat_id))
    
    tle_1 = data[0:69]
    tle_2 = data[70:139]
    orb_incl = data[78:86]
    return tle_1, tle_2, orb_incl

def create_orbital_track_shapefile_for_day(sat_id, track_day, step_minutes, output_shapefile):
    # Определяем, какую TLE запрашивать: последнюю или за конкретный период
    if track_day > date.today():
        print('В расчётах используется самый последний набор TLE, полученный на {}'.format(datetime.utcnow()))
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, None, None, latest=True)
    else:
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, track_day, track_day + timedelta(days=1), latest=False)

    if not tle_1 or not tle_2:
        raise Exception('Невозможно извлечь TLE для спутника с ID {}'.format(sat_id))
    
    orb = Orbital("N", line1=tle_1, line2=tle_2)
    track_shape = shapefile.Writer(output_shapefile, shapefile.POINT)
    
    # Определяем поля шейп-файла
    track_shape.field('Point_ID','N',10)
    track_shape.field('Point_Num','N',10)
    track_shape.field('Orbit_Num','N',10)
    track_shape.field('Date_Time','C',19)
    track_shape.field('Latitude','F',10,6)
    track_shape.field('Longitude','F',11,6)
    track_shape.field('Altitude','F',20,3)
    track_shape.field('Velocity','F',10,5)
    track_shape.field('Sun_Zenith','F',7,2)
    track_shape.field('Orbit_Incl','F',9,4)

    i = 0
    minutes = 0

    while minutes < 1440:
        utc_hour = int(minutes // 60)
        utc_minutes = int((minutes - (utc_hour * 60)) // 1)
        utc_seconds = int(round((minutes - (utc_hour * 60) - utc_minutes) * 60))
        utc_string = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
        utc_time = datetime(track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)

        # Расчёт позиции спутника
        lon, lat, alt = orb.get_lonlatalt(utc_time)
        orb_num = orb.get_orbit_number(utc_time, tbus_style=False)
        sun_zenith = astronomy.sun_zenith_angle(utc_time, lon, lat)
        pos, vel = orb.get_position(utc_time, normalize=False)
        vel_ = np.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)

        # Добавляем точку в шейп-файл
        track_shape.point(lon, lat)
        track_shape.record(i, i + 1, orb_num, utc_string, lat, lon, alt, vel_, sun_zenith, orb_incl)

        i += 1
        minutes += step_minutes

    try:
        prj_filename = output_shapefile.replace('.shp', '.prj')
        with open(prj_filename, "w") as prj:
            wgs84_wkt = ('GEOGCS["WGS 84",DATUM["WGS_1984",'
                         'SPHEROID["WGS 84",6378137,298.257223563]],'
                         'PRIMEM["Greenwich",0],'
                         'UNIT["degree",0.0174532925199433]]')
            prj.write(wgs84_wkt)
        print('Шейп-файл сохранён успешно')
    except Exception as e:
        raise Exception('Не удалось сохранить шейп-файл: {}'.format(e))


def convert_points_shp_to_line(input_shp, output_shp):
    """
    Читает shapefile с точками и создаёт новый shapefile с полилинией,
    которая соединяет все точки в порядке их записи, разбивая линию на сегменты
    при пересечении меридиана (разрыв по долготе > 180°).
    """
    # Читаем исходный shapefile с точками
    reader = shapefile.Reader(input_shp)
    shapes = reader.shapes()

    if not shapes:
        raise Exception("Исходный shapefile не содержит объектов.")

    # Собираем координаты точек (каждая запись содержит одну точку [lon, lat])
    points = []
    for shp in shapes:
        if shp.points and len(shp.points) > 0:
            points.append(shp.points[0])
        else:
            raise Exception("Обнаружена запись без координат в исходном shapefile.")

    # Разбиваем точки на сегменты, проверяя разрыв по меридиану
    segments = []
    current_segment = [points[0]]
    for i in range(1, len(points)):
        prev_lon = current_segment[-1][0]
        curr_lon = points[i][0]
        # Если разница между соседними долготами больше 180°, начинаем новый сегмент
        if abs(curr_lon - prev_lon) > 180:
            segments.append(current_segment)
            current_segment = [points[i]]
        else:
            current_segment.append(points[i])
    # Добавляем последний сегмент, если он не пуст
    if current_segment:
        segments.append(current_segment)

    # Создаём новый shapefile с типом геометрии POLYLINE (многосегментная линия)
    writer = shapefile.Writer(output_shp, shapeType=shapefile.POLYLINE)
    writer.field("ID", "N", size=10)

    # Записываем полилинию: каждый сегмент является отдельной частью
    writer.line(segments)
    writer.record(1)
    writer.close()

    # Создаём файл .prj для задания системы координат (WGS84)
    prj_filename = os.path.splitext(output_shp)[0] + ".prj"
    with open(prj_filename, "w") as prj_file:
        wgs84_wkt = (
            'GEOGCS["WGS 84",DATUM["WGS_1984",'
            'SPHEROID["WGS 84",6378137,298.257223563]],'
            'PRIMEM["Greenwich",0],'
            'UNIT["degree",0.0174532925199433]]'
        )
        prj_file.write(wgs84_wkt)

    print("Конвертация завершена. Линейный shapefile создан: {}".format(output_shp))
