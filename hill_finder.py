from subprocess import check_output
import sys
import math

lat, lng = 33.373447, -84.7394

database_path = 'grdn' + str(math.ceil(abs(lat))) + 'w' \
         + str(math.ceil(abs(lng))).zfill(3) + '_13/w001001.adf'

#print(database_path)

elevation = float(check_output(
    ['gdallocationinfo',database_path,
     '-valonly','-geoloc',str(lng),str(lat)
     ])
)

print(elevation)
