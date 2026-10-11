import os
import shutil

base = os.path.join("TigerTrace_AI", "data", "reference_catalogue")

mapping = {
    "Bajirao": "Maya_T1",
    "Swastik": "Chhota_Matka_T3",
    "T15_Collarwali": "Matkasur_T2",
    "T40_Patdev": "T54_Kolsa",
    "Karmajhiri_Core_Tigers": "Tadoba_Lake_Dominant",
    "T-74_L-Mark": "Telia_Sisters_Territory"
}

for old_name, new_name in mapping.items():
    old_p = os.path.join(base, old_name)
    new_p = os.path.join(base, new_name)
    if os.path.exists(old_p):
        if os.path.exists(new_p):
            shutil.rmtree(new_p)
        os.rename(old_p, new_p)
        print(f"Renamed {old_name} -> {new_name}")

print("Current directories:", os.listdir(base))
