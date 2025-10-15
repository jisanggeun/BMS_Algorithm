import numpy as np
import pandas as pd


class ADC:
    def __init__(self, adc_bits=16,
                 current_adc_min=-9, current_adc_max=9,
                 voltage_adc_min=2.33, voltage_adc_max=4.37,
                 temp_adc_min=224.15, temp_adc_max=332.15,
                 gaussian_sigma=1, random_seed=42,
                 log_file="/home/sanggeun/battery/output_log2.csv",
                 output_file="/home/sanggeun/battery/quantized_log.csv"):
        """
        ADC 클래스 초기화
        Args:
            adc_bits (int): ADC 비트 수 (기본값: 16)
            current_adc_min (float): 전류 ADC의 최소값
            current_adc_max (float): 전류 ADC의 최대값
            voltage_adc_min (float): 전압 ADC의 최소값
            voltage_adc_max (float): 전압 ADC의 최대값
            temp_adc_min (float): 온도 ADC의 최소값 (K)
            temp_adc_max (float): 온도 ADC의 최대값 (K)
            gaussian_sigma (float): Gaussian 노이즈의 표준편차 스케일 (기본값: 1)
            random_seed (int): 난수 생성기의 시드값 (기본값: 42)
        """
        self.log_file = log_file
        self.output_file = output_file
        self.adc_bits = adc_bits

        self.current_adc_min = current_adc_min
        self.current_adc_max = current_adc_max
        self.voltage_adc_min = voltage_adc_min
        self.voltage_adc_max = voltage_adc_max
        self.temp_adc_min = temp_adc_min
        self.temp_adc_max = temp_adc_max

        self.gaussian_sigma = gaussian_sigma
        self.random_seed = random_seed
        np.random.seed(self.random_seed)

        # 최소 resolution 및 표준편차 계산
        self.current_min_resolution = (self.current_adc_max - self.current_adc_min) / (2 ** self.adc_bits)
        self.voltage_min_resolution = (self.voltage_adc_max - self.voltage_adc_min) / (2 ** self.adc_bits)
        self.temp_min_resolution = (self.temp_adc_max - self.temp_adc_min) / (2 ** self.adc_bits)

        self.current_noise_std_dev = self.current_min_resolution * 5
        self.voltage_noise_std_dev = self.voltage_min_resolution * 5
        self.temp_noise_std_dev = self.temp_min_resolution * 5

    def add_noise(self, data, data_type="Cell current [A]"):
        """
        Gaussian 노이즈 추가
        Args:
            data: 노이즈를 추가할 데이터 (numpy 배열)
            data_type: 데이터 유형 ("current", "voltage", "temperature")
        Returns:
            노이즈가 추가된 데이터
        """
        if data_type == "Cell current [A]":
            noise = np.random.normal(0, self.current_noise_std_dev, data.shape)
        elif data_type == "Terminal voltage [V]":
            noise = np.random.normal(0, self.voltage_noise_std_dev, data.shape)
        elif data_type == "X-averaged cell temperature [K]":
            noise = np.random.normal(0, self.temp_noise_std_dev, data.shape)
        else:
            raise ValueError("Unsupported data_type")
        return data + noise

    def quantize_data(self, data, data_type="Cell current [A]"):
        """
        input data를 ADC 비트 수에 맞게 양자화
        Args:
            data (numpy.array): 양자화할 데이터
            data_type (str): 데이터 유형 ("Cell current [A]", "Terminal voltage [V]", "X-averaged cell temperature [K]")
        Returns:
            numpy.array: 양자화된 정수 데이터
        """
        if data_type == "Cell current [A]":
            adc_min, adc_max = self.current_adc_min, self.current_adc_max
        elif data_type == "Terminal voltage [V]":
            adc_min, adc_max = self.voltage_adc_min, self.voltage_adc_max
        else:
            adc_min, adc_max = self.temp_adc_min, self.temp_adc_max

        q_levels = 2 ** self.adc_bits
        rng = adc_max - adc_min
        clipped = np.clip(data, adc_min, adc_max)
        scaled = (clipped - adc_min) / rng * (q_levels - 1)
        return np.floor(scaled).astype(int)

    def process_adc_data(self):
        """
        log file 읽어 노이즈 추가 --> 양자화 --> 저장
        Returns:
            pandas.DataFrame: 처리된 데이터프레임
        """
        cols = [
            "Time [s]", "Cell current [A]", "Terminal voltage [V]",
            "X-averaged cell temperature [K]", "Battery open-circuit voltage [V]",
            "Pack terminal voltage [V]"
        ]
        df = pd.read_csv(self.log_file, names=cols)
        for col in ["Cell current [A]", "Terminal voltage [V]", "X-averaged cell temperature [K]"]:
            series = pd.to_numeric(df[col].str.replace(r'[\[\]]', '', regex=True), errors="coerce")
            
            # 노이즈 추가 -> Gaussian 필터 -> 양자화
            noisy = self.add_noise(series, col)
            quantized = self.quantize_data(noisy, col)
            df[f"Noisy {col}"] = noisy
            df[f"Quantized {col}"] = quantized
        df.to_csv(self.output_file, index=False)
        return df

    def run(self):
        self.process_adc_data()
        return self.output_file