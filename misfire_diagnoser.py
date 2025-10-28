import time

import obd


MISFIRE_CODES = {
    "P0300": "Random/Multiple Misfire",
    "P0301": "Cylinder 1 Misfire",
    "P0302": "Cylinder 2 Misfire",
    "P0303": "Cylinder 3 Misfire",
    "P0304": "Cylinder 4 Misfire",
}


def connect_obd():
    print("🔌 Підключення до OBD...")
    connection = obd.OBD()  # автоматичний пошук порту
    if not connection.is_connected():
        print("❌ Не вдалося підключитися до OBD.")
        return None
    print("✅ Підключення встановлено.")
    return connection


def read_dtc(connection):
    print("📖 Зчитування кодів помилок...")
    dtc_response = connection.query(obd.commands.GET_DTC)
    if not dtc_response.is_null():
        return [code for code, _ in dtc_response.value]
    return []


def read_rpm_fluctuation(connection, duration=5):
    print("📈 Зчитування флуктуацій RPM ({} сек)...".format(duration))
    rpms = []
    start = time.time()
    while time.time() - start < duration:
        rpm = connection.query(obd.commands.RPM)
        if not rpm.is_null():
            rpms.append(rpm.value.magnitude)
        time.sleep(0.5)
    if not rpms:
        return 0
    avg = sum(rpms) / len(rpms)
    variance = sum((r - avg) ** 2 for r in rpms) / len(rpms)
    return variance ** 0.5  # стандартне відхилення RPM


def diagnose_misfire(codes, rpm_fluctuation):
    if not codes:
        print("✅ Помилок не виявлено.")
        return

    for code in codes:
        desc = MISFIRE_CODES.get(code, "Unknown DTC")
        print(f"🚨 Виявлено {code}: {desc}")

        if code.startswith("P030") and code != "P0300":
            cyl = code[-1]
            print(f"🧩 Пропуски у циліндрі {cyl}.")

            if rpm_fluctuation > 80:
                print("⚠️ RPM сильно коливаються → ймовірно котушка запалювання.")
            else:
                print("🕯️ RPM стабільні → можливо проблема у свічці або компресії.")

        elif code == "P0300":
            print("🌪️ Пропуски на кількох циліндрах → перевір паливо, MAF або вакуум.")


def main():
    connection = connect_obd()
    if not connection:
        return

    codes = read_dtc(connection)
    rpm_fluct = read_rpm_fluctuation(connection)
    diagnose_misfire(codes, rpm_fluct)

if __name__ == "__main__":
    main()
