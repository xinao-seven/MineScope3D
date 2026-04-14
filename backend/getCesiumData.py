from pathlib import Path
import sys
import zipfile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://pdmap.pland.gov.hk/PLANDWEB/public/3d_photo_realistic_models/cesium/"
OUTPUT_DIR = Path(__file__).resolve().parent / "static" / "3dtiles"


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{size}B"


def print_progress(prefix: str, done: int, total: int, width: int = 32) -> None:
    if total <= 0:
        sys.stdout.write(f"\r{prefix}: {format_bytes(done)}")
        sys.stdout.flush()
        return

    ratio = min(max(done / total, 0.0), 1.0)
    filled = int(width * ratio)
    bar = "=" * filled + "-" * (width - filled)
    sys.stdout.write(
        f"\r{prefix} [{bar}] {ratio * 100:6.2f}% ({format_bytes(done)}/{format_bytes(total)})"
    )
    sys.stdout.flush()


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download_zip_with_progress(session: requests.Session, url: str, target_zip: Path) -> bool:
    tmp_zip = target_zip.with_suffix(target_zip.suffix + ".part")

    with session.get(url, stream=True, timeout=(10, 60)) as response:
        if response.status_code == 404:
            print(f"[SKIP] 远端不存在: {url}")
            return False

        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", "0"))
        downloaded = 0

        with tmp_zip.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                print_progress(f"下载 {target_zip.name}", downloaded, total_size)

    sys.stdout.write("\n")
    tmp_zip.replace(target_zip)
    return True


def extract_zip_with_progress(source_zip: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_zip, "r") as zf:
        infos = zf.infolist()
        total_unzip_size = sum(item.file_size for item in infos)
        extracted = 0

        for item in infos:
            zf.extract(item, target_dir)
            extracted += item.file_size
            print_progress(f"解压 {source_zip.name}", extracted, total_unzip_size)

    sys.stdout.write("\n")


def download_cesium_data(base_url: str = BASE_URL) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = build_session()

    tile_pairs = [(i, j) for i in range(20, 30) for j in range(20, 30)]
    total_tiles = len(tile_pairs)

    for idx, (i, j) in enumerate(tile_pairs, start=1):
        
        tile_name = f"tile_{i}_{j}_CESIUM"
        full_url = f"{base_url}{tile_name}.zip"
        zip_path = OUTPUT_DIR / f"{tile_name}.zip"
        extract_dir = OUTPUT_DIR / tile_name

        print(f"\n[{idx}/{total_tiles}] 处理 {tile_name}")

        if extract_dir.exists() and any(extract_dir.iterdir()):
            print(f"[SKIP] 已解压完成: {extract_dir}")
            continue

        try:
            ok = download_zip_with_progress(session, full_url, zip_path)
            if not ok:
                continue
            extract_zip_with_progress(zip_path, extract_dir)
        except requests.RequestException as e:
            print(f"[ERROR] 下载失败 {tile_name}: {e}")
        except zipfile.BadZipFile:
            print(f"[ERROR] 压缩包损坏: {zip_path}")


if __name__ == "__main__":
    download_cesium_data()