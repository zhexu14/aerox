import matplotlib.pyplot as plt
import numpy as np


class Aerofoil:
    """
    Representation of an aerofoil geometry.
    """
    def __init__(self):
        self.coordinates = []
        self.top = []
        self.bottom = []
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
        self.top = top[1: -1]
        self.bottom = bottom[1: -1]
        self.leading_edge = top[0]
        self.trailing_edge = top[-1]

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
