import math

g = -9.81 #accelertion due to gravity, m/s
drag_c = .6 #drag coefficient of human body
cross_a = .68 #Cross-sectional area of human body
mass = 80 #kg
frict_c = .03 #Coefficient of friction

def new_velocity(v0, dh, dist): # for small changes in V
    theta = math.atan2(dh, dist)
    a = ((g * math.sin(theta))
         - (1.225 * drag_c * cross_a * v0 ** 2) / (2 * mass)
         + (g * frict_c * math.cos(theta))
        )
        # Total Acceleration = grav, air resistance, rolling friction resistance
        # Assumes final velocity causes about the amount of air resistance as
        #   inital velocity TODO: Make more classically perfect by integrating
    vel_sqr = 2 * a * math.sqrt(dist**2 + dh**2) + v0 ** 2
    if vel_sqr > 0:
        return math.sqrt(vel_sqr)
    else:
        return 0
