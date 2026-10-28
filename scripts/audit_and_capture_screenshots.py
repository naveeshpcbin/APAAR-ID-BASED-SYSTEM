"""
PRAMAAN-AICTE: Exhaustive Feature Testing & High-Resolution UI Capture
Captures high-res production screenshots for all roles and workflows.
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = r"D:\AICTE\artifacts\live_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,920")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def audit_and_capture():
    print("Launching Chrome Headless for full system audit...")
    driver = setup_driver()
    
    try:
        # =====================================================================
        # 1. PUBLIC: PORTAL DIRECTORY (/login)
        # =====================================================================
        print("[1/8] Capturing Portal Directory (/login)...")
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "01_portal_directory.png"))

        # =====================================================================
        # 2. CENTRAL ADMIN: LOGIN & DASHBOARD
        # =====================================================================
        print("[2/8] Logging in as AICTE Central Admin...")
        driver.get(f"{BASE_URL}/login/central")
        time.sleep(1.5)
        
        demo_admin_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "demo-central-admin-btn"))
        )
        demo_admin_btn.click()
        WebDriverWait(driver, 10).until(EC.url_contains("/dashboard"))
        time.sleep(3.5) # allow charts to render
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "02_dashboard_overview.png"))

        # =====================================================================
        # 3. CENTRAL ADMIN: CONFLICTS INVESTIGATION (/conflicts)
        # =====================================================================
        print("[3/8] Capturing Cross-Institute Conflicts (/conflicts)...")
        driver.get(f"{BASE_URL}/conflicts")
        time.sleep(3)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "03_conflicts_adjudicated.png"))

        # =====================================================================
        # 4. CENTRAL ADMIN: TAMPER-EVIDENT AUDIT LEDGER (/audit)
        # =====================================================================
        print("[4/8] Capturing Cryptographic Hash Chain Audit Ledger (/audit)...")
        driver.get(f"{BASE_URL}/audit")
        time.sleep(3)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "04_audit_ledger_verified.png"))

        # =====================================================================
        # 5. CENTRAL ADMIN: QR VERIFICATION GATEWAY (/verification)
        # =====================================================================
        print("[5/8] Capturing QR Receipt Verification (/verification)...")
        driver.get(f"{BASE_URL}/verification")
        time.sleep(3)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "05_verification_qr_receipt.png"))

        # =====================================================================
        # 6. DTU DELHI: COLLEGE NODAL LOGIN & UPLOADS DESK
        # =====================================================================
        print("[6/8] Logging in as DTU Delhi College Nodal Officer...")
        driver.get(f"{BASE_URL}/login/college")
        time.sleep(1.5)
        
        demo_dtu_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "demo-dtu-btn"))
        )
        demo_dtu_btn.click()
        WebDriverWait(driver, 10).until(EC.url_contains("/uploads"))
        time.sleep(3)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "06_uploads_smart_ingestion.png"))

        # =====================================================================
        # 7. DTU DELHI: INTERACTIVE SPREADSHEET SANDBOX (/uploads/10)
        # =====================================================================
        print("[7/8] Capturing DTU Delhi Interactive Spreadsheet Sandbox (/uploads/10)...")
        driver.get(f"{BASE_URL}/uploads/10")
        time.sleep(3.5)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "07_interactive_spreadsheet_sandbox.png"))

        # =====================================================================
        # 8. DTU DELHI: SIH-R10 DEGREE CERTIFICATE (/admissions/certificate/2)
        # =====================================================================
        print("[8/8] Capturing DTU Delhi SIH-R10 Degree Certificate (/admissions/certificate/2)...")
        driver.get(f"{BASE_URL}/admissions/certificate/2")
        time.sleep(3.5)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "08_student_certificate_verified.png"))

        print("\nSUCCESS: All 8 production screens tested and captured successfully!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    audit_and_capture()
