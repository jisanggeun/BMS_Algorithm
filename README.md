# BMS_Algorithm
BMS Simulator &amp; Simple BMS Algorithm Repository

## 🔋 BMS Algorithm
<img width="1742" height="1870" alt="BMS_Algorithm" src="https://github.com/user-attachments/assets/247201dd-8603-4ba4-a187-f3ae7334c5f6" />

### 📘 Overview
The BMS estimates **State of Charge (SOC)** based on decoded **current**, **voltage**, and **temperature** data.

---

### ⚙️ 1. Mode Decision
- Compare current with thresholds:
  - `dsg_current_threshold`
  - `chg_current_threshold`
- Determine one of three modes:
  - **Relaxation**
  - **Charging**
  - **Discharging**

---

### 💤 2. Relaxation Mode
- Check stability conditions:
  - `dv/dt < relax_dvdt_threshold`
  - `time_in_relaxation > relax_time_threshold`
- If stable:
  - Perform **IR correction** using temperature-compensated resistance  
  - Estimate **SOC** from the corrected OCV
- If unstable:
  - Use **Coulomb Counting (CC)** method to update SOC

---

### ⚡ 3. Discharge Mode
- Use **Coulomb Counting** method to calculate and update SOC directly.

---

### 🔌 4. Charge Mode
- Compute charge amount via **Coulomb Counting**
- When charged up to `design_capacity`:
  - Linearly degrade total capacity
- Update SOC accordingly.

## 📦 Structure
<img width="920" height="391" alt="BMS_Structure" src="https://github.com/user-attachments/assets/76bb3af1-48e2-497f-9056-7d1a6ce2e001" />
<img width="971" height="682" alt="BMS_Structure_2" src="https://github.com/user-attachments/assets/ca8734f0-1ef0-44e5-9586-d77fef84a8b7" />

- `adc/`: ADC quantization module
- `bms/` : BMS logic (SOC estimation, degradation tracking)
- `utils/` : Helper and data processing functions
- `configs/` : Parameter and lookup tables
- `main.py` : Entry point for running the full simulation

## Results


# Todo-list

## 🚀 Run
```bash
python main.py
