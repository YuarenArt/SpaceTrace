from skyfield.api import load, EarthSatellite, Topos
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np

from .orbital_data_processor import OrbitalDataProcessorInterface

class SkyfieldOrbitalDataProcessor(OrbitalDataProcessorInterface):
    """
    Реализация OrbitalDataProcessorInterface с использованием Skyfield.
    Поддерживает орбиты глубокого космоса (периоды > 225 минут).
    """
    def __init__(self, tle_name: str, tle1: str, tle2: str, log_callback=None):
        """
        Инициализация с данными TLE и логгером.
        
        :param tle_name: Название спутника.
        :param tle1: Первая строка TLE.
        :param tle2: Вторая строка TLE.
        :param log_callback: Функция для логирования.
        """
        self.log_callback = log_callback or (lambda msg, lvl="INFO": print(f"[{lvl}] {msg}"))
        self._log(f"Инициализация SkyfieldOrbitalDataProcessor с именем={tle_name}", "DEBUG")
        
        try:
            self.ts = load.timescale()  # Создание шкалы времени
            self.satellite = EarthSatellite(tle1, tle2, tle_name, self.ts)  # Инициализация спутника
            self._log(f"Спутник инициализирован: {self.satellite.name}", "DEBUG")
        except Exception as e:
            self._log(f"Ошибка инициализации спутника: {str(e)}", "ERROR")
            raise ValueError(f"Ошибка инициализации спутника: {str(e)}")
        
    def _log(self, message: str, level: str = "INFO"):
        """Логирование сообщения."""
        if self.log_callback:
            self.log_callback(message, level)

    def get_coord(self, time_utc: datetime) -> Tuple[float, float, float]:
        """
        Получение геодезических координат (долгота, широта, высота) для заданного времени UTC.
        
        :param time_utc: Время в формате UTC.
        :return: Кортеж (lon, lat, alt) в градусах и километрах.
        """
        self._log(f"Получение координат для времени: {time_utc}", "DEBUG")
        t = self.ts.utc(time_utc.year, time_utc.month, time_utc.day, 
                       time_utc.hour, time_utc.minute, time_utc.second)
        geocentric = self.satellite.at(t)  # Позиция в геоцентрической системе
        subpoint = geocentric.subpoint()  # Преобразование в геодезические координаты
        lon = subpoint.longitude.degrees
        lat = subpoint.latitude.degrees
        alt = subpoint.elevation.km
        return lon, lat, alt

    def compute_orbital_parameters(
        self,
        times: List[datetime]
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Вычисление орбитальных параметров для списка времён.
        
        :param times: Список объектов datetime.
        :return: Список кортежей (time, lon, lat, alt, velocity, azimuth, arc, true_anomaly, inclination).
        """
        self._log(f"Вычисление параметров для {len(times)} времён", "DEBUG")
        results = []
        for time in times:
            t = self.ts.utc(time.year, time.month, time.day, 
                           time.hour, time.minute, time.second)
            geocentric = self.satellite.at(t)
            subpoint = geocentric.subpoint()
            lon = subpoint.longitude.degrees
            lat = subpoint.latitude.degrees
            alt = subpoint.elevation.km
            velocity = geocentric.velocity.km_per_s  # Скорость в км/с
            
            # Простые вычисления для дополнительных параметров
            velocity_norm = np.linalg.norm(velocity)
            inclination = self.satellite.model.inclo * (180.0 / np.pi)  # Наклонение в градусах
            
            # Заглушки для azimuth, arc, true_anomaly (требуют доработки)
            azimuth = 0.0  # Требуется расчёт направления движения
            arc = 0.0      # Требуется вычисление траекторной дуги
            true_anomaly = 0.0  # Требуется вычисление истинной аномалии
            
            results.append((time, lon, lat, alt, velocity_norm, azimuth, arc, true_anomaly, inclination))
        return results

    def propagate(
        self,
        start: datetime,
        duration_hours: float,
        step_minutes: float
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Генерация орбитальных параметров от начального времени на заданный период с шагом.
        
        :param start: Начальное время.
        :param duration_hours: Продолжительность в часах.
        :param step_minutes: Шаг в минутах.
        :return: Список кортежей с параметрами.
        """
        self._log(f"Пропагация орбиты: start={start}, duration={duration_hours}ч, step={step_minutes}мин", "INFO")
        times = []
        current = start
        end = start + timedelta(hours=duration_hours)
        step = timedelta(minutes=step_minutes)
        while current <= end:
            times.append(current)
            current += step
        return self.compute_orbital_parameters(times)