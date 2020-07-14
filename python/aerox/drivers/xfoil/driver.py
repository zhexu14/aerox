import numpy as np
import xfoil


def default_config():
    """
    - alphas: list of alphas to evaluate
    - xfoil/reynolds_number: Reynolds number
    - xfoil/mach: freestream Mach number
    :return: default config as dict
    """
    config = {}
    config['alphas'] = []
    config['xfoil'] = {'reynolds_number': '1e6',
                       'mach': 0.0 }
    return config


def run(config, aerofoil):
    """
    Run xfoil analysis.
    :param config: config as dict, see default_config() for details.
    :param aerofoil: aerox.aerofoil.aerofoil.Aerofoil object.
    :return: list of length equal to the number of alphas to evaluate. Entries are either None (analysis failed to
             converge) or dict with the following keys:
             - lift: lift coefficient
             - drag: drag coefficing
             - pitching_moment: quarter-chord pitching moment coefficient
    """
    xf = xfoil.XFoil()
    xf.airfoil = aerofoil.to_xfoil_airfoil()
    xf.Re = float(config['xfoil']['reynolds_number'])
    xf.M = config['xfoil']['mach']
    xf.max_iter = 100
    r = []
    for alpha in config['alphas']:
        xf.reset_bls()
        cl, cd, cm, cp = xf.a(alpha)
        if np.isnan(cl):
            r.append(None)
        else:
            r.append({'lift': cl,
                      'drag': cd,
                      'pitching_moment': cm})
    return r
