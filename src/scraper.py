"""Web scraping functionality for extracting comic images from webpages."""

from playwright.sync_api import sync_playwright


def scrape_images(url: str, headless: bool = True) -> list[str]:
    """Scrape all comic images from a URL.
    
    Args:
        url: The URL to scrape images from
        headless: Whether to run browser in headless mode
        
    Returns:
        List of image URLs found on the page
    """
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
