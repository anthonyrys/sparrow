import math

bezier_presets = {
    'linear': [[0, 0], [0, 1], [1, 1], [1, 0], 0],
    
    'ease_out': [[0, 0], [1, 0.09], [1, .95], [1, 0], 0],
    'ease_in': [[0, 0], [0, 0.09], [0, .95], [1, 0], 0]
}

def get_bezier_point(t, p_0, p_1, p_2, p_3, i=None):
    p = [
        math.pow(1 - t, 3) * p_0[0]
        + 3 * t * math.pow(1 - t, 2) * p_1[0]
        + 3 * math.pow(t, 2) * (1 - t) * p_2[0]
        + math.pow(t, 3) * p_3[0],

        math.pow(1 - t, 3) * p_0[1]
        + 3 * t * math.pow(1 - t, 2) * p_1[1]
        + 3 * math.pow(t, 2) * (1 - t) * p_2[1]
        + math.pow(t, 3) * p_3[1]
    ]

    if i is not None:
        return p[i]
    
    return p
