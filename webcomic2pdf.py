#!/usr/bin/env python3
import re
import shutil
from pathlib import Path
from datetime import datetime

import requests
import img2pdf
from playwright.sync_api import sync_playwright

def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    return re.sub(invalid_chars, '_', name).strip('. ')


def scrape_images(url: str, headless: bool = True) -> list[str]:
    """Scrape all comic images from a URL."""
    print(f"Scraping: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # Auto-scroll to load lazy images
        page.evaluate("""
            async () => {
                let lastHeight = 0;
                let stableCount = 0;
                
                while (stableCount < 8) {
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(r => setTimeout(r, 400));
                    
                    const h = document.body.scrollHeight;
                    if (h === lastHeight) stableCount++;
                    else { stableCount = 0; lastHeight = h; }
                }
            }
        """)
        
        # Extract image URLs
        images = page.evaluate("""
            () => {
                function pickFromSrcset(srcset) {
                    if (!srcset) return null;
                    const parts = srcset.split(',').map(s => s.trim());
                    const sorted = parts.map(p => {
                        const [u, w] = p.split(/\\s+/);
                        const n = parseInt((w || '').replace('w', '')) || 0;
                        return { u, n };
                    }).sort((a, b) => b.n - a.n);
                    return sorted[0]?.u || parts.pop().split(/\\s+/)[0];
                }

                const scope = document.querySelector('.reading-content') || document;
                const nodes = [...scope.querySelectorAll('.page-break, .page-break *')];
                const urls = new Set();

                nodes.filter(n => n.tagName === 'IMG').forEach(img => {
                    const candidates = [
                        img.getAttribute('src'),
                        img.getAttribute('data-src'),
                        img.getAttribute('data-lazy-src'),
                        pickFromSrcset(img.getAttribute('srcset')),
                        pickFromSrcset(img.getAttribute('data-srcset'))
                    ].filter(Boolean);
                    candidates.forEach(u => urls.add(new URL(u, location.href).href));
                });

                nodes.forEach(n => {
                    const style = getComputedStyle(n).backgroundImage || '';
                    const m = style.match(/url\\(["']?(.+?)["']?\\)/);
                    if (m) urls.add(new URL(m[1], location.href).href);
                });

                [...scope.querySelectorAll('noscript')].forEach(ns => {
                    const tmp = document.createElement('div');
                    tmp.innerHTML = ns.textContent || ns.innerHTML || '';
                    tmp.querySelectorAll('img').forEach(img => {
                        const u = img.getAttribute('src') || pickFromSrcset(img.getAttribute('srcset'));
                        if (u) urls.add(new URL(u, location.href).href);
                    });
                });

                return [...urls];
            }
        """)
        
        browser.close()
        print(f"  Found {len(images)} images")
        return images


def download_images(image_urls: list[str], output_dir: Path) -> list[Path]:
    """Download images to a directory."""
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


def create_pdf(image_paths: list[Path], output_path: Path) -> Path:
    """Create a PDF from images."""
    if not image_paths:
        raise ValueError("No images provided")
    
    if not output_path.suffix == ".pdf":
        output_path = output_path.with_suffix(".pdf")
    
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in image_paths]))
    
    print(f"  PDF created: {output_path} ({len(image_paths)} pages)")
    return output_path


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
