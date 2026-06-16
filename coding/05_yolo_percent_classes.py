import cv2
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from ultralytics import YOLO
import os
import shutil

DATASET_PATH = Path(r"output\cpted_master.v1i.yolov8")
SPLITS = ["train", "valid"]
OUTPUT_CSV = DATASET_PATH / "dataset_summary.csv"

with open(DATASET_PATH / "data.yaml", "r") as f:
    data_yaml = yaml.safe_load(f)
class_names = data_yaml["names"]
print(f"{class_names}")


"""
data_yaml_path = DATASET_PATH / "data.yaml"
#device = 0  # oppure "cpu"

model = YOLO("yolov8s-seg.pt")  # modello pre-addestrato

model.train(
    data=str(data_yaml_path),
    epochs=100,
    patience=20000,
    save_period=20,
    imgsz=640,
    batch=4,
    optimizer="auto",
    plots=True,
    #device=device,
    workers=0  # IMPORTANTISSIMO su Windows
)
best_src = Path("runs/segment/yolo8/weights/best.pt")
best_dst = Path(r"coding\YOLO8\CV_best_model\best_yolo11.pt")

best_dst.parent.mkdir(parents=True, exist_ok=True)  # crea cartella se manca
shutil.copy(best_src, best_dst)

print("Modello salvato in:", best_dst)
"""

rows = []

for split in SPLITS:
    images_dir = DATASET_PATH / split / "images"
    labels_dir = DATASET_PATH / split / "labels"
    print(f"\nSplit: {split}")
    print(f"Cartella immagini: {images_dir}")
    print(f"Cartella labels: {labels_dir}")

    for img_path in images_dir.glob("**/*"):
        if img_path.is_file() and img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            label_path = labels_dir / f"{img_path.stem}.txt"
            if label_path.exists():
                print(f"Trovata immagine e label: {img_path.name}")
            else:
                print(f"Manca label per: {img_path.name}")
                continue

            img = cv2.imread(str(img_path))
            if img is None:
                continue
            h, w = img.shape[:2]
            img_area = h * w
            class_areas = {name: 0 for name in class_names}

            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 3:
                        continue
                    class_id = int(parts[0])
                    coords = np.array(list(map(float, parts[1:])))
                    coords[0::2] *= w  # x
                    coords[1::2] *= h  # y
                    polygon = coords.reshape(-1, 2)

                    mask = np.zeros((h, w), dtype=np.float32)
                    int_polygon = np.round(polygon).astype(np.int32)
                    int_polygon[:, 0] = np.clip(int_polygon[:, 0], 0, w - 1)
                    int_polygon[:, 1] = np.clip(int_polygon[:, 1], 0, h - 1)

                    if int_polygon.shape[0] >= 3:
                        cv2.fillPoly(mask, [int_polygon], 1.0)
                    class_areas[class_names[class_id]] += mask.sum()

            image_id = img_path.stem.split("_")[0]
            row = {"image": image_id, "split": split}
            """
            for cname in class_names:
                row[cname] = f"{(class_areas[cname] / img_area) * 100:.2f}%"
            rows.append(row)
            """
            image_id = img_path.stem.split("_")[0]
            row = {"image": image_id, "split": split}

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
