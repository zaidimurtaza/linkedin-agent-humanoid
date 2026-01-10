"""
LinkedIn Scraper using Playwright
Function-based approach with human-like behavior to avoid bot detection
"""

from playwright.sync_api import sync_playwright, Page
import time
import os
import random
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


def random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
    """Add random delay to simulate human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def human_type(page: Page, selector: str, text: str):
    """Type text character by character with random delays like a human"""
    page.click(selector)
    random_delay(0.3, 0.8)
    
    for char in text:
        page.type(selector, char, delay=random.randint(50, 150))
    
    random_delay(0.2, 0.5)


def move_mouse_randomly(page: Page):
    """Move mouse to random positions to simulate human behavior"""
    try:
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
    except:
        pass


def login_to_linkedin(page: Page, email: str, password: str) -> bool:
    """
    Step 1: Login to LinkedIn with human-like behavior
    
    Args:
        page: Playwright page object
        email: LinkedIn account email
        password: LinkedIn account password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    print("Step 1: Logging into LinkedIn...")
    
    try:
        # Navigate to LinkedIn login page
        print("→ Navigating to LinkedIn login page...")
        try:
            response = page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
            if response:
                print(f"  → Page loaded (Status: {response.status})")
            random_delay(2, 4)
        except Exception as e:
            print(f"  ⚠ Navigation error: {str(e)}")
            print("  → Checking if page loaded anyway...")
            random_delay(2, 3)
            if 'linkedin.com' not in page.url:
                raise Exception("Failed to navigate to LinkedIn login page")
        
        # Random mouse movement
        move_mouse_randomly(page)
        random_delay(0.5, 1.5)
        
        # Fill email with human-like typing
        email_selector = 'input#username'  # REPLACE WITH ACTUAL SELECTOR
        print(f"→ Typing email...")
        human_type(page, email_selector, email)
        print(f"✓ Filled email: {email}")
        
        # Random mouse movement
        move_mouse_randomly(page)
        random_delay(0.8, 1.5)
        
        # Fill password with human-like typing
        password_selector = 'input#password'  # REPLACE WITH ACTUAL SELECTOR
        print("→ Typing password...")
        human_type(page, password_selector, password)
        print("✓ Filled password")
        
        # Random delay before clicking login
        random_delay(1, 2)
        move_mouse_randomly(page)
        
        # Click login button
        login_button_selector = 'button[type="submit"]'  # REPLACE WITH ACTUAL SELECTOR
        print("→ Clicking login button...")
        page.click(login_button_selector)
        print("✓ Clicked login button")
        
        # Wait for navigation after login (with flexible timeout handling)
        print("→ Waiting for login to complete...")
        try:
            # Try to wait for navigation, but don't fail if it times out
            page.wait_for_load_state('domcontentloaded', timeout=10000)
            random_delay(2, 3)
        except Exception as e:
            print(f"  ⚠ Timeout waiting for page load, but continuing...")
            random_delay(2, 3)
        
        # Additional wait for any async content
        random_delay(2, 4)
        
        # Check if login was successful
        current_url = page.url
        print(f"→ Current URL: {current_url}")
        
        if 'feed' in current_url or 'mynetwork' in current_url:
            print("✓ Login successful!")
            return True
        elif 'checkpoint' in current_url or 'challenge' in current_url:
            print("⚠ LinkedIn security challenge detected!")
            print("→ Please complete the CAPTCHA/verification manually...")
            input("Press Enter after completing the challenge...")
            
            # Check again after manual intervention
            random_delay(1, 2)
            if 'feed' in page.url or 'mynetwork' in page.url:
                print("✓ Login successful after challenge!")
                return True
            else:
                print("✗ Login failed after challenge")
                return False
        elif 'login' in current_url:
            print("⚠ Still on login page. Login may have failed.")
            return False
        else:
            # If we're not on login page, might be logged in - check for feed elements
            print("⚠ URL doesn't match expected patterns. Checking for feed elements...")
            try:
                # Check if feed elements are present
                feed_check = page.locator('div.scaffold-finite-scroll__content, div.feed-shared-update-v2').first
                if feed_check.count() > 0:
                    print("✓ Feed elements found - assuming login successful!")
                    return True
                else:
                    print("⚠ No feed elements found. Current URL:", current_url)
                    return False
            except:
                print("⚠ Could not verify login status. Current URL:", current_url)
                return False
            
    except Exception as e:
        print(f"⚠ Error during login: {str(e)}")
        # Even if there was an error, check if we're logged in
        try:
            current_url = page.url
            if 'feed' in current_url or 'mynetwork' in current_url:
                print("✓ However, appears to be logged in based on URL. Proceeding...")
                return True
            else:
                print("✗ Login failed and not on feed page")
                return False
        except:
            print("✗ Login failed and could not verify status")
            return False


