import numpy as np

from aerofoil import Aerofoil
from aerox.drivers.gmsh.geometry import Circle
from aerox.drivers.gmsh.geometry import Line
from aerox.drivers.gmsh.geometry import Loop
from aerox.drivers.gmsh.geometry import PhysicalCurve
from aerox.drivers.gmsh.geometry import Point
from aerox.drivers.gmsh.geometry import Surface

def default_config():
    return { 'far_field': { 'size': 5.2 },
             'boundary_layer': { 'thickness': 0.2,
                                 'layers': 40,
                                 'leading_edge_discretisation': 40,
                                 'trailing_edge_discretisation': 40 } }


def geometry( aerofoil, config ):

    top = _half_aerofoil( [ aerofoil.leading_edge ] + aerofoil.top + [ aerofoil.trailing_edge ],
                          config )

    bottom = _half_aerofoil( [ aerofoil.trailing_edge ] + aerofoil.bottom + [ aerofoil.leading_edge ],
                              config )

    leading_edge = _leading_edge( top, bottom, config )

    trailing_edge = _trailing_edge( top, bottom, config )

    far_field = _far_field( config )

    far_field_surface = Surface( [ surface.id for surface in top[ 'loops' ][ 'all' ]
                                   + bottom[ 'loops' ][ 'all' ]
                                   + leading_edge[ 'loops' ][ 'all' ]
                                   + trailing_edge[ 'loops' ][ 'all' ]]
                                 + [ far_field['loops']['all'][0].id ] )

    # physical objects
    aerofoil_curve = PhysicalCurve( 'aerofoil',
                                    [ line.id for line in top[ 'curves' ][ 'aerofoil' ] ]
                                    + [ trailing_edge[ 'curves' ][ 'trailing_edge' ][ 0 ].id ]
                                    + [ line.id for line in bottom[ 'curves' ][ 'aerofoil' ] ]
                                    + [ leading_edge[ 'curves' ][ 'inner_circle' ][ 0 ].id ] )
    far_field_curve = PhysicalCurve( 'far_field',
                                     [ line.id for line in far_field[ 'curves' ][ 'all' ] ] )

    return _serialise( top ) \
           + _serialise( bottom ) \
           + _serialise( leading_edge ) \
           + _serialise( trailing_edge ) \
           + _serialise( far_field ) \
           + [ str( far_field_surface ), str( aerofoil_curve ), str( far_field_curve ) ]

def _serialise( block ):
    """
    serialise block data structure
    :param block:
    :return:
    """
    out = []
    for type in [ 'points', 'curves', 'loops', 'surfaces' ]:
        if type not in block:
            continue
        for element in block[ type ]:
            out += [ str( component ) for component in block[ type ][ element ] ]
    return out

def _half_aerofoil( coordinates, config ):
    """
    Constructs half aerofoil
    :param coordinates: coordinates of aerofoil
    :param config: config as dict
    :return:
    """
    aerofoil_points = []
    boundary_points = []

    # points on the aerofoil and boundary layer
    for i in range( 1, len( coordinates ) ):
        first = np.array( [ coordinates[ i - 1 ][ 0 ],
                            coordinates[ i - 1 ][ 1 ],
                            0 ] )
        second = np.array( [ coordinates[ i ][ 0 ],
                             coordinates[ i ][ 1 ],
                             0 ] )
        midpoint = first + 0.5 * ( second - first )
        boundary_point = midpoint + \
                         ( config[ 'boundary_layer' ][ 'thickness' ] \
                           / np.linalg.norm( second - first ) ) \
                         * np.cross( second - first, [ 0, 0, -1 ] )
        aerofoil_points.append( Point( tuple( midpoint ) ) )
        boundary_points.append( Point( tuple( boundary_point ) ) )

    aerofoil_lines = []
    boundary_lines = []
    vertical_lines = [ Line( aerofoil_points[ 0 ],
                             boundary_points[ 0 ],
                             transfinite = config[ 'boundary_layer' ][ 'layers' ] ) ]
    loops = []
    surfaces = []
    for i in range( 1, len( aerofoil_points ) ):
        aerofoil_line = Line( aerofoil_points[ i-1 ], aerofoil_points[ i ], transfinite = 10 )
        boundary_line = Line( boundary_points[ i ], boundary_points[ i - 1 ], transfinite = 10 )
        vertical_line = Line( aerofoil_points[ i ],
                              boundary_points[ i ],
                              transfinite = config[ 'boundary_layer' ][ 'layers' ] )
        aerofoil_lines.append( aerofoil_line )
        boundary_lines.append( boundary_line )
        vertical_lines.append( vertical_line )
        loops.append( Loop( [ aerofoil_lines[ -1 ].id,
                              vertical_lines[ -1 ].id,
                              boundary_lines[ -1 ].id,
                              -1 * vertical_lines[ -2 ].id ] ) )
        surfaces.append( Surface( [ loops[ -1 ].id ], transfinite = True ) )

    return { 'points': { 'aerofoil': aerofoil_points, 'boundary_layer': boundary_points },
             'curves': { 'aerofoil': aerofoil_lines, 'boundary_layer': boundary_lines, 'normals': vertical_lines },
             'loops': { 'all': loops },
             'surfaces': { 'all': surfaces } }

