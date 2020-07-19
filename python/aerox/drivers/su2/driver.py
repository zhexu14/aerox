import numpy as np
import os
import shlex
import subprocess
import sys

from aerox.drivers.su2.config import Config


def default_config():
    """
    - path: path to SU2_CFD executable. If none, use SU2_CFD i.e. assume executable is in PATH
    - alphas: list of alphas to evaluate
    - airspeed: airspeed to calculate at, m/s
    - window_iterations: average this many iterations from the end of the history output to calculate aerodynamic
                         moments
    - su2/*: override SU2 config
    :return: default config as dict
    """
    config = {}
    config['path'] = None
    config['alphas'] = []
    config['airspeed'] = 50.0
    config['window_iterations'] = 1
    config['su2'] = {}
    return config


def run(config, verbose = False):
    """
    Run SU2
    :param config: run config, see default_config() for details.
    :param verbose: if True, produce verbose output.
    :return: list of dicts showing lift, drag and pitching_moment coefficients at each configured alpha.
    """
    command = 'SU2_CFD'
    if config['path'] is not None:
        command = config['path']

    config_file = 'config.cfg'
    coefficients = []
    for alpha in config['alphas']:
        su2_config = Config()
        su2_config.update(config['su2'])
        su2_config['INC_VELOCITY_INIT'] = str(tuple([float(config['airspeed']) * np.cos(alpha * np.pi / 180.0),
                                                     float(config['airspeed']) * np.sin(alpha * np.pi / 180.0),
                                                     0.0]))
        with open(config_file, 'w') as fd:
            su2_config.write(fd)
        result = subprocess.run( shlex.split('{} {}'.format(command, config_file)),
                                 stdin = subprocess.PIPE,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)
        if not os.path.exists('history.dat') or result.returncode != 0:
            raise ValueError('SU2_CFD failed with\n{}\n{}'.format(result.stdout, result.stderr))

        with open('history.dat', 'r') as fd:
            coefficients.append(_load_history(fd, config))

        os.rename('history.dat', 'history_{}.dat'.format(alpha))

        if verbose:
            sys.stderr.write('{},{},{},{}\n'.format(alpha,
                                                    coefficients[-1]['lift'],
                                                    coefficients[-1]['drag'],
                                                    coefficients[-1]['pitching_moment']))
            sys.stderr.flush()
    return coefficients


def _load_history(file, config):
    """
    :param file: file-like object
    :param config: config as dict. See default_config for details.
    :return: coefficients as dict containing:
             - drag: drag coefficient
             - lift: lift coefficient
             - pitching_moment: moment coefficient
    """
    #  skip prefix
    file.readline()
    header = file.readline()
    columns = header.split(',')
    for i in range(len(columns)):
        columns[i] = columns[i].replace(' ', '')
        columns[i] = columns[i].replace('"', '')
    dtype = []
    for column in columns:
        dtype.append((column, 'f'))

    data = []
    for line in file:
        data.append(tuple(line.split(',')))
    data = np.array(data, dtype = dtype)
    data = data[np.where(data['Inner_Iter'] > 0)]
    data = data[-config['window_iterations']:]
    return {'drag': np.mean(data['CD']),
            'lift': np.mean(data['CL']),
            'pitching_moment': np.mean(data['CMz'])}
