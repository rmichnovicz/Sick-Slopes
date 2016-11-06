import acceleration

length = 275
height = 275 * .0524
v = 0
for x in range(0, 275, 10):
    v = acceleration.new_velocity(v, 10 * .0524, 10.0)
    print(v)