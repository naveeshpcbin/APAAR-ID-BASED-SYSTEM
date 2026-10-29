import os
import sys
import json
import time

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

VIEWPORTS = [
    {"name": "320_small_mobile", "width": 320, "height": 568},
    {"name": "375_common_mobile", "width": 375, "height": 667},
    {"name": "390_modern_mobile", "width": 390, "height": 844},
    {"name": "430_large_mobile", "width": 430, "height": 932},
    {"name": "768_tablet_portrait", "width": 768, "height": 1024},
    {"name": "1024_tablet_landscape", "width": 1024, "height": 768},
    {"name": "1366_desktop", "width": 1366, "height": 768},
]

BASE_URL = "https://brainforge.info"
OUT_DIR = "artifacts/responsive_live_production"
os.makedirs(OUT_DIR, exist_ok=True)

opts = EdgeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-gpu")
driver = webdriver.Edge(options=opts)

routes = [
    "/login",
    "/login/college",
    "/login/central",
    "/register",
    "/verification/receipt/rcpt_532763c1caad4cf8bd1ea9bdf7a4b50d"
]
results = []

print("=== VERIFYING LIVE PRODUCTION: https://brainforge.info ===")

for route in routes:
    url = f"{BASE_URL}{route}"
    print(f"\nTesting live URL: {url}")
    for vp in VIEWPORTS:
        driver.set_window_size(vp["width"], vp["height"])
        driver.get(url)
        time.sleep(1.5)
        
        m = driver.execute_script("""
            const winWidth = window.innerWidth;
            const scrollWidth = document.documentElement.scrollWidth;
            const bodyScrollWidth = document.body ? document.body.scrollWidth : 0;
            return {
                winWidth: winWidth,
                scrollWidth: Math.max(scrollWidth, bodyScrollWidth),
                hasOverflow: scrollWidth > winWidth + 2 || bodyScrollWidth > winWidth + 2
            };
        """)
        status = "FAIL" if m["hasOverflow"] else "PASS"
        results.append({"route": route, "viewport": vp["name"], "status": status, "scroll": m["scrollWidth"], "win": m["winWidth"]})
        print(f"  [{status}] {vp['name']}: scroll={m['scrollWidth']}px, win={m['winWidth']}px")
        
        if vp["width"] in (320, 390, 768, 1366):
            safe = route.strip("/").replace("/", "_") or "root"
            driver.save_screenshot(os.path.join(OUT_DIR, f"live_{safe}_{vp['width']}.png"))

# Test Authenticated flow on live production
print("\nTesting Authenticated Drawer on Live Production (375px)...")
driver.set_window_size(375, 667)
driver.get(f"{BASE_URL}/login")
time.sleep(1)

driver.execute_script("""
    localStorage.setItem('pramaan_token', 'mock_token');
    localStorage.setItem('pramaan_user', JSON.stringify({
        email: 'aicte.admin@pramaan.gov.in',
        role: 'AICTE_ADMIN',
        fullName: 'Dr. Sunita Deshmukh'
    }));
""")
driver.get(f"{BASE_URL}/dashboard")
time.sleep(2)

m_dash = driver.execute_script("""
    const winWidth = window.innerWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    return { winWidth, scrollWidth, hasOverflow: scrollWidth > winWidth + 2 };
""")
print(f"  [Dashboard 375px]: status={'FAIL' if m_dash['hasOverflow'] else 'PASS'}, scroll={m_dash['scrollWidth']}px, win={m_dash['winWidth']}px")
driver.save_screenshot(os.path.join(OUT_DIR, "live_dashboard_375.png"))

hamburger = driver.find_element("id", "mobile-nav-toggle-btn")
print(f"  Hamburger visible: {hamburger.is_displayed()}, size={hamburger.size}")
hamburger.click()
time.sleep(0.8)

drawer = driver.find_element("id", "mobile-sidebar-drawer")
print(f"  Mobile drawer opened: {drawer.is_displayed()}")
driver.save_screenshot(os.path.join(OUT_DIR, "live_drawer_open_375.png"))

close_btn = driver.find_element("id", "mobile-sidebar-close-btn")
close_btn.click()
time.sleep(0.5)

drawers = driver.find_elements("id", "mobile-sidebar-drawer")
print(f"  Mobile drawer closed: {len(drawers) == 0}")

driver.quit()

total = len(results)
fails = [r for r in results if r["status"] == "FAIL"]
print(f"\n=======================================================")
print(f"LIVE VERIFICATION RESULT: {total} checks, {len(fails)} failures")
print(f"=======================================================")

