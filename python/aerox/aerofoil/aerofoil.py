
class Aerofoil:

    def __init__(self):
        self.coordinates = []
        self.top = []
        self.bottom = []
        self.leading_edge = None
        self.trailing_edge = None

    def load_from_gnu(self, file):
        top = []
        bottom = []
        points = top
        for line in file:
            line = line.rstrip( '\n' )
            s = line.split( ',' )
            if len( s ) < 2:
                points = bottom
                continue
            points.append( ( float( s[ 0 ] ), float( s[ 1 ] ) ) )

        bottom.reverse()
        self.coordinates = top + bottom[ 1: -1 ]
        self.top = top[ 1: -1 ]
        self.bottom = bottom[ 1: -1 ]
        self.leading_edge = top[ 0 ]
        self.trailing_edge = top[ -1 ]
