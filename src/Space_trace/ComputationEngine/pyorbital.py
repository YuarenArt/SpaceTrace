from pyorbital.orbital import Orbital
import numpy as np
from datetime import timedelta, datetime

from .ComputationEngine import ComputationEngine

class PyorbitalEngine(ComputationEngine):
    def compute_points(self, data, config):
        start_datetime = config.start_datetime
        duration_hours = config.duration_hours
        step_minutes = config.step_minutes
        data_format = config.data_format

        end_time = start_datetime + timedelta(hours=duration_hours)
        step = timedelta(minutes=step_minutes)
        num_steps = int((end_time - start_datetime) / step)
        start_time_np = np.datetime64(start_datetime)
        step_np = np.timedelta64(int(step_minutes * 60 * 1e6), 'us')
        times = start_time_np + np.arange(num_steps) * step_np

        if data_format == 'TLE':
            tle_1, tle_2, inc = data
        elif data_format == 'OMM':
            record = data[0]
            tle_1 = record.get("TLE_LINE1")
            tle_2 = record.get("TLE_LINE2")
            inc = float(record.get("INCLINATION"))
        else:
            raise ValueError("Unsupported data format.")

        orb = Orbital("N", line1=tle_1, line2=tle_2)

        lons, lats, alts = orb.get_lonlatalt(times)
        points = [(times[i].astype('datetime64[ms]').astype(datetime), lons[i], lats[i], alts[i])
                  for i in range(len(times))]
        return points