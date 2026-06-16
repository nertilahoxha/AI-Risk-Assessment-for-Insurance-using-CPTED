# crop_zoom_center.py
# Input:  cartella con immagini satellitari
# Output: cartella con immagini "zoomate" (crop centrale + resize a dimensioni originali)

from pathlib import Path
from PIL import Image

# ----------------------------
# PARAMETRI (MODIFICA QUI)
# ----------------------------
INPUT_DIR  = Path(r"output_satellite_maps_500x500")     # <-- input
OUTPUT_DIR = Path(r"output_satellite_maps_zoom")        # <-- output

BORDER_CROP_PX = 350

EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
JPEG_QUALITY = 95

# NEW: file txt con lista codici da ESCLUDERE (uno per riga)
EXCLUDE_TXT = Path(r"output\codice_cliente_missing.txt")


# NEW: carica codici da escludere in un set (velocissimo nei lookup)
def load_exclude_codes(txt_path: Path) -> set[str]:
    if not txt_path.exists():
        print(f"[ATTENZIONE] File exclude non trovato: {txt_path.resolve()} (nessuna esclusione applicata)")
        return set()

    codes: set[str] = set()
    with txt_path.open("r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if not code:
                continue
            # se per caso nel txt ci sono separatori/virgole, prendiamo comunque il "primo token"
            code = code.split()[0].strip().strip(",;")
            if code:
                codes.add(code)
    return codes


def crop_center_keep_size(img: Image.Image, border_px: int) -> Image.Image:
    """Crop centrale togliendo border_px per lato e poi resize alle dimensioni originali."""
    w, h = img.size

    if border_px <= 0:
        return img.copy()

    max_border = min(w, h) // 2 - 1
    if border_px > max_border:
        raise ValueError(
            f"BORDER_CROP_PX={border_px} troppo grande per immagine {w}x{h}. "
            f"Massimo consigliato: {max_border}"
        )

    left   = border_px
    upper  = border_px
    right  = w - border_px
    lower  = h - border_px

    cropped = img.crop((left, upper, right, lower))
    resized = cropped.resize((w, h), resample=Image.Resampling.LANCZOS)
    return resized


def process_folder(input_dir: Path, output_dir: Path, border_px: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    if not files:
        print(f"Nessuna immagine trovata in: {input_dir.resolve()}")
        return

    # NEW: set di codici da escludere
    exclude_codes = load_exclude_codes(EXCLUDE_TXT)

    ok, err, skipped = 0, 0, 0
    for in_path in files:
        try:
            # NEW: codice = nome file senza estensione
            code = in_path.stem

            # NEW: se il codice è nella blacklist, non salvare
            if code in exclude_codes:
                skipped += 1
                continue

            with Image.open(in_path) as img:
                img = img.convert("RGB") if img.mode in ("P", "RGBA", "LA") else img
                out_img = crop_center_keep_size(img, border_px)

                rel = in_path.relative_to(input_dir)
                out_path = output_dir / rel
                out_path.parent.mkdir(parents=True, exist_ok=True)

                suffix = out_path.suffix.lower()
                save_kwargs = {}

                if suffix in (".jpg", ".jpeg"):
                    save_kwargs = {"quality": JPEG_QUALITY, "optimize": True}
                elif suffix == ".png":
                    save_kwargs = {"optimize": True}

                out_img.save(out_path, **save_kwargs)

            ok += 1
        except Exception as e:
            err += 1
            print(f"[ERRORE] {in_path.name}: {e}")

    print("\n=== RISULTATO ===")
    print(f"Input:  {input_dir.resolve()}")
    print(f"Output: {output_dir.resolve()}")
    print(f"Crop bordo (px per lato): {border_px}")
    print(f"Esclusi (in txt): {len(exclude_codes)}")
    print(f"Skippati (match): {skipped}")
    print(f"Salvate: {ok}")
    print(f"Errori:  {err}")


if __name__ == "__main__":
    process_folder(INPUT_DIR, OUTPUT_DIR, BORDER_CROP_PX)