def _leading_edge( top, bottom, config ):
    """
    Meshes leading edge of aerofoil plus its boundary layer
    :param top:
    :param bottom:
    :param config:
    :return:
    """
    def circle_center( top_aerofoil_points, bottom_aerofoil_points ):
        """
        Center of circle that is tangential to front line segment of aerofoil top and bottom.
        :param top_aerofoil_points:
        :param bottom_aerofoil_points:
        :return:
        """
        q = np.array( top_aerofoil_points[ 0 ].coordinates) - np.array(top_aerofoil_points[1].coordinates)
        r = np.array(bottom_aerofoil_points[ -1 ].coordinates) - np.array(bottom_aerofoil_points[-2].coordinates)
        c = np.cross(q, [0, 0, -1]) / np.linalg.norm(q)
        d = np.cross(r, [0, 0, 1]) / np.linalg.norm(r)
        radius = (q[1] - r[1]) / (d[1] - c[1])
        s = q + radius * c
        return Point( tuple( -s ) )

    center_point = circle_center( top[ 'points' ][ 'aerofoil' ], bottom[ 'points' ][ 'aerofoil' ] )
    inner = Circle(begin = top[ 'points' ][ 'aerofoil' ][0].id,
                             center = center_point.id,
                             end = bottom[ 'points' ][ 'aerofoil' ][-1].id,
                             transfinite = config[ 'boundary_layer' ][ 'leading_edge_discretisation' ] )
    outer = Circle(begin = top[ 'points' ][ 'boundary_layer' ][0].id,
                             center = center_point.id,
                             end = bottom[ 'points' ][ 'boundary_layer' ][-1].id,
                             transfinite = config[ 'boundary_layer' ][ 'leading_edge_discretisation' ] )
    loop = Loop( [ inner.id,
                   bottom[ 'curves' ][ 'normals' ][-1].id,
                    - outer.id,
                   - top[ 'curves' ][ 'normals' ][0].id])
    surface = Surface([loop.id], transfinite = True)

    return { 'points': { 'center': [ center_point ] },
             'curves': { 'inner_circle': [ inner ],
                          'outer_circle': [ outer ] },
             'loops': { 'all': [ loop ] },
             'surfaces': { 'all': [ surface ] } }


def _trailing_edge( top, bottom, config ):
    """
    Meshes trailing edge of aerofoil plus its boundary layer    :param top:
    :param bottom:
    :param config:
    :return:
    """
    te_line = Line( top[ 'points' ][ 'aerofoil' ][-1],
                    bottom[ 'points' ][ 'aerofoil' ][0],
                    transfinite = config[ 'boundary_layer' ][ 'trailing_edge_discretisation' ] )
    center_point = Point( ( top[ 'points' ][ 'aerofoil' ][ - 1].coordinates[0],
                             0,
                             0 ) )
    circle = Circle( begin = top[ 'points' ][ 'boundary_layer' ][ -1 ].id,
                     center = center_point.id,
                     end = bottom[ 'points' ][ 'boundary_layer' ][ 0 ].id,
                     transfinite = config[ 'boundary_layer' ][ 'trailing_edge_discretisation' ] )
    loop = Loop( [ top[ 'curves' ][ 'normals' ][-1].id,
                    circle.id,
                    - bottom[ 'curves' ][ 'normals' ][0].id,
                    - te_line.id ] )
    surface = Surface([loop.id], transfinite = True)

    return { 'points': { 'center': [ center_point ] },
             'curves': { 'trailing_edge': [ te_line ],
                          'circle': [ circle ] },
             'loops': { 'all': [ loop ] },
             'surfaces': { 'all': [ surface ] } }

def _far_field( config ):
    """
    Meshes far field
    :param config:
    :return:
    """
    def _points( config ):
        v = config[ 'far_field' ][ 'size' ]
        return [ Point( ( -v, -v, 0 ), 0.1 ),
                 Point( ( -v, v, 0 ), 0.1 ),
                 Point( ( v, v, 0 ), 0.1 ),
                 Point( ( v, -v, 0 ), 0.1 ) ]

    def _lines( points, closed = True, transfinite = None ):
        """
        :param points: ordered list of Point objects forming a closed loop
        :param closed: if True, close a loop
        :return: array of Line objects that draw the closed loop
        """
        lines = []
        for i in range( 1, len( points ) ):
            lines.append( Line( points[ i - 1 ], points[ i ], transfinite ) )
        if closed:
            lines.append( Line( points[ -1 ], points[ 0 ], transfinite ) )
        return lines

    def _loop( lines ):
        """
        :param lines: list of Line objects that forms the loop
        :return: Loop object
        """
        elements = []
        for line in lines:
            elements.append( line.id )
        return Loop( elements )

    points = _points(config)
    lines = _lines( points )
    loop = _loop( lines )

    return { 'points': { 'all': points },
             'curves': { 'all': lines },
             'loops': { 'all': [ loop ] } }

