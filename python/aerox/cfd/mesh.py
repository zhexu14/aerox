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
    - far_field/size: half-dimensions of the far field. The far field is a square at +/- this size from the leading
                      edge of the aerofoil.

    Boundary layer
    - boundary_layer/thickness: boundary layer thickness.
    - boundary_layer/layers, discretisation: the layers and discretisation parameters define the regular discretisation
                                             of the boundary layer along the axes normal and tangential to the aerofoil
                                             surface respectively. The below example has layers = 3 and
                                             discretisation = 7.
                                              _ _ _ _ _ _
                                             |_|_|_|_|_|_| boundary layer
                                             |_|_|_|_|_|_|
                                             |_|_|_|_|_|_|
                                             Segment of aerofoil surface
    - boundary_layer/leading_edge_discretisation: the number of regular radial cells to use when meshing along the
                                                  leading edge surface.
    - boundary_layer/trailing_edge_discretisation: the number of regular cells to model the wake with.
    :return: default config as dict.
    """
    return {'far_field': {'size': 5.2},
            'boundary_layer': {'thickness': 0.2,
                               'layers': 40,
                               'leading_edge_discretisation': 4,
                               'trailing_edge_discretisation': 200,
                               'discretisation': 2}}


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

    far_field = _far_field(config)

    far_field_surface = Surface([surface.id for surface in top['loops']['all']
                                 + bottom['loops']['all']
                                 + leading_edge['loops']['all']
                                 + trailing_edge['loops']['all']]
                                 + [far_field['loops']['all'][0].id])

    # physical objects
    aerofoil_curve = PhysicalCurve('aerofoil',
                                    [line.id for line in top['curves']['aerofoil']]
                                    + [trailing_edge['curves']['trailing_edge'][0].id]
                                    + [line.id for line in bottom['curves']['aerofoil']]
                                    + [leading_edge['curves']['inner_circle'][0].id])
    far_field_curve = PhysicalCurve('far_field',
                                    [line.id for line in far_field['curves']['all']])
    physical_surface = PhysicalSurface('dummy',
                                       [surface.id for surface in top['surfaces']['all']
                                                                    + bottom['surfaces']['all']
                                                                    + leading_edge['surfaces']['all']
                                                                    + trailing_edge['surfaces']['all']]
                                       + [far_field_surface.id])

    return _serialise(top) \
           + _serialise(bottom) \
           + _serialise(leading_edge) \
           + _serialise(trailing_edge) \
           + _serialise(far_field) \
           + [str(far_field_surface), str(aerofoil_curve), str(far_field_curve), str(physical_surface)]

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
    aerofoil_points = []
    boundary_points = []

    # points on the aerofoil and boundary layer
    for i in range(1, len(coordinates)):
        first = np.array([coordinates[i - 1][0], coordinates[i - 1][1], 0])
        second = np.array([coordinates[i][0], coordinates[i][1], 0])
        midpoint = first + 0.5 * (second - first)
        boundary_point = midpoint + \
                         (config['boundary_layer']['thickness'] / np.linalg.norm(second - first)) \
                         * np.cross(second - first, [0, 0, -1])
        if boundary_point[0] > 0.7 and boundary_point[0] < midpoint[0]: #  hack to handle reflexed aerofoils
            boundary_point[0] = midpoint[0]
        aerofoil_points.append(Point(tuple(midpoint)))
        boundary_points.append(Point(tuple(boundary_point)))

    aerofoil_lines = []
    boundary_lines = []
    vertical_lines = [Line(aerofoil_points[0], boundary_points[0], transfinite = config['boundary_layer']['layers'])]
    loops = []
    surfaces = []
    for i in range(1, len(aerofoil_points)):
        aerofoil_line = Line(aerofoil_points[i-1],
                             aerofoil_points[i],
                             transfinite = config['boundary_layer']['discretisation'])
        boundary_line = Line(boundary_points[i],
                             boundary_points[i - 1],
                             transfinite = config['boundary_layer']['discretisation'])
        vertical_line = Line(aerofoil_points[i],
                             boundary_points[i],
                             transfinite = config['boundary_layer']['layers'])
        aerofoil_lines.append(aerofoil_line)
        boundary_lines.append(boundary_line)
        vertical_lines.append(vertical_line)
        loops.append(Loop([aerofoil_lines[-1].id,
                           vertical_lines[-1].id,
                           boundary_lines[-1].id,
                           -1 * vertical_lines[-2].id]))
        surfaces.append(Surface([loops[-1].id], transfinite = True))

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

    inner = Line(begin = top['points']['aerofoil'][0],
                 end = bottom['points']['aerofoil'][-1],
                 transfinite = config['boundary_layer']['leading_edge_discretisation'])
    outer = Circle(begin = top['points']['boundary_layer'][0].id,
                   center = center_point.id,
                   end = bottom['points']['boundary_layer'][-1].id,
                   transfinite = config['boundary_layer']['leading_edge_discretisation'])
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
    :param top: coordinates of the top of the aerofoil.
    :param bottom: coordinates of the top of the aerofoil.
    :param config: config as dict. See default_config() for details.
    :return: block data structure representing the trailing edge.
    """

    def rectangle(top_left, bottom_left, left_line, vertical_discretisation, horizontal_discretisation):
        """
        :param top_left: top left point of rectangle (existing point)
        :param bottom_left: bottom left point of rectangle (existing point)
        :param left_line: left line of rectangle (existing line)
        :param vertical_discretisation: vertical discretisation, should match the discretisation of left_line.
        :param horizontal_discretisation: horizontal discretisation.
        :return: block data structure representing a rectangle in the trailing edge wake.
        """
        top_right = Point((config['far_field']['size'] - 0.5,
                           top_left.coordinates[1],
                           0))
        bottom_right = Point((config['far_field']['size'] - 0.5,
                              bottom_left.coordinates[1],
                              0))

        top_line = Line(top_left,
                        top_right,
                        transfinite = horizontal_discretisation)
        bottom_line = Line(bottom_right,
                           bottom_left,
                           transfinite = horizontal_discretisation)
        right_line = Line(top_right,
                          bottom_right,
                          transfinite = vertical_discretisation)

        loop = Loop([left_line.id,
                     top_line.id,
                     right_line.id,
                     bottom_line.id])

        surface = Surface([loop.id], transfinite = True)

        return {'points': {'all': [top_right, bottom_right]},
                'curves': {'all': [top_line, right_line, bottom_line]},
                'loops': {'all': [loop]},
                'surfaces': {'all': [surface]}}
    
    te_line = Line(top['points']['aerofoil'][-1],
                   bottom['points']['aerofoil'][0],
                   transfinite = 2)

    top_rectangle = rectangle(top_left = top['points']['boundary_layer'][-1],
                              bottom_left = top['points']['aerofoil'][-1],
                              left_line = top['curves']['normals'][-1],
                              vertical_discretisation = config['boundary_layer']['layers'],
                              horizontal_discretisation = config['boundary_layer']['trailing_edge_discretisation'])

    bottom_rectangle = rectangle(top_left = bottom['points']['boundary_layer'][0],
                                 bottom_left = bottom['points']['aerofoil'][0],
                                 left_line = bottom['curves']['normals'][0],
                                 vertical_discretisation = config['boundary_layer']['layers'],
                                 horizontal_discretisation = config['boundary_layer']['trailing_edge_discretisation'])


    center_right_line = Line(top_rectangle['points']['all'][1],
                             bottom_rectangle['points']['all'][1],
                             transfinite = 2)
    center_loop = Loop([te_line.id,
                        top_rectangle['curves']['all'][2].id,
                        - center_right_line.id,
                        - bottom_rectangle['curves']['all'][2].id])
    center_surface = Surface([center_loop.id], transfinite = True)

    r = top_rectangle
    for key in ['points', 'curves', 'loops', 'surfaces']:
        r[key]['all'] += bottom_rectangle[key]['all']
    r['curves']['trailing_edge'] = [te_line]
    r['curves']['all'] += [center_right_line]
    r['loops']['all'] += [center_loop]
    r['surfaces']['all'] += [center_surface]

    return r


def _far_field(config):
    """
    Meshes far field
    :param config: config as dict. See default_config() for details.
    :return: block data structure representing far field.
    """
    def _points(config):
        v = config['far_field']['size']
        return [Point((-v, -v, 0), 0.1),
                Point((-v, v, 0), 0.1),
                Point((v, v, 0), 0.1),
                Point((v, -v, 0), 0.1)]

    def _lines(points, closed = True, transfinite = None):
        """
        :param points: ordered list of Point objects forming a closed loop
        :param closed: if True, close a loop
        :return: array of Line objects that draw the closed loop
        """
        lines = []
        for i in range(1, len(points)):
            lines.append(Line(points[i - 1], points[i], transfinite))
        if closed:
            lines.append(Line(points[-1], points[0], transfinite))
        return lines

    def _loop(lines):
        """
        :param lines: list of Line objects that forms the loop
        :return: Loop object
        """
        elements = []
        for line in lines:
            elements.append(line.id)
        return Loop(elements)

    points = _points(config)
    lines = _lines(points)
    loop = _loop(lines)

    return {'points': {'all': points},
            'curves': {'all': lines},
            'loops': {'all': [loop]}}
