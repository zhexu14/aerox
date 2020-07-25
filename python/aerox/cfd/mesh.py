import copy
import numpy as np

from aerox.drivers.gmsh.geometry import Circle
from aerox.drivers.gmsh.geometry import Line
from aerox.drivers.gmsh.geometry import Loop
from aerox.drivers.gmsh.geometry import PhysicalCurve
from aerox.drivers.gmsh.geometry import PhysicalSurface
from aerox.drivers.gmsh.geometry import Point
from aerox.drivers.gmsh.geometry import Surface


def default_config():
    """
    All dimensions are in arbitrary units. Typically the chord length is 1 unit.

    Far field
    - far_field/discretisation: grid size at far field

    Grid around aerofoil
    - grid/regular/thickness: thickness of C-type grid, distance from airfoil.
    - grid/regular/layers: the number of layers of the grid in the C-grid. In the example grid below,
                           there are 3 layers.
                              _ _ _ _ _ _
                             |_|_|_|_|_|_| C-grid
                             |_|_|_|_|_|_|
                             |_|_|_|_|_|_|
                             Segment of aerofoil surface
    - grid/regular/width: maximum width of cells before the trailing edge.
    - grid/regular/wake/width: average width of cells after the trailing edge.
    - grid/regular/wake/progression: progression in the thickness of the horizontal gridding in the wake.
                                     1 is uniform thickness, >1 means grid become thicker the farther away they are from
                                     the trailing edge. Set to None to automatically calculate this value.
    - grid/regular/boundary_layer/initial_thickness: thickness of the cell immediately adjacent to aerofoil. Cells will
                                                     increase in thickness.
    :return: default config as dict.
    """
    return {'grid': {'regular': {'width': 0.05,
                                 'wake': {'width': 0.1, 'progression': None},
                                 'layers': 50,
                                 'thickness': 5,
                                 'boundary_layer': { 'initial_thickness': 4.2e-5 }}}}


def aerofoil_geometry(aerofoil, config):
    """
    Meshes aerofoil using gmsh
    :param aerofoil: aerox.aerofoil.aerofoil.Aerofoil object describing aerofoil to be meshed.
    :param config: meshing config, see default_config() for details.
    :return: list of gmsh statements defining mesh geometry.
    """
    top = _half_aerofoil([aerofoil.leading_edge] + aerofoil.top,
                          config)

    bottom = _half_aerofoil(aerofoil.bottom + [aerofoil.leading_edge],
                            config)

    leading_edge = _leading_edge(top, bottom, config)

    trailing_edge = _trailing_edge(top, bottom, config)

    # physical objects
    aerofoil_curve = PhysicalCurve('aerofoil',
                                    [line.id for line in top['curves']['aerofoil']]
                                    + [trailing_edge['curves']['trailing_edge'][0].id]
                                    + [line.id for line in bottom['curves']['aerofoil']]
                                    + [leading_edge['curves']['inner_circle'][0].id])
    far_field_curve = PhysicalCurve('far_field',
                                    [line.id for line in top['curves']['boundary_layer']
                                                         + [ trailing_edge['curves']['all'][0]]
                                                         + [trailing_edge['curves']['all'][1]]
                                                         + [trailing_edge['curves']['all'][-1]]
                                                         + [trailing_edge['curves']['all'][4]]
                                                         + [trailing_edge['curves']['all'][3]]
                                                         + bottom['curves']['boundary_layer']
                                                         + leading_edge['curves']['outer_circle']])
    physical_surface = PhysicalSurface('dummy',
                                       [surface.id for surface in top['surfaces']['all']
                                                                    + bottom['surfaces']['all']
                                                                    + leading_edge['surfaces']['all']
                                                                    + trailing_edge['surfaces']['all']])

    return _serialise(top) \
           + _serialise(bottom) \
           + _serialise(leading_edge) \
           + _serialise(trailing_edge) \
           + [str(aerofoil_curve), str(far_field_curve), str(physical_surface)]

