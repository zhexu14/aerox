import xfoil

def default_config():
    """
    - path: path to xfoil executable. If none, use xfoil i.e. assume executable is in PATH
    - alphas: list of alphas to evaluate
    :return: default config as dict
    """
    config = {}
    config['alphas'] = []
    config['xfoil'] = {'reynolds_number': '1e6',
                       'mach': 0.0 }
    return config

def run(config, aerofoil):
    """

    :param config:
    :param aerofoil:
    :return:
    """
    xf = xfoil.XFoil()
    xf.airfoil = aerofoil.to_xfoil_airfoil()
    xf.repanel()
    xf.Re = float(config['xfoil']['reynolds_number'])
    xf.M = config['xfoil']['mach']
    r = []
    for alpha in config['alphas']:
        cl, cd, cm, cp = xf.a(alpha)
        r.append({'lift': cl,
                  'drag': cd,
                  'pitching_moment': cm})
    return r
