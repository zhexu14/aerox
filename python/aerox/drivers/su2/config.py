import io


class Config:
    """
    Representation of SU2 config
    """
    def __init__(self):
        self._base_config()

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[ key ] = value

    def __contains__(self, key):
        return key in self._config

    def keys(self):
        return self._config.keys()

    def read(self, file):
        """
        Read config from file.
        :param file: file-like object.
        :return: None
        """
        for line in file:
            line = line.split('%')[0]
            s = line.split('=')
            if len(s) != 2:
                continue
            self._config[s[0].rstrip(' ')] = s[1].lstrip(' ')

    def write(self, file):
        """
        Write config to file.
        :param file: file-like object.
        :return: None
        """
        for key in self._config:
            file.write('{}={}\n'.format(key, self._config[key]))

    def update(self, right):
        for key in right:
            self[key] = right[key]

    def _base_config(self):
        """
        Set up base config
        :return: None
        """
        config_string = """
SOLVER= RANS
KIND_TURB_MODEL= SA
MATH_PROBLEM= DIRECT
TIME_DOMAIN = YES
TIME_MARCHING= DUAL_TIME_STEPPING-2ND_ORDER
TIME_STEP= 5e-4
TIME_ITER= 200
INNER_ITER= 50
MACH_NUMBER= 0.3
AOA= 1.0
REF_DIMENSIONALIZATION = DIMENSIONAL
FREESTREAM_TEMPERATURE= 293.0
REYNOLDS_NUMBER= 1e+3
REYNOLDS_LENGTH= 1.0
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
REF_LENGTH= 1.0
REF_AREA= 0
MARKER_HEATFLUX= (aerofoil, 0.0)
MARKER_FAR= (far_field)
MARKER_PLOTTING= (aerofoil)
MARKER_MONITORING= (aerofoil)
NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES
CFL_NUMBER= 20.0
CFL_ADAPT= NO
CFL_ADAPT_PARAM= (1.5, 0.5, 1.0, 100.0)
RK_ALPHA_COEFF= (0.66667, 0.66667, 1.000000)
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_ERROR= 1E-6
LINEAR_SOLVER_ITER= 5
CONV_NUM_METHOD_FLOW= JST
JST_SENSOR_COEFF= ( 0.5, 0.01)
TIME_DISCRE_FLOW= EULER_IMPLICIT
CONV_NUM_METHOD_TURB= SCALAR_UPWIND
MUSCL_TURB= NO
TIME_DISCRE_TURB= EULER_IMPLICIT
CONV_CRITERIA = RESIDUAL
CONV_FIELD= REL_RMS_DENSITY
CONV_RESIDUAL_MINVAL= -3
WINDOW_CAUCHY_CRIT = YES
CONV_WINDOW_FIELD = (TAVG_DRAG, TAVG_LIFT)
CONV_WINDOW_STARTITER = 0
CONV_WINDOW_CAUCHY_EPS = 1E-3
CONV_WINDOW_CAUCHY_ELEMS = 10
WINDOW_START_ITER = 500
WINDOW_FUNCTION = HANN_SQUARE
HISTORY_WRT_FREQ_INNER=50
SCREEN_WRT_FREQ_INNER=50
MESH_FILENAME=mesh.su2	
MESH_FORMAT= SU2

TABULAR_FORMAT=TECPLOT
CONV_FILENAME=history

WRT_SOL_FREQ=200
WRT_SOL_FREQ_DUALTIME=1
WRT_CON_FREQ_DUALTIME=10
WRT_CON_FREQ=1
WRT_CSV_SOL=NO
SCREEN_OUTPUT=(TIME_ITER, INNER_ITER, AERO_COEFF)
HISTORY_OUTPUT=(ITER, TIME_DOMAIN, AERO_COEFF)
OUTPUT_FILES=(RESTART)
    """
        buffer = io.StringIO()
        buffer.write(config_string)
        buffer.seek(0)
        self.read(buffer)

    _config = {}
