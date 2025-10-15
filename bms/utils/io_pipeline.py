import numpy as np
import pandas as pd


def load_table(BMS_configuration):
    # R table
    r_rows = []
    with open(BMS_configuration["r_file"], "r") as f:
        next(f)
        for line in f:
            soc, r = line.strip().split(",")
            r_rows.append([float(soc.strip("[]")), float(r.strip("[]"))])
    BMS_configuration["r_table"] = np.array(r_rows)

    # SOC–OCV table
    so_rows = []
    with open(BMS_configuration["soc_ocv_file"], "r") as f:
        next(f)
        for line in f:
            soc, ocv = line.strip().split(",")
            so_rows.append([float(soc.strip("[]")), float(ocv.strip("[]"))])
    BMS_configuration["soc_ocv_table"] = np.array(so_rows)


def decode(quantized, adc_min, adc_max, q_levels):
    rng = adc_max - adc_min
    return adc_min + (quantized / (q_levels - 1)) * rng


def process_quantized_data(csv_file_path, adc):
    df = pd.read_csv(csv_file_path)
    cur_q = df["Quantized Cell current [A]"].astype(float).values
    vol_q = df["Quantized Terminal voltage [V]"].astype(float).values
    tmp_q = df["Quantized X-averaged cell temperature [K]"].astype(float).values

    current = decode(cur_q, adc["current_min"], adc["current_max"], adc["q_levels"])
    voltage = decode(vol_q, adc["voltage_min"], adc["voltage_max"], adc["q_levels"])
    temp = decode(tmp_q, adc["temp_min"], adc["temp_max"], adc["q_levels"])
    t = df["Time [s]"].astype(float).values
    return current, voltage, temp, t


def run_bms(initial_soc, np_value, capacity, BMS_configuration, csv_file_path, output_csv_file):
    from bms.mybms_module import MyBMS

    adc = {
        "q_levels": 2 ** 16,
        "current_min": -9, "current_max": 9,
        "voltage_min": 2.33, "voltage_max": 4.37,
        "temp_min": 224.15, "temp_max": 332.15,
    }

    load_table(BMS_configuration)
    my_bms = MyBMS(initial_soc, np_value, capacity, BMS_configuration)

    cur, vol, tmp, t = process_quantized_data(csv_file_path, adc)
    soc = my_bms.estimate_soc(cur, vol, tmp, t, mode="current-voltage")

    out = pd.DataFrame({
        "Time [s]": t,
        "Decoded cell current": cur,
        "Decoded terminal voltage": vol,
        "Decoded temperature": tmp,
        "SOC": soc
    })
    out.to_csv(output_csv_file, mode="a", index=False)
    print(f"Final SOC: {soc[-1]:.6f}")


def compute_MSE(sim_result_csv, bms_result_csv):
    try:
        sim_df = pd.read_csv(sim_result_csv)
        sim_soc = sim_df["SOC"].values
    except FileNotFoundError:
        print(f"BatterySimulation 결과 파일을 찾을 수 없습니다: {sim_result_csv}")
        return None

    try:
        bms_df = pd.read_csv(bms_result_csv)
        bms_soc = bms_df["SOC"].values
    except FileNotFoundError:
        print(f"MyBMS 결과 파일을 찾을 수 없습니다: {bms_result_csv}")
        return None

    n = min(len(sim_soc), len(bms_soc))
    sim_soc, bms_soc = sim_soc[:n], bms_soc[:n]

    se = (sim_soc - bms_soc) ** 2
    mse = float(se.mean())
    idx = int(se.argmax())
    print(f"MSE: {mse}")
    print(f"최대 오차: {se[idx]} (Index: {idx})")
    print(f"OCV_SOC: {sim_soc[idx]}, BMS_SOC: {bms_soc[idx]}")
    return mse, float(se[idx]), idx