"""
The implementation relies on a block data structure to represent parts of the geometry.

block data structure, a dict with zero or more of the following keys:
  - 'points'
  - 'curves'
  - 'loops'
  - 'surfaces'
  Each key corresponds with a dict that groups zero or more entities, for example
  {
    'points': { 'first': {...}, 
                'second': {...} }
    'curves': { 'all': {...} },
    'loops': {}
  }
  Entity keys may be anything. Each entity value is a list of geometry objects, typically:
  - 'points': Point objects
  - 'curves': Line or Circle objects
  - 'loops': Loop objects
  - 'surfaces': Surface objects
"""


def _serialise(block):
    """
    Serialise block data structure.
    :param block: block data structure to serialise.
    :return: string representation of block.
    """
    out = []
    for type in ['points', 'curves', 'loops', 'surfaces']:
        if type not in block:
            continue
        for element in block[type]:
            out += [str(component) for component in block[type][element]]
    return out


def _half_aerofoil(coordinates, config):
    """
    Constructs half aerofoil plus its boundary layer.
    :param coordinates: coordinates of the half aerofoil, either top or bottom.
    :param config: config as dict.
    :return: block data structure representing half an aerofoil.
    """

    coordinates = copy.deepcopy(coordinates)
    reversed = False
    if coordinates[0][0] > coordinates[1][0]:
        coordinates.reverse()
        reversed = True
    i = 1
    while i < len(coordinates):
        previous_index = i - 1
        first = np.array([coordinates[previous_index][0], coordinates[previous_index][1], 0])
        second = np.array([coordinates[i][0], coordinates[i][1], 0])
        if first[0] > 0.7 and np.abs(second[0] - first[0]) < 1e-3:
                coordinates = coordinates[0: i-1] + coordinates[i:]
        else:
            i += 1
    if reversed:
        coordinates.reverse()

    aerofoil_points = []
    boundary_points = []

    # points on the aerofoil and boundary layer
    for i in range(1, len(coordinates)):
        first = np.array([coordinates[i - 1][0], coordinates[i - 1][1], 0])
        second = np.array([coordinates[i][0], coordinates[i][1], 0])

        #  normally use midpoint, but on trailing edge, use close to the aft point
        ratio = 0.5
        if not reversed and i == len(coordinates)-1:
            ratio = 0.95
        if reversed and i == 1:
            ratio = 0.05
        midpoint = first + ratio * (second - first)
        boundary_point = midpoint + \
                         (config['grid']['regular']['thickness'] / np.linalg.norm(second - first)) \
                         * np.cross(second - first, [0, 0, -1])
        aerofoil_points.append(Point(tuple(midpoint)))
        boundary_points.append(Point(tuple(boundary_point)))

    #  go through boundary points to make sure x values are in ascending/descending order
    if aerofoil_points[1].coordinates[0] > aerofoil_points[0].coordinates[0]:
        indices = list(range(len(boundary_points)))
    else:
        indices = list(range(len(boundary_points) - 1, -1, -1))

    for i in range(1,len(indices)):
        current_index = indices[i]
        previous_index = indices[i-1]
        if boundary_points[current_index].coordinates[0] < boundary_points[previous_index].coordinates[0]:
            aerofoil_difference = aerofoil_points[current_index].coordinates[0] \
                                  - aerofoil_points[previous_index].coordinates[0]
            boundary_points[current_index].coordinates = (boundary_points[previous_index].coordinates[0] \
                                                          + aerofoil_difference,
                                                          boundary_points[previous_index].coordinates[1],
                                                          0)

    aerofoil_lines = []
    boundary_lines = []
    vertical_lines = [Line(aerofoil_points[0],
                           boundary_points[0],
                           transfinite = config['grid']['regular']['layers'])]
    loops = []
    surfaces = []
    for i in range(1, len(aerofoil_points)):
        length = np.linalg.norm(np.array(boundary_points[i-1].coordinates)
                                - np.array(boundary_points[i].coordinates))
        num_transfinite = int(length / config['grid']['regular']['width']) + 1
        if num_transfinite < 2:
            num_transfinite = 2
        aerofoil_line = Line(aerofoil_points[i-1],
                             aerofoil_points[i],
                             transfinite = num_transfinite)
        boundary_line = Line(boundary_points[i],
                             boundary_points[i - 1],
                             transfinite = num_transfinite)
        vertical_line = Line(aerofoil_points[i],
                             boundary_points[i],
                             transfinite = config['grid']['regular']['layers'])
        aerofoil_lines.append(aerofoil_line)
        boundary_lines.append(boundary_line)
        vertical_lines.append(vertical_line)
        loops.append(Loop([aerofoil_lines[-1].id,
                           vertical_lines[-1].id,
                           boundary_lines[-1].id,
                           -1 * vertical_lines[-2].id]))
        surfaces.append(Surface([loops[-1].id], transfinite = True))

    for line in vertical_lines:
        line.progression_from_width(config['grid']['regular']['boundary_layer']['initial_thickness'])

    return {'points': {'aerofoil': aerofoil_points, 'boundary_layer': boundary_points},
            'curves': {'aerofoil': aerofoil_lines, 'boundary_layer': boundary_lines, 'normals': vertical_lines},
            'loops': {'all': loops},
            'surfaces': {'all': surfaces}}


