#!/usr/bin/env python3
"""Main CLI entry point for webcomic2pdf."""

import shutil
from pathlib import Path
from datetime import datetime

from src.scraper import scrape_images
from src.downloader import download_images
from src.pdf_generator import create_pdf
from src.utils import sanitize_filename


def main():
    """Main entry point."""
    urls_file = Path("urls.txt")
    
    if not urls_file.exists():
        print(f"Error: {urls_file} not found")
        print("Create a urls.txt file with format: URL | PDF Name")
        return 1
    
    # Parse URLs file
    entries = []
    with open(urls_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "|" in line:
                url, name = line.split("|", 1)
                entries.append((url.strip(), name.strip()))
            else:
                entries.append((line, "comic"))
    
    if not entries:
        print("No URLs found in urls.txt")
        return 1
    
    print(f"Processing {len(entries)} URL(s)...\n")
    
    # Process each URL
    for url, name in entries:
        print(f"\nProcessing: {url} → {name}.pdf")
        
        # Create temp directory
        temp_dir = Path(f"tmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Scrape, download, create PDF
            image_urls = scrape_images(url)
            if not image_urls:
                print("  No images found, skipping")
                continue
            
            image_files = download_images(image_urls, temp_dir)
            if not image_files:
                print("  Failed to download images, skipping")
                continue
            
            output_name = sanitize_filename(name)
            create_pdf(image_files, Path(f"{output_name}.pdf"))
            print(f"  ✓ Success!\n")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    print("\nDone!")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
