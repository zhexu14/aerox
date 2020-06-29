import os
import shlex
import subprocess
import sys

from aerox.aerofoil.aerofoil import Aerofoil


def run(name, config, **kwargs):
    """
    Run naca456 to generate coordinates of NACA aerofoil.
    :param name: name of aerofoil to generate e.g. '2412' for NACA2412 aerofoil or '65-110' for NACA65-110 aerofoil.
    :param config: config as dict. See default_config() for details.
    :return: Aerofoil object.
    """

    input_filename = 'naca.in'
    with open(input_filename, 'w') as fd:
        _write(_config_from_name(name, **kwargs), fd)

    command = 'naca456'
    if config['path'] is not None:
        command = os.path.join(config['path'])

    process = subprocess.Popen(shlex.split(command),
                               stdin = subprocess.PIPE,
                               stdout = subprocess.PIPE)
    stdout, stderr = process.communicate(input_filename.encode())
    if not os.path.exists('naca.gnu'):
        raise ValueError('naca456 failed to execute with the following error message:\n{}'.format(stdout))

    aerofoil = Aerofoil()
    with open('naca.gnu', 'r') as fd:
        aerofoil.load_from_gnu(fd)
    os.remove('naca.gnu')
    os.remove('naca.dbg')
    os.remove('naca.out')
    os.remove(input_filename)
    return aerofoil


def default_config():
    """
    - path: path to executable
    - name: name of aerofoil
    - profile/type: name of profile type, valid values '4', '4A', '6?', '6A'
    - camber/type: camber type, valid values are '0', '2', '3', '3R', '6' and '6A'
    - camber/max_fraction: maximum camber as fraction of chord
    - chord/length: chord length in non-dimensional units
    - chord/max_camber_fraction: fraction of chord where max camber occurs
    - thickness_fraction: thickness fraction of aerofoil
    - lift_coefficient: design lift coefficient, only applicable to '3', '3R', '6' and '6A' camber types
    - six/*: applicable to six digit aerofoils only
    - six/constant_loading_fraction: a, fraction of chord with constant loading
    :return: default config as dict
    """
    config = {}
    config['path'] = None
    config['name'] = ''
    config['camber'] = {}
    config['camber']['type'] = '0'
    config['camber']['max_fraction'] = None
    config['thickness'] = {}
    config['thickness']['type'] = '4'
    config['thickness']['max_fraction'] = 0.12
    config['chord'] = {}
    config['chord']['length'] = 1.0
    config['chord']['max_camber_fraction'] = None
    config['lift_coefficient'] = None
    config['six'] = {}
    config['six']['constant_loading_fraction'] = 1.0  # a
    return config


def _config_from_name(name, **kwargs):
    """
    :param name: name as string e.g. '2412' for NACA2412 aerofoil
    :return: aerofoil config from name
    """
    if len(name) == 4:
        return _four_digit(name)
    elif name[0] == '6':
        return _six_digit(name, **kwargs)
    else:
        raise ValueError('Expected valid aerofoil name, got {}'.format(name))


def _write(config, ostream = sys.stdout):
    """
    Write config into nml output for naca456 application.
    :param config: config to write.
    :param ostream: output stream.
    :return: None
    """
    #  header
    output = '&NACA\n'

    #  name
    if len(config['name']) > 0:
        output += 'name={},\n'.format(config['name'])

    #  always output dense sampling of points
    output += 'dencode=3,\n'

    #  camber
    output += """camber='{}',\n""".format(config['camber']['type'])
    if config['camber']['max_fraction'] is not None:
        output += 'cmax={},\n'.format(config['camber']['max_fraction'])

    #  thickness
    output += 'toc={},\n'.format(config['thickness']['max_fraction'])
    output += """profile='{}',\n""".format(config['thickness']['type'])

    #  chord
    output += 'chord={},\n'.format(config['chord']['length'])
    if config['chord']['max_camber_fraction'] is not None:
        output += 'xmaxc={},\n'.format(config['chord']['max_camber_fraction'])

    if config['lift_coefficient'] is not None:
        if config['camber']['type'] not in ('3', '3R', '6', '6A'):
            raise ValueError('lift_coefficient is set for camber line type {}.' + \
                             'Expected one of 3, 3R, 6 or 6A'.format(config['camber']['type']))
        output += 'cl={},\n'.format(config['lift_coefficient'])

    if config['camber']['type'] in ('6', '6A'):
        output += 'a={},\n'.format(config['six']['constant_loading_fraction'])

    #  write EOF symbol
    output = output[0:-2]
    output += '/\n'
    ostream.write(output)


def _four_digit(name):
    """
    Constructs NACA four digit aerofoil.
    :param name: name of aerofoil e.g. '2412'.
    :return: config as dict. See default_config() for details.
    """
    config = default_config()
    config['thickness']['type'] = '4'
    if name[0] == '0':
        config['camber']['type'] = '0'
    else:
        config['camber']['type'] = '2'
        config['camber']['max_fraction'] = float(name[0]) * 0.01
        config['chord']['max_camber_fraction'] = float(name[1]) * 0.1
    config['thickness']['max_fraction'] = float(name[2:4]) * 0.01
    return config


def _six_digit(name):
    """
    Constructs NACA six digit aerofoil.
    :param name: name of aerofoil e.g. '64-110'.
    :return: config as dict. See default_config() for details.
    """
    s = name.split('-')
    if len(s) != 2:
        raise ValueError('Expected name as 6x-xxx, got {}'.format(name))
    config = default_config()
    config['thickness']['type'] = s[0]
    config['thickness']['max_fraction'] = float(s[1][1:3]) * 0.01
    config['lift_coefficient'] = float(s[1][0]) * 0.1
    if s[1][0] == '0':
        config['camber']['type'] = '0'
    else:
        config['camber']['type'] = '6'
    return config
