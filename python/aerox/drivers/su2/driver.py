import numpy as np
import os
import shlex
import subprocess

from aerox.drivers.su2.config import Config


def default_config():
    """
    - path: path to SU2_CFD executable. If none, use SU2_CFD i.e. assume executable is in PATH
    - alphas: list of alphas to evaluate
    - skip_iterations: ignore these number of iterations at the beginning for initialisation
    - su2/*: override SU2 config
    :return: default config as dict
    """
    config = {}
    config['path'] = None
    config['alphas'] = []
    config['skip_iterations'] = 100
    config['su2'] = {}
    return config


def run(config):
    command = 'SU2_CFD'
    if config['path'] is not None:
        command = config['path']

    config_file = 'config.cfg'
    coefficients = []
    for alpha in config['alphas']:
        su2_config = Config()
        su2_config['AOA'] = alpha
        with open(config_file, 'w') as fd:
            su2_config.write(fd)
        result = subprocess.run( shlex.split('{} {}'.format(command, config_file)),
                                 stdin = subprocess.PIPE,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)
        if not os.path.exists('history.dat') or result.return_code != 0:
            raise ValueError('SU2_CFD failed with\n{}\n{}'.format(result.stdout, result.stderr))

        with open('history.dat', 'r') as fd:
            coefficients.append(_load_history(fd))

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
    if len(data) < config['skip_iterations']:
        raise ValueError('CFD simulation stopped after {} iterations'.format(len(data)))
    data = data[np.where(data['Time_Iter'] > config['skip_iterations'])]
    return {'drag': np.mean(data['CD']),
            'lift': np.mean(data['CL']),
            'pitching_moment': np.mean(data['CMz'])}
