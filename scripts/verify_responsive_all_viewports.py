import os
import sys
import json
import time

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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

PUBLIC_ROUTES = [
    "/login",
    "/login/college",
    "/login/central",
    "/register",
    "/verification/receipt/rcpt_532763c1caad4cf8bd1ea9bdf7a4b50d",
]

AUTH_ROUTES = [
    "/dashboard",
    "/admissions",
    "/approvals",
    "/audit",
    "/conflicts",
    "/anomalies",
    "/institutions",
    "/reference-data",
    "/reports",
    "/uploads",
    "/verification",
    "/settings",
]

BASE_URL = "http://localhost:3000"
OUT_DIR = "artifacts/responsive_after"
os.makedirs(OUT_DIR, exist_ok=True)

opts = EdgeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")

driver = webdriver.Edge(options=opts)

results = []
failures = []

def measure_overflow():
    return driver.execute_script("""
        const winWidth = window.innerWidth;
        const docWidth = document.documentElement.offsetWidth;
        const docScrollWidth = document.documentElement.scrollWidth;
        const bodyScrollWidth = document.body ? document.body.scrollWidth : 0;
        
        const overflowingElements = [];
        const all = document.querySelectorAll('*');
        all.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.right > winWidth + 1.5) {
                overflowingElements.push({
                    tag: el.tagName,
                    id: el.id,
                    className: (el.className || '').toString().slice(0, 60),
                    rectRight: Math.round(rect.right),
                    overflowPx: Math.round(rect.right - winWidth)
                });
            }
        });
        
        return {
            winWidth: winWidth,
            docWidth: docWidth,
            docScrollWidth: docScrollWidth,
            bodyScrollWidth: bodyScrollWidth,
            hasHorizontalOverflow: docScrollWidth > winWidth + 2 || bodyScrollWidth > winWidth + 2,
            overflowCount: overflowingElements.length,
            overflowingElements: overflowingElements.slice(0, 5)
        };
    """)

