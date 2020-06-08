"""
This module implements classes representing gmsh primitives
"""


class Point:
    """
    Point
    """

    def __init__( self, coordinates, grid_size = None ):
        self.id = self._next_id
        Point._next_id += 1
        self.coordinates = coordinates
        self.grid_size = grid_size

    def __str__( self ):
        grid_size = ''
        if self.grid_size is not None:
            grid_size = ', {}'.format( self.grid_size )
        return 'Point( {id} ) = {{ {x}, {y}, {z} {grid_size} }};'.format( id = self.id,
                                                                          x = self.coordinates[ 0 ],
                                                                          y = self.coordinates[ 1 ],
                                                                          z = self.coordinates[ 2 ],
                                                                          grid_size = grid_size )

    _next_id = 1


class Curve:
    """
    Base class for all curves
    """

    def __init__( self ):
        self.id = self._next_id
        Curve._next_id += 1

    _next_id = 1


class Line( Curve ):
    """
    Lines
    """

    def __init__( self, begin, end, transfinite = None ):
        super( Line, self ).__init__()
        self.begin = begin
        self.end = end
        self.transfinite = transfinite

    def __str__( self ):
        transfinite_statement = ''
        if self.transfinite is not None:
            transfinite_statement = 'Transfinite Line {{ {id} }} = {n} Using Progression 1;'.format( id = self.id,
                                                                                                     n = self.transfinite )
        return 'Line( {id} ) = {{ {begin}, {end} }}; {transfinite}'.format( id = self.id,
                                                                            begin = self.begin.id,
                                                                            end = self.end.id,
                                                                            transfinite = transfinite_statement )


class Circle( Curve ):
    """
    Circle arc
    """

    def __init__( self, center, begin, end, transfinite = None ):
        super( Circle, self ).__init__()
        self.center = center
        self.begin = begin
        self.end = end
        self.transfinite = transfinite

    def __str__( self ):
        transfinite_statement = ''
        if self.transfinite is not None:
            transfinite_statement = 'Transfinite Line {{ {id} }} = {n} Using Progression 1;'.format( id = self.id,
                                                                                                     n = self.transfinite )
        return 'Circle( {id} ) = {{ {begin}, {center}, {end} }}; {t}'.format( id = self.id,
                                                                              center = self.center,
                                                                              begin = self.begin,
                                                                              end = self.end,
                                                                              t = transfinite_statement )


class Loop( Curve ):
    """
    Curve loop
    """
    def __init__( self, elements ):
        super( Loop, self ).__init__()
        self.elements = elements

    def __str__( self ):
        return 'Curve Loop( {id} ) = {{ {s} }};'.format( id = self.id, s = ','.join( [ str( v ) for v in self.elements ] ) )


class Surface:
    """
    Plane surface
    """
    def __init__( self, elements, transfinite = False ):
        self.id = self._next_id
        Surface._next_id += 1
        self.elements = elements
        self.transfinite = transfinite

    def __str__( self ):
        transfinite_statement = ''
        if self.transfinite:
            transfinite_statement = 'Transfinite Surface{{ {id} }}; Recombine Surface{{ {id} }};'.format( id = self.id )
        return 'Plane Surface( {id} ) = {{ {s} }}; {t}'.format( id = self.id,
                                                                s = ','.join( [ str( v ) for v in self.elements ] ),
                                                                t = transfinite_statement )

    _next_id = 1


class PhysicalCurve:
    """
    Physical curve
    """

    def __init__( self, name, elements ):
        self.name = name
        self.elements = elements

    def __str__( self ):
        return 'Physical Curve( "{name}" ) = {{ {s} }};'.format( name = self.name,
                                                                 s = ','.join( [ str( v ) for v in self.elements ] ) )


class PhysicalSurface:
    """
    Physical curve
    """

    def __init__( self, name, elements ):
        self.name = name
        self.elements = elements

    def __str__( self ):
        return 'Physical Surface( "{name}" ) = {{ {s} }};'.format( name = self.name,
                                                                   s = ','.join( [ str( v ) for v in self.elements ] ) )