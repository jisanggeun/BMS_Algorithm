import numpy as np

r_table_array = np.array([
    [0.9999889, 0.075478092254735],
    [0.60362566, 0.05707887345652015],
    [0.12985104, 0.08756416148391949],
    [0.06123932, 0.128216146686215]
])

ocv_array = np.array([
    4.19998, 4.110136, 4.089385, 4.0463243,
    3.9788966, 3.8967965, 3.8467634, 3.793938,
    3.730277, 3.665835, 3.592339, 3.5290298,
    3.4511325, 3.2407937, 2.687574, 2.50000
])

soc_array = np.array([
    0.9999889, 0.857805, 0.7278938, 0.618027,
    0.48295924, 0.36903974, 0.25513136, 0.18300903,
    0.14913777, 0.1171282, 0.09689905, 0.08417945,
    0.07511466, 0.068105, 0.06240614, 0
])

BMS_configuration = {
    "r_array": r_table_array,
    "ocv_array": ocv_array,
    "soc_array": soc_array,
    "degradation_rate": 0.2,
    "capacity": 5,
    "design_capacity": 5,
    "dsg_current_threshold": 0.07,
    "chg_current_threshold": -0.07,
    "relax_dvdt_threshold": 4e-6,
    "relax_time_threshold": 1800,
    "temp_coef": 0.023,
    "temp_ref": 0.0
}