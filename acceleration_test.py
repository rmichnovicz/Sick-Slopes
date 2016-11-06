import acceleration
import hill_finder
lat = 33.773963
lng = -84.394920
end_lng = -84.391991
height = 275 * .0524
v = 0
elevation = 0
while lng < end_lng:
    elevation = hill_finder.get_elevations_by_coords([lat], [lng])[0]
    lng += 1/3600/3
    new_elevation = hill_finder.get_elevations_by_coords([lat], [lng])[0]
    change = float(new_elevation) - float(elevation)
    v = acceleration.new_velocity(v, change, 10.29)
    print(v)