def geometry_old( aerofoil, config ):

    def _aerofoil_points( coordinates ):
        """
        :param coordinates: aerofoil coordinates
        :return: list of Point objects
        """
        points = []
        for coordinate in coordinates:
            points.append( Point( ( coordinate[ 0 ], coordinate[ 1 ], 0 ) ) )
        return points

    def _boundary_layer_points( aerofoil, config ):
        top_points = []
        for coordinate in [ aerofoil.leading_edge ] + aerofoil.top + [ aerofoil.trailing_edge ]:
            top_points.append( Point( ( coordinate[ 0 ],
                                        coordinate[ 1 ] + config[ 'boundary_layer' ][ 'thickness' ],
                                        0 ) ) )
        top_points += [ Point( ( aerofoil.trailing_edge[ 0 ] + config[ 'boundary_layer' ][ 'trailing_edge_structured' ],
                                 config[ 'boundary_layer' ][ 'thickness' ],
                                 0 ) ) ]

        bottom_points = [ Point( ( aerofoil.trailing_edge[ 0 ] + config[ 'boundary_layer' ][ 'trailing_edge_structured' ],
                                    - config[ 'boundary_layer' ][ 'thickness' ],
                                    0 ) ) ]
        for coordinate in [ aerofoil.trailing_edge ] + aerofoil.bottom + [ aerofoil.leading_edge ]:
            bottom_points.append( Point( ( coordinate[ 0 ],
                                           coordinate[ 1 ] - config[ 'boundary_layer' ][ 'thickness' ],
                                           0 ) ) )

        return top_points + bottom_points

    def _lines( points, closed = True, transfinite = None ):
        """
        :param points: ordered list of Point objects forming a closed loop
        :param closed: if True, close a loop
        :return: array of Line objects that draw the closed loop
        """
        lines = []
        for i in range( 1, len( points ) ):
            lines.append( Line( points[ i - 1 ], points[ i ], transfinite ) )
        if closed:
            lines.append( Line( points[ -1 ], points[ 0 ], transfinite ) )
        return lines

    def _far_field_points( config ):
        v = config[ 'far_field' ]
        return [ Point( ( -v, -v, 0 ) ),
                 Point( ( -v, v, 0 ) ),
                 Point( ( v, v, 0 ) ),
                 Point( ( v, -v, 0 ) ) ]

    def _loop( lines ):
        """
        :param lines: list of Line objects that forms the loop
        :return: Loop object
        """
        elements = []
        for line in lines:
            elements.append( line.id )
        return Loop( elements )

    aerofoil_points = _aerofoil_points( aerofoil.coordinates )
    far_field_points = _far_field_points( config )
    aerofoil_lines = _lines( aerofoil_points, transfinite = 0.01 )
    far_field_lines = _lines( far_field_points )
    boundary_layer_points = _boundary_layer_points( aerofoil, config )
    boundary_layer_lines = _lines( boundary_layer_points, closed = False )
    boundary_layer_circle_center = Point( ( aerofoil.leading_edge[ 0 ] + 0.00001,
                                            aerofoil.leading_edge[ 1 ],
                                            0 ) )
    boundary_layer_leading_edge = Circle( boundary_layer_points[ 0 ].id,
                                          boundary_layer_circle_center.id,
                                          boundary_layer_points[ -1 ].id )

    out = ["""SetFactory("OpenCASCADE");""" ]
    for point in aerofoil_points + far_field_points + boundary_layer_points + [ boundary_layer_circle_center ]:
        out.append( str( point ) )
    for line in aerofoil_lines + far_field_lines + boundary_layer_lines:
        out.append( str( line ) )
    out.append( str( boundary_layer_leading_edge ) )
    out.append( str( _loop( aerofoil_lines ) ) )
    out.append( str( _loop( far_field_lines ) ) )
    out.append( str( _loop( boundary_layer_lines + [ boundary_layer_leading_edge ] ) ) )

    return out

if __name__ == '__main__':
    aerofoil = Aerofoil()
    with open( '/home/zxu02/src/naca/65-110.csv' ) as fd:
        coordinates = aerofoil.load_from_gnu( fd )
        out = geometry( aerofoil, default_config() )
        print( '\n'.join( out ) )