def extract_post_data(page: Page, post_element) -> Optional[Dict]:
    """
    Extract data from a single LinkedIn post element
    
    Args:
        page: Playwright page object
        post_element: Post element handle
    
    Returns:
        dict: Post data or None if extraction fails
    """
    try:
        post_data = {}
        
        # Extract Post URN (only valid URNs, skip ember IDs)
        post_urn = post_element.get_attribute('data-urn') or ''
        # Filter out invalid URNs (ember IDs, etc.)
        if post_urn and (post_urn.startswith('urn:li:') or post_urn.startswith('urn:li:activity:')):
            post_data['post_urn'] = post_urn
        else:
            # Try to get from parent or other attributes
            try:
                parent_urn = post_element.evaluate("""el => {
                    let current = el;
                    for (let i = 0; i < 5 && current; i++) {
                        if (current.getAttribute('data-urn') && current.getAttribute('data-urn').startsWith('urn:li:activity:')) {
                            return current.getAttribute('data-urn');
                        }
                        current = current.parentElement;
                    }
                    return '';
                }""")
                post_data['post_urn'] = parent_urn or ''
            except:
                post_data['post_urn'] = ''
        
        # Extract Author Name (get first line only, clean up)
        try:
            # Try multiple selectors to find author name
            author_name_elem = post_element.locator('span.update-components-actor__title span[dir="ltr"], span.update-components-actor__title').first
            if author_name_elem.count() == 0:
                author_name_elem = post_element.locator('a.update-components-actor__meta-link span.update-components-actor__title span').first
            
            if author_name_elem.count() > 0:
                author_text = author_name_elem.inner_text().strip()
                # Get first line only, remove extra whitespace and newlines
                author_name = author_text.split('\n')[0].strip()
                # Remove any "Verified" or other suffixes
                author_name = author_name.split('•')[0].strip()
                author_name = author_name.split('Verified')[0].strip()
                post_data['author_name'] = author_name
            else:
                post_data['author_name'] = ''
        except:
            post_data['author_name'] = ''
        
        # Extract Author Profile URL (to get URN from URL)
        try:
            author_link_elem = post_element.locator('a.update-components-actor__meta-link').first
            if author_link_elem.count() > 0:
                author_url = author_link_elem.get_attribute('href') or ''
                # Extract URN from URL if possible
                if '/in/' in author_url:
                    profile_slug = author_url.split('/in/')[-1].split('?')[0]
                    post_data['author_profile_url'] = f"https://www.linkedin.com{author_url}" if author_url.startswith('/') else author_url
                    post_data['author_urn'] = profile_slug  # Simplified, actual URN would need API
                else:
                    post_data['author_profile_url'] = author_url
                    post_data['author_urn'] = ''
            else:
                post_data['author_profile_url'] = ''
                post_data['author_urn'] = ''
        except:
            post_data['author_profile_url'] = ''
            post_data['author_urn'] = ''
        
        # Extract Post Text
        try:
            # Try to get full text (may need to click "see more" if truncated)
            text_elem = post_element.locator('div.update-components-text, div.feed-shared-inline-show-more-text').first
            if text_elem.count() > 0:
                # Check if there's a "see more" button
                see_more_btn = post_element.locator('button.feed-shared-inline-show-more-text__see-more-less-toggle').first
                if see_more_btn.count() > 0:
                    try:
                        see_more_btn.click()
                        random_delay(0.5, 1.0)
                    except:
                        pass
                
                post_text = text_elem.inner_text().strip()
                # Clean up "hashtag" prefix that appears before hashtags
                post_text = post_text.replace('hashtag\n#', '#').replace('hashtag\n', '')
                post_text = post_text.replace('\nhashtag\n', '\n').replace('\nhashtag', '')
                # Clean up multiple newlines
                post_text = re.sub(r'\n{3,}', '\n\n', post_text)
                post_data['post_text'] = post_text
            else:
                post_data['post_text'] = ''
        except:
            post_data['post_text'] = ''
        
        # Extract Image URL
        try:
            img_elem = post_element.locator('img.update-components-image__image, img.ivm-view-attr__img--centered').first
            if img_elem.count() > 0:
                post_data['image_url'] = img_elem.get_attribute('src') or ''
            else:
                post_data['image_url'] = ''
        except:
            post_data['image_url'] = ''
        
        # Extract Engagement Metrics
        try:
            # Reactions count
            reactions_elem = post_element.locator('span.social-details-social-counts__reactions-count, button[data-reaction-details] span').first
            if reactions_elem.count() > 0:
                reactions_text = reactions_elem.inner_text().strip()
                # Parse number (handle "1", "1.2K", etc.)
                post_data['reactions_count'] = reactions_text
            else:
                post_data['reactions_count'] = '0'
        except:
            post_data['reactions_count'] = '0'
        
        try:
            # Comments count (if visible)
            comments_elem = post_element.locator('button[aria-label*="Comment"], button.comment-button').first
            if comments_elem.count() > 0:
                # Comments count might be in a separate element
                post_data['comments_count'] = 'N/A'  # LinkedIn often doesn't show count directly
            else:
                post_data['comments_count'] = 'N/A'
        except:
            post_data['comments_count'] = 'N/A'
        
        # Extract Timestamp
        try:
            timestamp_elem = post_element.locator('span.update-components-actor__sub-description').first
            if timestamp_elem.count() > 0:
                post_data['timestamp'] = timestamp_elem.inner_text().strip()
            else:
                post_data['timestamp'] = ''
        except:
            post_data['timestamp'] = ''
        
        # Extract Author Title/Description (get first line only, no duplicates)
        try:
            author_desc_elem = post_element.locator('span.update-components-actor__description').first
            if author_desc_elem.count() > 0:
                title_text = author_desc_elem.inner_text().strip()
                # Get first line only, remove duplicates
                title_lines = [line.strip() for line in title_text.split('\n') if line.strip()]
                if title_lines:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_lines = []
                    for line in title_lines:
                        if line not in seen:
                            seen.add(line)
                            unique_lines.append(line)
                    post_data['author_title'] = ' | '.join(unique_lines[:3])  # Max 3 lines
                else:
                    post_data['author_title'] = ''
            else:
                post_data['author_title'] = ''
        except:
            post_data['author_title'] = ''
        
        # Add scrape timestamp
        post_data['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return post_data
        
    except Exception as e:
        print(f"  ⚠ Error extracting post data: {str(e)}")
        return None


def scroll_feed(page: Page, scroll_count: int = 3):
    """
    Scroll the LinkedIn feed to load more posts
    
    Args:
        page: Playwright page object
        scroll_count: Number of times to scroll
    """
    print(f"→ Scrolling feed {scroll_count} times...")
    
    for i in range(scroll_count):
        # Scroll down
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        random_delay(2, 4)
        
        # Random mouse movement
        move_mouse_randomly(page)
        random_delay(0.5, 1.5)
        
        print(f"  ✓ Scroll {i+1}/{scroll_count} completed")


def scrape_linkedin_feed(page: Page, max_posts: int = 10, scroll_count: int = 3) -> List[Dict]:
    """
    Step 2: Scrape LinkedIn feed posts
    
    Args:
        page: Playwright page object
        max_posts: Maximum number of posts to scrape
        scroll_count: Number of times to scroll the feed
    
    Returns:
        list: List of post data dictionaries
    """
    print("\nStep 2: Scraping LinkedIn feed...")
    
    try:
        # Navigate to feed if not already there
        if 'feed' not in page.url:
            print("→ Navigating to LinkedIn feed...")
            try:
                response = page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=30000)
                if response:
                    print(f"  → Feed page loaded (Status: {response.status})")
                random_delay(3, 5)
            except Exception as e:
                print(f"  ⚠ Navigation error: {str(e)}")
                print("  → Checking if page loaded anyway...")
                random_delay(2, 3)
                if 'feed' not in page.url:
                    raise Exception("Failed to navigate to LinkedIn feed")
        
        # Wait for feed to load
        print("→ Waiting for feed to load...")
        page.wait_for_selector('div.scaffold-finite-scroll__content', timeout=10000)
        random_delay(2, 3)
        
        # Scroll to load more posts
        scroll_feed(page, scroll_count)
        
        # Find all post containers (prioritize actual posts with data-urn)
        print("→ Extracting posts...")
        # First try to get posts with proper URNs
        post_selector = 'div[data-urn*="activity"], div.feed-shared-update-v2[data-urn], div.occludable-update[data-urn]'
        post_elements = page.locator(post_selector).all()
        
        # If not enough, get all feed-shared-update-v2
        if len(post_elements) < 3:
            all_posts = page.locator('div.feed-shared-update-v2').all()
            # Combine and deduplicate
            seen_ids = set()
            unique_posts = []
            for post in all_posts:
                try:
                    post_id = post.get_attribute('data-urn') or post.get_attribute('id') or ''
                    if post_id and post_id not in seen_ids:
                        seen_ids.add(post_id)
                        unique_posts.append(post)
                except:
                    continue
            post_elements = unique_posts if unique_posts else post_elements
        
        print(f"  → Found {len(post_elements)} posts")
        
        posts_data = []
        processed_urns = set()  # Track processed posts to avoid duplicates
        
        for idx, post_elem in enumerate(post_elements[:max_posts]):
            try:
                # Get post URN to check for duplicates
                post_urn = post_elem.get_attribute('data-urn') or ''
                
                if post_urn and post_urn in processed_urns:
                    continue
                
                if post_urn:
                    processed_urns.add(post_urn)
                
                print(f"  → Extracting post {idx+1}/{min(len(post_elements), max_posts)}...")
                
                # Extract post data
                post_data = extract_post_data(page, post_elem)
                
                # Only add posts with meaningful data (has post text or valid URN)
                if post_data:
                    has_content = (
                        post_data.get('post_text', '').strip() or 
                        post_data.get('post_urn', '').startswith('urn:li:activity:') or
                        post_data.get('author_name', '').strip()
                    )
                    
                    if has_content:
                        posts_data.append(post_data)
                        author = post_data.get('author_name', 'Unknown')[:30]
                        text_preview = post_data.get('post_text', '')[:50].replace('\n', ' ')
                        print(f"    ✓ Extracted: {author} - {text_preview}...")
                    else:
                        print(f"    ⚠ Skipped post {idx+1} (no meaningful content)")
                else:
                    print(f"    ⚠ Skipped post {idx+1} (no data extracted)")
                
                # Random delay between extractions
                random_delay(0.5, 1.5)
                
            except Exception as e:
                print(f"    ✗ Error processing post {idx+1}: {str(e)}")
                continue
        
        print(f"\n✓ Successfully extracted {len(posts_data)} posts")
        return posts_data
        
    except Exception as e:
        print(f"✗ Feed scraping failed: {str(e)}")
        return []


