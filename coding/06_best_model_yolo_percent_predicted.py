import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
import os
import yaml


DATASET_PATH = Path(r"C:\Users\nertila.hoxha\Downloads\tila_challenge 2.v1-test.yolov8")
NEW_IMAGES_DIR = Path(r"C:\Users\nertila.hoxha\Downloads\new_images")  # immagini da predire
MODEL_PATH = Path(r"runs/train/weights/best.pt")  # modello addestrato precedentemente
OUTPUT_CSV = NEW_IMAGES_DIR / "new_images_summary.csv"


with open(DATASET_PATH / "data.yaml", "r") as f:
    data_yaml = yaml.safe_load(f)
class_names = data_yaml["names"]
print(f"Classi: {class_names}")

model = YOLO(str(MODEL_PATH))

rows = []
for img_path in NEW_IMAGES_DIR.glob("*"):
    if not img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        continue

    results = model.predict(str(img_path), save=False, imgsz=640)

    # Recupera maschere
    masks = results[0].masks  # maschere come oggetti Mask
    if masks is None:
        continue

    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]
    img_area = h * w
    class_areas = {name: 0 for name in class_names}

    for i, mask in enumerate(masks.xy):  # xy contiene poligoni
        class_id = int(results[0].boxes.cls[i])  # id classe predetta
        polygon = np.array(mask).reshape(-1,2)

        # crea maschera binaria
        mask_img = np.zeros((h,w), dtype=np.float32)
        int_polygon = np.round(polygon).astype(np.int32)
        int_polygon[:,0] = np.clip(int_polygon[:,0],0,w-1)
        int_polygon[:,1] = np.clip(int_polygon[:,1],0,h-1)
        if int_polygon.shape[0] >= 3:
            cv2.fillPoly(mask_img, [int_polygon], 1.0)

        class_areas[class_names[class_id]] += mask_img.sum()

    # riga in CSV 
    image_id = img_path.stem.split("_")[0]
    row = {"image": image_id, "split": predicted}
    total_percent = 0.0

    for cname in class_names:
        percent = (class_areas[cname] / img_area) * 100
        total_percent += percent
        row[cname] = f"{percent:.2f}%"

    unknown = max(0.0, 100.0 - total_percent)  # evita -0.00% per velocita di calcolo
    row["unknown"] = f"{unknown:.2f}%"
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False)
print(f"CSV creato: {OUTPUT_CSV}")
