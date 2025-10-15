from simulation.battery_simulation import BatterySimulation
from adc.adc_module import ADC
from utils.io_pipeline import run_bms, compute_MSE

test_soc = 1.0
np_value = 1
capacity = 5
output_csv_file = "/home/sanggeun/battery/simulation_data1.csv"

# Simulation 
simulation = BatterySimulation(
    I_mag=5,
    OCV_init=3.6,
    Ri_init=5e-2,
    R_busbar=1.5e-3,
    R_connection=1e-2,
    Np=1,
    Ns=1,
    initial_soc=test_soc,
)
simulation.setup_circuit()
# simulation.draw_circuit()
simulation.setup_experiment()
simulation.run_simulation()
simulation.get_results()
simulation.plot_results()
simulation.get_ocv_from_output()
print("SIM COM")

# ADC Quantization
my_ADC = ADC()
quantized_path = my_ADC.run()
print("ADC COM")

# BMS Config & Test
BMS_configuration = {
    "charging_eta": 1.0,
    "discharging_eta": 1.0,
    "alpha": 0.5,
    "r_file": "/home/sanggeun/battery/reduced_r_table.csv",
    "soc_ocv_file": "/home/sanggeun/battery/reduced_soc_ocv_curve.csv",
}

run_bms(
    initial_soc=test_soc,
    np_value=np_value,
    capacity=capacity,
    BMS_configuration=BMS_configuration,
    csv_file_path=quantized_path,
    output_csv_file=output_csv_file,
)
print("BMS COM")

# MSE Calculate
compute_MSE("/home/sanggeun/battery/soc_log.csv", output_csv_file)
# simulation.discharge_and_log_soc_ocv_curve()