try:
    print("=================================================================")
    print("       STARTING PRAMAAN-AICTE RESPONSIVENESS SUITE (7 VIEWPORTS)  ")
    print("=================================================================")

    # 1. TEST PUBLIC ROUTES
    print("\n--- 1. TESTING PUBLIC ROUTES ---")
    for route in PUBLIC_ROUTES:
        url = f"{BASE_URL}{route}"
        print(f"\n[Route] {route}")
        for vp in VIEWPORTS:
            driver.set_window_size(vp["width"], vp["height"])
            driver.get(url)
            time.sleep(1.0)
            
            m = measure_overflow()
            status = "PASS" if not m["hasHorizontalOverflow"] else "FAIL"
            
            # Save screenshot for 320, 390, 768, 1366
            if vp["width"] in (320, 390, 768, 1366):
                safe_name = route.strip("/").replace("/", "_") or "root"
                ss_file = os.path.join(OUT_DIR, f"{safe_name}_{vp['width']}.png")
                driver.save_screenshot(ss_file)

            res_item = {
                "route": route,
                "viewport": vp["name"],
                "width": vp["width"],
                "height": vp["height"],
                "status": status,
                "winWidth": m["winWidth"],
                "scrollWidth": m["docScrollWidth"],
                "overflowCount": m["overflowCount"],
                "overflows": m["overflowingElements"]
            }
            results.append(res_item)
            if status == "FAIL":
                failures.append(res_item)
                print(f"  ❌ {vp['name']} ({vp['width']}x{vp['height']}): OVERFLOW by {m['docScrollWidth'] - m['winWidth']}px! Elements: {m['overflowingElements']}")
            else:
                print(f"  ✓ {vp['name']} ({vp['width']}x{vp['height']}): OK (scroll: {m['docScrollWidth']}px, win: {m['winWidth']}px)")

    # 2. LOG IN VIA CENTRAL ADMIN FOR AUTHENTICATED PORTAL ROUTES
    print("\n--- 2. LOGGING IN FOR AUTHENTICATED PORTAL ROUTES ---")
    driver.set_window_size(1366, 768)
    driver.get(f"{BASE_URL}/login")
    time.sleep(1.0)
    
    driver.execute_script("""
        localStorage.setItem('pramaan_token', 'mock_jwt_token_for_verification');
        localStorage.setItem('pramaan_user', JSON.stringify({
            email: 'aicte.admin@pramaan.gov.in',
            role: 'AICTE_ADMIN',
            fullName: 'Dr. Sunita Deshmukh',
            institutionId: null,
            institutionName: 'AICTE Central HQ'
        }));
    """)
    driver.get(f"{BASE_URL}/dashboard")
    time.sleep(1.5)
    print(f"  [OK] Authenticated session active at: {driver.current_url}")

    print("\n--- 3. TESTING AUTHENTICATED PORTAL ROUTES ---")
    for route in AUTH_ROUTES:
        url = f"{BASE_URL}{route}"
        print(f"\n[Portal Route] {route}")
        for vp in VIEWPORTS:
            driver.set_window_size(vp["width"], vp["height"])
            driver.get(url)
            time.sleep(1.2)
            
            m = measure_overflow()
            status = "PASS" if not m["hasHorizontalOverflow"] else "FAIL"
            
            # Save screenshot for 320, 390, 768, 1366
            if vp["width"] in (320, 390, 768, 1366):
                safe_name = route.strip("/").replace("/", "_")
                ss_file = os.path.join(OUT_DIR, f"{safe_name}_{vp['width']}.png")
                driver.save_screenshot(ss_file)

            res_item = {
                "route": route,
                "viewport": vp["name"],
                "width": vp["width"],
                "height": vp["height"],
                "status": status,
                "winWidth": m["winWidth"],
                "scrollWidth": m["docScrollWidth"],
                "overflowCount": m["overflowCount"],
                "overflows": m["overflowingElements"]
            }
            results.append(res_item)
            if status == "FAIL":
                failures.append(res_item)
                print(f"  ❌ {vp['name']} ({vp['width']}x{vp['height']}): OVERFLOW by {m['docScrollWidth'] - m['winWidth']}px! Elements: {m['overflowingElements']}")
            else:
                print(f"  ✓ {vp['name']} ({vp['width']}x{vp['height']}): OK (scroll: {m['docScrollWidth']}px, win: {m['winWidth']}px)")

    # 4. TEST MOBILE HAMBURGER & DRAWER INTERACTION ON 375px
    print("\n--- 4. TESTING MOBILE HAMBURGER & DRAWER INTERACTION ---")
    driver.set_window_size(375, 667)
    driver.get(f"{BASE_URL}/dashboard")
    time.sleep(1.5)
    
    hamburger = driver.find_element(By.ID, "mobile-nav-toggle-btn")
    print(f"  [OK] Mobile hamburger button found: displayed={hamburger.is_displayed()}, size={hamburger.size}")
    
    # Click hamburger
    hamburger.click()
    time.sleep(0.5)
    
    # Check if mobile drawer is visible
    drawer = driver.find_element(By.ID, "mobile-sidebar-drawer")
    print(f"  ✓ Mobile sidebar drawer after click: displayed={drawer.is_displayed()}")
    driver.save_screenshot(os.path.join(OUT_DIR, "mobile_drawer_open_375.png"))
    
    # Check close button
    close_btn = driver.find_element(By.ID, "mobile-sidebar-close-btn")
    print(f"  ✓ Mobile sidebar close button: displayed={close_btn.is_displayed()}")
    close_btn.click()
    time.sleep(0.5)
    
    drawer_elements = driver.find_elements(By.ID, "mobile-sidebar-drawer")
    drawer_hidden = len(drawer_elements) == 0
    print(f"  ✓ Mobile sidebar drawer after close click: is_closed={drawer_hidden}")

    # Output Summary
    print("\n=================================================================")
    print(f"  TEST SUMMARY: Total Checks: {len(results)} | Failures: {len(failures)}")
    print("=================================================================")
    
    report_json_path = os.path.join(OUT_DIR, "responsive_verification_results.json")
    with open(report_json_path, "w") as f:
        json.dump({
            "total_checks": len(results),
            "failures_count": len(failures),
            "viewports_tested": [vp["name"] for vp in VIEWPORTS],
            "failures": failures,
            "results": results
        }, f, indent=2)
    print(f"Results saved to {report_json_path}")

finally:
    driver.quit()
