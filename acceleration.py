def find_final_velocity(v0, dh, dist): # for small changes in V
    g = 9.81 #accelertion due to gravity, m/s
    drag_c = .6 #drag coefficient of human body
    cross_a = .68 #Cross-sectional area of human body
    mass = 80 #kg
    frict_c = .03 #Coefficient of friction
    a = g - 1.225 * drag_c * cross_a * v0 ** 2 / (2 * mass) - g * c
        # Total Acceleration = grav, air resistance, rolling friction resistance
        # Assumes final velocity causes about the amount of air resistance as
        #   inital velocity TODO: Make more classically perfect by integrating
    return (2 * a * dist + v0 ** 2)
