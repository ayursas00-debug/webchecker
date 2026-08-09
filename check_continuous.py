"""
check_continuous.py -- continuous monitoring version with ntfy notifications

Checks https://broneering.mfa.ee/ every 1 minute for D-visa availability
at the Embassy of the Republic of Estonia in New Delhi.

Working hours: 10 AM to 5 PM (checks only during this time)

Sends ntfy notifications:
- When bot starts
- When D-visa service is found (3 notifications)
- When bot stops

Run:
    python check_continuous.py
"""

import json
import time
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

URL = "https://broneering.mfa.ee/en/"
TARGET_OFFICE_TEXT = "New Delhi"
# Check for either "D-visa" or "long stay" (case-insensitive)
TARGET_SERVICE_KEYWORDS = ["d-visa", "long stay"]
CHECK_INTERVAL = 60  # seconds (1 minute)

# Working hours configuration
START_HOUR = 10  # 10 AM
END_HOUR = 17    # 5 PM (17:00)

# Ntfy configuration
NTFY_URL = "https://ntfy.sh/webchecker"

def send_ntfy_notification(title, message, priority="default", tags=None):
    """Send notification to ntfy"""
    try:
        headers = {
            "Title": title,
            "Priority": priority,
        }
        if tags:
            headers["Tags"] = tags
        
        response = requests.post(
            NTFY_URL,
            data=message,
            headers=headers
        )
        if response.status_code == 200:
            print(f"Notification sent: {title}")
        else:
            print(f"Notification failed: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")

def is_within_working_hours():
    """Check if current time is between START_HOUR and END_HOUR"""
    current_hour = datetime.now().hour
    return START_HOUR <= current_hour < END_HOUR

def wait_until_working_hours():
    """Wait until START_HOUR if outside working hours"""
    now = datetime.now()
    current_hour = now.hour
    
    if current_hour < START_HOUR:
        # Wait until START_HOUR today
        target_time = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        wait_seconds = (target_time - now).total_seconds()
        print(f"\nOutside working hours. Waiting until {START_HOUR}:00 AM...")
        print(f"Will start in {int(wait_seconds/60)} minutes")
        time.sleep(wait_seconds)
    elif current_hour >= END_HOUR:
        # Wait until START_HOUR tomorrow
        tomorrow = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0) + timedelta(days=1)
        wait_seconds = (tomorrow - now).total_seconds()
        print(f"\nOutside working hours. Waiting until {START_HOUR}:00 AM tomorrow...")
        print(f"Will start in {int(wait_seconds/3600)} hours")
        time.sleep(wait_seconds)

def check_once():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)

        office_select = page.locator("select").first
        office_select.wait_for(state="visible", timeout=15000)
        options = office_select.locator("option").all_text_contents()

        match_index = None
        matched_text = None
        for i, text in enumerate(options):
            if TARGET_OFFICE_TEXT.lower() in text.lower():
                match_index = i
                matched_text = text.strip()
                break

        if match_index is None:
            browser.close()
            return {
                "found": False,
                "error": f"no office option matched '{TARGET_OFFICE_TEXT}'",
                "all_office_options": [o.strip() for o in options],
            }

        office_select.select_option(index=match_index)
        page.wait_for_timeout(5000)  # let the service list load after selecting the office

        service_texts = []
        found = False
        try:
            service_select = page.locator("select").nth(1)
            if service_select.count() > 0:
                service_texts = [o.strip() for o in service_select.locator("option").all_text_contents()]
                # Check if any keyword is found in any service option (case-insensitive)
                for service in service_texts:
                    service_lower = service.lower()
                    if any(keyword in service_lower for keyword in TARGET_SERVICE_KEYWORDS):
                        found = True
                        break
        except Exception:
            pass

        if not found:
            body_text = page.inner_text("body").lower()
            found = any(keyword in body_text for keyword in TARGET_SERVICE_KEYWORDS)

        browser.close()

        return {
            "found": found,
            "matched_office": matched_text,
            "service_options_seen": service_texts,
        }

if __name__ == "__main__":
    print(f"Visa Checker - Working Hours: {START_HOUR}:00 AM to {END_HOUR}:00 PM")
    print(f"Target: {TARGET_OFFICE_TEXT}")
    print(f"Check interval: {CHECK_INTERVAL} seconds (1 minute)")
    print(f"Press Ctrl+C to stop\n")
    print("=" * 80)
    
    check_count = 0
    found_notified = False  # Track if we've already sent found notifications
    daily_start_notified = False  # Track if we've sent today's start notification
    
    try:
        while True:
            # Wait if outside working hours
            wait_until_working_hours()
            
            # Send start notification once per day
            if not daily_start_notified:
                send_ntfy_notification(
                    "Visa Checker Started",
                    f"Monitoring {TARGET_OFFICE_TEXT} for D-visa availability. Working hours: {START_HOUR}:00 AM - {END_HOUR}:00 PM. Checking every {CHECK_INTERVAL//60} minute(s).",
                    priority="default",
                    tags="robot,white_check_mark"
                )
                daily_start_notified = True
            
            try:
                # Check if still within working hours
                if not is_within_working_hours():
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{current_time}] Outside working hours ({END_HOUR}:00 PM reached)")
                    
                    # Send end-of-day notification
                    send_ntfy_notification(
                        "Visa Checker - Day Ended",
                        f"Monitoring stopped for today. Completed {check_count} checks. Will resume tomorrow at {START_HOUR}:00 AM.",
                        priority="default",
                        tags="calendar,zzz"
                    )
                    
                    # Reset for next day
                    check_count = 0
                    found_notified = False
                    daily_start_notified = False
                    
                    # Wait until next working day
                    continue
                
                check_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n[Check #{check_count}] {timestamp}")
                print("-" * 80)
                
                result = check_once()
                
                # Print formatted result
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Alert if found and not yet notified
                if result.get("found") and not found_notified:
                    print("\n" + "!" * 80)
                    print("ALERT: D-VISA SERVICE IS AVAILABLE!")
                    print("!" * 80)
                    
                    # Send 3 notifications
                    for i in range(1, 4):
                        send_ntfy_notification(
                            f"D-VISA AVAILABLE! (Alert {i}/3)",
                            f"D-visa service is now available at {result.get('matched_office')}!\n\nServices: {', '.join(result.get('service_options_seen', []))}",
                            priority="urgent",
                            tags="tada,fire,rotating_light"
                        )
                        time.sleep(1)  # Small delay between notifications
                    
                    found_notified = True  # Mark as notified to avoid spam
                
                print(f"\nNext check in {CHECK_INTERVAL} seconds...")
                print("=" * 80)
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                raise  # Re-raise to be caught by outer try-except
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                print(f"Retrying in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print(f"Total checks performed today: {check_count}")
        
        # Send shutdown notification
        send_ntfy_notification(
            "Visa Checker Stopped",
            f"Monitoring stopped by user after {check_count} checks.",
            priority="default",
            tags="stop_sign,zzz"
        )
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        
        # Send error notification
        send_ntfy_notification(
            "Visa Checker Error",
            f"Fatal error occurred: {str(e)}",
            priority="high",
            tags="x,warning"
        )
