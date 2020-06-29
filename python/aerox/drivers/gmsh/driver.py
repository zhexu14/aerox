import os
import subprocess
import shlex


def default_config():
    """
    - path: absolute path where gmsh executable is, or None if gmsh is installed (i.e. in PATH environment variable)
    - dimensions: 1, 2, or 3
    - working_directory: working directory path as str.
    :return: default config as dict
    """
    return {'path': None,
            'dimensions': 2,
            'working_directory': '.'}


def run(geometry, config):
    """
    Runs gmsh to generate SU2 mesh.
    :param geometry: gmsh geometry definition (contents of .geo file) as string.
    :param config: gmsh config, see default_config() for details.
    :return: None
    """
    geometry_file = os.path.join(config['working_directory'], 'mesh.geo')
    output = os.path.join(config['working_directory'], 'mesh.su2')
    with open(geometry_file, 'w') as fd:
        for line in geometry:
            fd.write(line + '\n')

    executable = 'gmsh'
    if config['path'] is not None:
        executable = config[ 'path' ]

    command = '{executable} -{dimensions} {geometry} -format su2 -o {output}'.format(executable = executable,
                                                                                     dimensions = config['dimensions'],
                                                                                     geometry = geometry_file,
                                                                                     output = output)
    p = subprocess.Popen(shlex.split(command),
                         stdin = subprocess.PIPE,
                         stdout = subprocess.PIPE)
    p.wait()
