import numpy as np

class MyBMS:
    def __init__(self, initial_soc, np_value, capacity, BMS_configuration):
        """
        MyBMS 클래스 초기화 
        Args:
            initial_soc (float): 초기 SOC (State of Charge)
            np_value (int): 병렬 연결된 셀의 수
            capacity (float): 배터리의 정격 용량 (Ah)
            BMS_configuration (dict): BMS 설정값 (효율, 저항 테이블, SOC-OCV 테이블 등)
        """
        self.initial_soc = initial_soc
        self.Np = np_value
        self.capacity = capacity
        self.BMS_configuration = BMS_configuration

    def estimate_soc(self, decoded_current, decoded_voltage, decoded_temp, time_stamps, mode):
        """
        SOC 추정 목적
        Args:
            decoded_current (list): 디코딩된 전류 데이터 (A)
            decoded_voltage (list): 디코딩된 전압 데이터 (V)
            decoded_temp (list): 디코딩된 온도 데이터 (K)
            time_stamps (list): 타임스탬프 데이터 (s)
            mode (str): SOC 추정 모드 ("current-only", "voltage-only", "current-voltage")
        Returns:
            list: 추정된 SOC 값의 리스트
        """
        delta_t = 1 / 3600
        soc = [self.initial_soc]

        i_low = 0.1
        i_ocv = 0.05
        t_relx_minutes = 120
        t_ocv_minutes = 30
        relax_active = False
        ocv_active = False

        for i in range(1, len(time_stamps)):
            current = decoded_current[i]
            voltage = decoded_voltage[i]
            temp = decoded_temp[i]
            time_now = time_stamps[i]

            # CC
            if current > 0: # Charging
                eta = self.BMS_configuration["charging_eta"]
                soc_t_current = soc[-1] - (current * delta_t) * eta / (self.Np * self.capacity)
            else: # Discharging
                eta = self.BMS_configuration["discharging_eta"]
                soc_t_current = soc[-1] - (current * delta_t) / (self.Np * self.capacity * eta)

            # OCV 기반
            resistance = self.get_resistance(soc[-1])
            ocv = voltage + current * resistance
            soc_t_ocv = self.get_soc_from_ocv(ocv)

            alpha = self.BMS_configuration["alpha"]

            if mode == "current-only":
                soc_t = soc_t_current
            elif mode == "voltage-only":
                soc_t = soc_t_ocv
            else:  # current-voltage
                if abs(current) < i_ocv:
                    if not relax_active:
                        relax_active = True
                        relax_start_time = time_now
                    if not ocv_active:
                        ocv_active = True
                        ocv_start_time = time_now
                    relax_duration = time_now - relax_start_time
                    ocv_duration = time_now - ocv_start_time
                    if ocv_duration >= t_ocv_minutes * 60:
                        soc_t = alpha * soc_t_current + (1 - alpha) * soc_t_ocv
                    if relax_duration >= t_relx_minutes * 60:
                        soc_t = soc_t_ocv
                    else:
                        soc_t = soc_t_current
                elif abs(current) < i_low:
                    relax_active = False
                    if not ocv_active:
                        ocv_active = True
                        ocv_start_time = time_now
                    ocv_duration = time_now - ocv_start_time
                    if ocv_duration >= t_ocv_minutes * 60:
                        soc_t = alpha * soc_t_current + (1 - alpha) * soc_t_ocv
                    else:
                        soc_t = soc_t_current
                else:
                    relax_active = False
                    ocv_active = False
                    soc_t = soc_t_current

            soc.append(soc_t)
        return soc

    def get_resistance(self, soc):
        """
        SOC에 따른 배터리 내부 저항 값 계산
        Args:
            soc (float): SOC 값
        Returns:
            float: SOC에 따른 내부 저항 값
        """
        soc_table = self.BMS_configuration["r_table"][:, 0]
        r_table = self.BMS_configuration["r_table"][:, 1]

        if soc <= soc_table[-1]:
            return float(r_table[-1])
        if soc >= soc_table[0]:
            return float(r_table[0])

        for i in range(1, len(soc_table)):
            if soc_table[i] <= soc <= soc_table[i - 1]:
                x1, x2 = soc_table[i - 1], soc_table[i]
                y1, y2 = r_table[i - 1], r_table[i]
                return float(y1 + (soc - x1) * (y2 - y1) / (x2 - x1))
        return float(r_table[-1])

    def get_soc_from_ocv(self, ocv):
        """
        OCV를 기반으로 SOC 값 계산
        Args:
            ocv (float): OCV 값
        Returns:
            float: OCV에 따른 SOC 값
        """
        soc_table = self.BMS_configuration["soc_ocv_table"][:, 0]
        ocv_table = self.BMS_configuration["soc_ocv_table"][:, 1]

        if ocv <= ocv_table[-1]:
            return float(soc_table[-1])
        if ocv >= ocv_table[0]:
            return float(soc_table[0])

        for i in range(1, len(ocv_table)):
            if ocv_table[i] <= ocv <= ocv_table[i - 1]:
                x1, x2 = ocv_table[i - 1], ocv_table[i]
                y1, y2 = soc_table[i - 1], soc_table[i]
                return float(y1 + (ocv - x1) * (y2 - y1) / (x2 - x1))
        return float(soc_table[-1])