def _leading_edge(top, bottom, config):
    """
    Meshes leading edge of aerofoil plus its boundary layer.
    :param top: coordinates of the top of the aerofoil.
    :param bottom: coordinates of the top of the aerofoil.
    :param config: config as dict. See default_config() for details.
    :return: block data structure representing the leading edge.
    """
    def circle_center(top_aerofoil_points, bottom_aerofoil_points):
        """
        Center of circle that is tangential to front line segment of aerofoil top and bottom.
        :param top_aerofoil_points:
        :param bottom_aerofoil_points:
        :return: Point object representing the circle center.
        """
        q = np.array(top_aerofoil_points[0].coordinates) - np.array(top_aerofoil_points[1].coordinates)
        r = np.array(bottom_aerofoil_points[-1].coordinates) - np.array(bottom_aerofoil_points[-2].coordinates)
        c = np.cross(q, [0, 0, -1]) / np.linalg.norm(q)
        d = np.cross(r, [0, 0, 1]) / np.linalg.norm(r)
        radius = (q[1] - r[1]) / (d[1] - c[1])
        s = q + radius * c
        return Point(tuple(-s))

    center_point = circle_center(top['points']['aerofoil'], bottom['points']['aerofoil'])

    num_transfinite = int(np.linalg.norm(np.array(top['points']['boundary_layer'][0].coordinates)
                                         - np.array(bottom['points']['boundary_layer'][-1].coordinates))
                          / config['grid']['regular']['width'])

    inner = Line(begin = top['points']['aerofoil'][0],
                 end = bottom['points']['aerofoil'][-1],
                 transfinite = num_transfinite)

    outer = Circle(begin = top['points']['boundary_layer'][0].id,
                   center = center_point.id,
                   end = bottom['points']['boundary_layer'][-1].id,
                   transfinite = num_transfinite)
    loop = Loop([inner.id,
                 bottom['curves']['normals'][-1].id,
                 - outer.id,
                 - top['curves']['normals'][0].id])
    surface = Surface([loop.id], transfinite = True)

    return {'points': {'center': [center_point]},
            'curves': {'inner_circle': [inner],
                       'outer_circle': [outer]},
            'loops': {'all': [loop]},
            'surfaces': {'all': [surface]}}


