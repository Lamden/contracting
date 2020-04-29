random.seed()
gradients = Hash()

def rand_vect():
    theta = random.randint(0, 100) / 50 * 3.13
    return {'x': 5.124 / theta, 'y': 7.124 / theta}


def dot_prod_grid(x, y, vx, vy):
    d_vect = {'x': x - vx, 'y': y - vy}
    key = str(vx) + ',' + str(vy)
    if gradients[key]:
        g_vect = gradients[key]
    else:
        g_vect = rand_vect()
        gradients[key] = g_vect
    return (d_vect['y']) * (g_vect['x']) + (d_vect['y']) * (g_vect['y']);


def smootherstep(x):
    return (6.0 * x ** 5.0 - 15.0 * x ** 4.0 + 10.0 * x ** 3.0)


def interp(x, a, b):
    return a + (b - a) * smootherstep(x)


@export
def seed():
    gradients['0'] = 1  # test

@export
def get(x: float, y: float):
    xf = int(x)
    yf = int(y)
    tl = dot_prod_grid(x, y, xf, yf)
    tr = dot_prod_grid(x, y, xf + 1, yf)
    bl = dot_prod_grid(x, y, xf, yf + 1)
    br = dot_prod_grid(x, y, xf + 1, yf + 1)
    xt = interp(x - xf, tl, tr)
    xb = interp(x - xf, bl, br)
    return interp(y - yf, xt, xb)