def save_posts_to_csv(posts: List[Dict], filename: str = 'linkedin_posts.csv'):
    """
    Save scraped posts to CSV file
    
    Args:
        posts: List of post data dictionaries
        filename: Output CSV filename
    """
    if not posts:
        print("⚠ No posts to save")
        return
    
    print(f"\n→ Saving {len(posts)} posts to {filename}...")
    
    # Define CSV columns
    fieldnames = [
        'post_urn',
        'author_urn',
        'author_name',
        'author_title',
        'author_profile_url',
        'post_text',
        'image_url',
        'reactions_count',
        'comments_count',
        'timestamp',
        'scraped_at'
    ]
    
    try:
        # Create output directory if it doesn't exist
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        # Write to CSV with proper escaping
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for post in posts:
                # Ensure all fields exist and clean newlines for CSV
                row = {}
                for field in fieldnames:
                    value = post.get(field, '')
                    # Replace newlines with spaces for better CSV readability (or keep them if needed)
                    # For post_text, we'll keep newlines but ensure proper CSV escaping
                    if field == 'post_text':
                        # Keep newlines but ensure proper CSV formatting
                        row[field] = value
                    else:
                        # Replace newlines with spaces for other fields
                        row[field] = str(value).replace('\n', ' ').replace('\r', ' ').strip()
                writer.writerow(row)
        
        print(f"✓ Posts saved to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"✗ Error saving CSV: {str(e)}")
        return None


def main():
    """Main function to run the LinkedIn scraper"""
    
    # Get credentials from environment variables
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', 'your_email@example.com')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', 'your_password')
    
    with sync_playwright() as p:
        # Launch browser with anti-detection settings
        print("→ Launching browser...")
        browser = p.chromium.launch(
            headless=False,  # Set to True for production (but may increase detection)
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                # Removed --disable-web-security as it can cause network issues
                # Removed --disable-features=IsolateOrigins,site-per-process as it can block network
            ]
        )
        
        # Create context with realistic headers and settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            # Ensure network is enabled
            offline=False,
            java_script_enabled=True,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            # Network settings
            ignore_https_errors=False,
            bypass_csp=False,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Hide webdriver property
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override the plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Add chrome object
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Create new page
        page = context.new_page()
        
        # Test network connectivity
        try:
            print("→ Testing network connectivity...")
            response = page.goto('https://www.google.com', wait_until='domcontentloaded', timeout=10000)
            if response and response.status == 200:
                print("✓ Network connectivity confirmed")
            else:
                print("⚠ Network response status:", response.status if response else "No response")
        except Exception as e:
            print(f"⚠ Network test failed: {str(e)}")
            print("⚠ Continuing anyway - check your internet connection")
        
        try:
            # Step 1: Login
            if login_to_linkedin(page, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
                # Step 2: Scrape feed posts
                posts = scrape_linkedin_feed(page, max_posts=20, scroll_count=5)
                
                # Step 3: Save to CSV
                if posts:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'linkedin_posts_{timestamp}.csv'
                    save_posts_to_csv(posts, filename)
                    print(f"\n✓ Scraped and saved {len(posts)} posts successfully!")
                else:
                    print("\n⚠ No posts were scraped")
                
                print("\n✓ All steps completed successfully!")
            else:
                print("\n✗ Process failed at login step")
            
            # Keep browser open for inspection
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
