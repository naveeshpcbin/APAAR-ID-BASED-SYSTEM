import os
import json
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By

VIEWPORTS = [
    {"name": "320_small_mobile", "width": 320, "height": 568},
    {"name": "375_common_mobile", "width": 375, "height": 667},
    {"name": "390_modern_mobile", "width": 390, "height": 844},
    {"name": "430_large_mobile", "width": 430, "height": 932},
    {"name": "768_tablet_portrait", "width": 768, "height": 1024},
    {"name": "1024_tablet_landscape", "width": 1024, "height": 768},
    {"name": "1366_desktop", "width": 1366, "height": 768},
]

ROUTES = [
    "/login",
    "/login/college",
    "/login/central",
    "/register",
    "/verification"
]

BASE_URL = "https://brainforge.info"
OUT_DIR = "artifacts/responsive_before"
os.makedirs(OUT_DIR, exist_ok=True)

opts = EdgeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")

driver = webdriver.Edge(options=opts)

results = []

try:
    for route in ROUTES:
        url = f"{BASE_URL}{route}"
        print(f"\n--- Testing Route: {route} ---")
        for vp in VIEWPORTS:
            driver.set_window_size(vp["width"], vp["height"])
            driver.get(url)
            time.sleep(2)  # wait for hydration

            # Measure overflow
            metrics = driver.execute_script("""
                const docWidth = document.documentElement.offsetWidth;
                const scrollWidth = document.documentElement.scrollWidth;
                const winWidth = window.innerWidth;
                const bodyScrollWidth = document.body ? document.body.scrollWidth : 0;
                
                // Find all elements causing overflow
                const overflowingElements = [];
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.right > winWidth + 1) {
                        overflowingElements.push({
                            tag: el.tagName,
                            id: el.id,
                            className: (el.className || '').toString().slice(0, 80),
                            rectRight: Math.round(rect.right),
                            overflowPx: Math.round(rect.right - winWidth)
                        });
                    }
                });
                
                return {
                    winWidth: winWidth,
                    docWidth: docWidth,
                    scrollWidth: scrollWidth,
                    bodyScrollWidth: bodyScrollWidth,
                    hasHorizontalOverflow: scrollWidth > winWidth + 2 || bodyScrollWidth > winWidth + 2,
                    overflowingCount: overflowingElements.length,
                    topOverflows: overflowingElements.slice(0, 5)
                };
            """)

            res_entry = {
                "route": route,
                "viewport": vp["name"],
                "width": vp["width"],
                "height": vp["height"],
                "hasHorizontalOverflow": metrics["hasHorizontalOverflow"],
                "scrollWidth": metrics["scrollWidth"],
                "winWidth": metrics["winWidth"],
                "overflowingCount": metrics["overflowingCount"],
                "topOverflows": metrics["topOverflows"]
            }
            results.append(res_entry)

            status = "FAIL (OVERFLOW)" if metrics["hasHorizontalOverflow"] else "OK"
            print(f"  [{vp['width']}x{vp['height']}] {vp['name']}: {status} (scroll: {metrics['scrollWidth']}, win: {metrics['winWidth']}, overflowElements: {metrics['overflowingCount']})")

            # Save screenshot
            ss_path = os.path.join(OUT_DIR, f"{route.replace('/', '_')}_{vp['name']}.png")
            driver.save_screenshot(ss_path)

    # Save summary report JSON
    with open(os.path.join(OUT_DIR, "reproduction_summary.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\nReproduction inspection complete! Saved screenshots and summary to", OUT_DIR)

finally:
    driver.quit()

