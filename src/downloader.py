"""Image downloading functionality."""

from pathlib import Path

import requests


def download_images(image_urls: list[str], output_dir: Path) -> list[Path]:
    """Download images to a directory.
    
    Args:
        image_urls: List of image URLs to download
        output_dir: Directory to save downloaded images
        
    Returns:
        List of paths to downloaded image files, sorted by filename
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    for i, url in enumerate(image_urls):
        filename = f"{str(i + 1).zfill(3)}.jpg"
        filepath = output_dir / filename
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            filepath.write_bytes(response.content)
            downloaded_files.append(filepath)
            print(f"  Downloaded {i+1}/{len(image_urls)}: {filename}")
        except Exception as e:
            print(f"  Error downloading {url}: {e}")
    
    return sorted(downloaded_files)