def _trailing_edge(top, bottom, config):
    """
    Meshes trailing edge of aerofoil plus its wake.
    :param top: block data structure representing the top of the aerofoil.
    :param bottom: block data structure representing the bottom of the aerofoil.
    :param config: config as dict. See default_config() for details.
    :return: block data structure representing the trailing edge.
    """

    def rectangle(top_left,
                  bottom_left,
                  left_line,
                  horizontal_discretisation,
                  wake_progression = 1):
        """
        :param top_left: top left point of rectangle (existing point)
        :param bottom_left: bottom left point of rectangle (existing point)
        :param left_line: left line of rectangle (existing line)
        :param horizontal_discretisation: horizontal discretisation.
        :param wake_progression: progression on horizontal line from trailing edge aft-wards.
        :return: block data structure representing a rectangle in the trailing edge wake.
        """
        x_dim = 2 * config['grid']['regular']['thickness']
        top_right = Point((x_dim,
                           top_left.coordinates[1],
                           0))
        bottom_right = Point((x_dim,
                              bottom_left.coordinates[1],
                              0))

        transfinite_num = int((x_dim - bottom_left.coordinates[0]) / horizontal_discretisation)

        if transfinite_num < 2:
            transfinite_num = 2

        top_line = Line(top_left,
                        top_right,
                        transfinite = transfinite_num,
                        progression = wake_progression)
        bottom_line = Line(bottom_left,
                           bottom_right,
                           transfinite = transfinite_num,
                           progression = wake_progression)

        if wake_progression is None:
            x = []
            for i in range(0, 4):
                x.append(bottom['points']['aerofoil'][i].coordinates[0])
            d = np.mean(np.diff(np.array(x)))
            top_line.progression_from_width(d)
            bottom_line.progression_from_width(d)

        right_line = Line(bottom_right,
                          top_right,
                          transfinite = left_line.transfinite,
                          progression = left_line.progression)

        loop = Loop([left_line.id,
                     top_line.id,
                     -right_line.id,
                     -bottom_line.id])

        surface = Surface([loop.id], transfinite = True)

        return {'points': {'all': [top_right, bottom_right]},
                'curves': {'all': [top_line, right_line, bottom_line]},
                'loops': {'all': [loop]},
                'surfaces': {'all': [surface]}}

    te_line = Line(top['points']['aerofoil'][-1],
                   bottom['points']['aerofoil'][0])
    te_line.transfinite_from_grid_size(config['grid']['regular']['boundary_layer']['initial_thickness'])

    top_rectangle = rectangle(top_left = top['points']['boundary_layer'][-1],
                              bottom_left = top['points']['aerofoil'][-1],
                              left_line = top['curves']['normals'][-1],
                              horizontal_discretisation = config['grid']['regular']['wake']['width'],
                              wake_progression = config['grid']['regular']['wake']['progression'])

    bottom_rectangle = rectangle(top_left = bottom['points']['boundary_layer'][0],
                                 bottom_left = bottom['points']['aerofoil'][0],
                                 left_line = bottom['curves']['normals'][0],
                                 horizontal_discretisation = config['grid']['regular']['wake']['width'],
                                 wake_progression = config['grid']['regular']['wake']['progression'])

    center_right_line = Line(top_rectangle['points']['all'][1],
                             bottom_rectangle['points']['all'][1])
    center_right_line.transfinite_from_grid_size(config['grid']['regular']['boundary_layer']['initial_thickness'])

    center_loop = Loop([te_line.id,
                        - top_rectangle['curves']['all'][2].id,
                        - center_right_line.id,
                        bottom_rectangle['curves']['all'][2].id])
    center_surface = Surface([center_loop.id], transfinite = True)

    r = top_rectangle
    for key in ['points', 'curves', 'loops', 'surfaces']:
        r[key]['all'] += bottom_rectangle[key]['all']
    r['curves']['trailing_edge'] = [te_line]
    r['curves']['all'] += [center_right_line]
    r['loops']['all'] += [center_loop]
    r['surfaces']['all'] += [center_surface]

    return r
