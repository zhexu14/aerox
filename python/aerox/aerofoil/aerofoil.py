import copy
import matplotlib.pyplot as plt
import numpy as np
import sys
import xfoil


class Aerofoil:
    """
    Representation of an aerofoil geometry.
    """
    def __init__(self):
        self.coordinates = [] #  coordinates from leading edge aft, wrapping around trailing edge back to the leading edge
        self.top = [] #  top half of aerofoil from leading edge to trailing edge
        self.bottom = [] #  bottom half of aerofoil from trailing edge to leading edge
        self.leading_edge = None
        self.trailing_edge = None

    def load_from_gnu(self, file):
        """
        Load aerofoil from gnu format output
        :param file: file-like object to read from
        :return: None
        """
        top = []
        bottom = []
        points = top
        for line in file:
            line = line.rstrip('\n')
            line = line[3:]
            s = line.split(' ')
            if len(s) > 2:
                s = [s[0], s[-1]]
            if len(s) < 2:
                points = bottom
                continue
            points.append((float(s[0]), float(s[1])))

        bottom.reverse()
        self.coordinates = top + bottom[1: -1]
        self.top = top[1:]
        self.bottom = bottom[:-1]
        self.leading_edge = top[0]
        self.trailing_edge = (top[-1][0], 0.5*(bottom[-1][1] + top[-1][1]))

    def plot(self):
        """
        Plot aerofoil geometry using matplotlib.

        Example:
        >>> import matplotlib.pyplot as plt
        >>> aerofoil = Aerofoil()
        >>> with open('coordinates.gnu', 'r') as file:
        >>>     aerofoil.load_from_gnu(file)
        >>> aerofoil.plot()
        >>> plt.show()
        :return: None
        """
        c = np.array(self.coordinates)
        plt.plot(c[:, 0], c[:, 1])

    def to_xfoil(self, ostream = sys.stdout):
        """
        Writes aerofoil to x-foil plain file format
        :return: None
        """
        top_reversed = copy.deepcopy(self.top)
        top_reversed.reverse()
        for i in range(len(top_reversed)):
            ostream.write('{} {}\n'.format(top_reversed[i][0], top_reversed[i][1]))

        bottom_reversed = copy.deepcopy(self.bottom)
        bottom_reversed.reverse()
        for i in range(1, len(bottom_reversed)):
            ostream.write('{} {}\n'.format(bottom_reversed[i][0], bottom_reversed[i][1]))

    def to_xfoil_airfoil(self):
        """
        :return: xfoil.xfoil.Airfoil object
        """
        top_reversed = copy.deepcopy(self.top)
        top_reversed.reverse()

        bottom_reversed = copy.deepcopy(self.bottom)
        bottom_reversed.reverse()

        coordinates = np.array(top_reversed + bottom_reversed)
        airfoil = xfoil.xfoil.Airfoil(coordinates[:,0], coordinates[:,1])
        return airfoil
