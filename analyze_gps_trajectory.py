import pandas as pd
import numpy as np

df = pd.read_csv('vehicle_2_4_first_200.csv')
src_lats = df['Latitude_source'].values
src_lons = df['Longitude_source'].values

print('GPS Trajectory Analysis:')
print(f'Total points: {len(df)}')
print(f'\nStart: ({src_lats[0]:.6f}, {src_lons[0]:.6f})')
print(f'End: ({src_lats[-1]:.6f}, {src_lons[-1]:.6f})')

# Calculate cumulative distance
distances = []
cum_dist = 0
for i in range(1, len(src_lats)):
    lat_diff = (src_lats[i] - src_lats[i-1]) * 111000
    lon_diff = (src_lons[i] - src_lons[i-1]) * 111000 * np.cos(np.radians(src_lats[i]))
    dist = np.sqrt(lat_diff**2 + lon_diff**2)
    cum_dist += dist
    distances.append(cum_dist)

print(f'\nTotal path distance: {cum_dist:.1f}m')
print(f'\nKey milestones:')
for i in [0, 50, 100, 150, 199]:
    if i == 0:
        d = 0
    else:
        d = distances[i-1]
    print(f'  Point {i:3d}: ({src_lats[i]:.6f}, {src_lons[i]:.6f}) - {d:6.1f}m from start')

