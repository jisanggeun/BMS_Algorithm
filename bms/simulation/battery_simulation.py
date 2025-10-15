import liionpack as lp
import pybamm
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

def load_drive_cycles():
    os.chdir(pybamm.__path__[0] + "/..")
    return [
        # pd.read_csv("pybamm/input/drive_cycles/compare3.csv", comment="#", header=None).to_numpy(),
        pd.read_csv("pybamm/input/drive_cycles/test3.csv", comment="#", header=None).to_numpy(),
    ]

class BatterySimulation:
    def __init__(self, I_mag, OCV_init, Ri_init, R_busbar, R_connection, Np, Ns, initial_soc,
                 output_file="/home/sanggeun/battery/output_log2.csv",
                 soc_log="/home/sanggeun/battery/soc_log.csv"):
        """
        배터리 시뮬레이션 파라미터 초기화
        """
        self.I_mag = I_mag
        self.OCV_init = OCV_init
        self.Ri_init = Ri_init
        self.R_busbar = R_busbar
        self.R_connection = R_connection
        self.Np = Np
        self.Ns = Ns
        self.initial_soc = initial_soc

        self.parameter_values = None
        self.netlist = None
        self.experiment = None
        self.output = None

        self.output_file = output_file
        self.soc_log = soc_log
        self.drive_cycles = load_drive_cycles()

    def setup_circuit(self):
        """
        회로 설정 
        """
        self.parameter_values = pybamm.ParameterValues("Chen2020")
        self.netlist = lp.setup_circuit(
            Np=self.Np, Ns=self.Ns, Rb=self.R_busbar, Rc=self.R_connection
        )

    def draw_circuit(self, **kwargs):
        """
        회로 출력
        """
        lp.draw_circuit(self.netlist, cpt_size=kwargs.get("cpt_size", 1.0),
                        dpi=kwargs.get("dpi", 150), node_spacing=kwargs.get("node_spacing", 2.5))

    def setup_experiment(self):
        '''
        초기 실험 Setup
        '''
        self.experiment = pybamm.Experiment(
            [pybamm.step.current(dc) for dc in self.drive_cycles],
            period="1 second",
        )

    def _sei_degradation_with_temperature_model(self, parameter_values=None):
        model = pybamm.lithium_ion.SPM(
            options={
                "SEI": "ec reaction limited",
                "SEI film resistance": "distributed",
                "SEI porosity change": "true",
                "thermal": "lumped",
            }
        )
        model = lp.add_events_to_model(model)

        if parameter_values is None:
            parameter_values = pybamm.ParameterValues("Chen2020")

        parameter_values.update({
            "Ambient temperature [K]": 298.15,
            "Total heat transfer coefficient [W.m-2.K-1]": 10.0,
            "Initial temperature [K]": 298.15,
            "Separator thermal conductivity [W.m-1.K-1]": 0.344,
            "Positive electrode thermal conductivity [W.m-1.K-1]": 1.0,
            "Negative electrode thermal conductivity [W.m-1.K-1]": 1.0,
        })

        solver = pybamm.CasadiSolver(mode="safe")
        sim = pybamm.Simulation(
            model=model,
            parameter_values=self.parameter_values,
            solver=solver,
        )
        return sim

    def run_simulation(self):
        """
        시뮬레이션 실행
        """
        output_variables = [
            "Terminal voltage [V]",
            "X-averaged cell temperature [K]",
            "Battery open-circuit voltage [V]",
        ]
        self.output = lp.solve(
            netlist=self.netlist,
            parameter_values=self.parameter_values,
            experiment=self.experiment,
            sim_func=self._sei_degradation_with_temperature_model,
            output_variables=output_variables,
            initial_soc=self.initial_soc,
        )

    def get_results(self):
        """
        시뮬레이션 결과에서 필요한 정보만 출력
        """
        if self.output is None:
            print("No output to save.")
            return

        for i in range(len(self.output["Time [s]"])):
            row = {
                "Time [s]": [self.output["Time [s]"][i]],
                "Cell current [A]": [self.output["Cell current [A]"][i]],
                "Terminal voltage [V]": [self.output["Terminal voltage [V]"][i]],
                "X-averaged cell temperature [K]": [self.output["X-averaged cell temperature [K]"][i]],
                "Battery open-circuit voltage [V]": [self.output["Battery open-circuit voltage [V]"][i]],
                "Cell internal resistance [Ohm]": [self.output["Cell internal resistance [Ohm]"][i]],
            }
            df = pd.DataFrame(row)
            df.to_csv(self.output_file, mode="a", header=not os.path.exists(self.output_file), index=False)

    def plot_results(self):
        """
        시뮬레이션 결과 Plot
        """
        if self.output is not None:
            lp.plot_output(self.output)
            plt.show()

    def discharge_and_log_soc_ocv_curve(self):
        soc_ocv_data = []
        total_capacity = self.Np * 5  # 배터리 총 용량 (예시)
        soc = [self.initial_soc]
        prev_t = self.output["Time [s]"][0]

        for i in range(1, len(self.output["Time [s]"])):
            current = self.output["Cell current [A]"][i] # 각 time step의 전류 값
            t_now = self.output["Time [s]"][i]
            dt = t_now - prev_t
            prev_t = t_now
            ocv = self.output["Battery open-circuit voltage [V]"][i] # 각 time step의 OCV 값

            # SOC 계산 (Coulomb Counting 방식)
            soc_t = soc[-1] - (current * dt) / (total_capacity * 3600)
            soc_t = max(0.0, soc_t)
            soc.append(soc_t)
            soc_ocv_data.append((soc_t, ocv))
            if soc_t <= 0:
                break

        # SOC와 OCV pair 저장
        df = pd.DataFrame(soc_ocv_data, columns=["SOC", "OCV"])
        df.to_csv(self.soc_log.replace("soc_log.csv", "soc_ocv_curve.csv"), index=False)
        print("SOC-OCV 곡선 저장 완료.")

    def get_ocv_from_output(self):
        csv_path = self.soc_log.replace("soc_log.csv", "soc_ocv_curve.csv")
        try:
            soc_ocv_df = pd.read_csv(csv_path)
        except FileNotFoundError:
            print(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            return None

        # output_log2.csv 읽기 (헤더 없는 경우를 대비해 names 지정)
        column_names = [
            "Time [s]", "Cell current [A]", "Terminal voltage [V]",
            "X-averaged cell temperature [K]", "Battery open-circuit voltage [V]", "Pack terminal voltage [V]"
        ]
        try:
            output_df = pd.read_csv(self.output_file, header=None, names=column_names)
        except FileNotFoundError:
            print(f"CSV 파일을 찾을 수 없습니다: {self.output_file}")
            return None

        def clean(x):
            if isinstance(x, str):
                x = x.strip("[]")
            return float(x)

        try:
            soc_ocv_df["OCV"] = soc_ocv_df["OCV"].apply(clean)
            soc_ocv_df["SOC"] = soc_ocv_df["SOC"].apply(clean)
        except Exception as e:
            print(f"데이터 정리 중 오류: {e}")
            return None

        soc_ocv_df = soc_ocv_df.sort_values("OCV").drop_duplicates(subset="OCV")
        results = []

        ocv_vals = soc_ocv_df["OCV"].values
        soc_vals = soc_ocv_df["SOC"].values

        for ocv in output_df["Battery open-circuit voltage [V]"].dropna():
            ocv = clean(ocv)
            # 범위 밖이면 스킵
            if ocv < ocv_vals.min() or ocv > ocv_vals.max():
                continue
            # 선형 보간
            idx = np.searchsorted(ocv_vals, ocv)  # 오름차순 가정
            idx = np.clip(idx, 1, len(ocv_vals) - 1)
            x1, x2 = ocv_vals[idx - 1], ocv_vals[idx]
            y1, y2 = soc_vals[idx - 1], soc_vals[idx]
            soc = y1 + (ocv - x1) * (y2 - y1) / (x2 - x1)
            results.append({"OCV": ocv, "SOC": soc})

        res_df = pd.DataFrame(results)
        res_df.to_csv(self.soc_log, index=False)
        print(f"SOC 로그 저장: {self.soc_log}")
        return res_df
