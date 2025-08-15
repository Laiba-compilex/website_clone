import requests
from bs4 import BeautifulSoup
import json
import asyncio
import aiohttp
from datetime import datetime
import os
from urllib.parse import urljoin, urlparse, parse_qs
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import hashlib

class DolaAPIClient:
    def __init__(self, site_code="gavn138"):
        self.site_code = site_code
        self.base_url = None
        self.session = None
        self.auth_token = None
        
    async def fetch_base_url(self):
        """Fetch dynamic base URL from CDN tracker"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://cdntracker0019.com?site_code={self.site_code}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('url'):
                            self.base_url = f"{data['url']}/api/"
                            return self.base_url
                    raise Exception("Invalid response for base URL")
        except Exception as e:
            print(f"Error fetching base URL: {e}")
            # Fallback URLs
            fallback_urls = {
                "gavn138": "https://bo.gavn138.com/api/",
                "staging": "https://staging.gasv388.net/api/"
            }
            self.base_url = fallback_urls.get(self.site_code, "https://bo.gavn138.com/api/")
            return self.base_url
    
    async def init_session(self):
        """Initialize aiohttp session with base URL"""
        if not self.base_url:
            await self.fetch_base_url()
        
        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    def set_auth_token(self, token):
        """Set authentication token"""
        self.auth_token = token
        if self.session:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    # User APIs
    async def check_phone_exists(self, phone):
        """Check if phone number exists"""
        try:
            async with self.session.get(f"/check_phone/{phone}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error checking phone: {e}")
        return None
    
    async def register_user(self, phone, password, agent_id=None, fp_data=None):
        """Register new user"""
        data = {
            'phone': phone,
            'password': password,
            'agent_id': agent_id,
            'fp_data': fp_data
        }
        try:
            async with self.session.post("/register_user", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') and result.get('token'):
                        return result['token']
        except Exception as e:
            print(f"Error registering user: {e}")
        return None
    
    async def login_user(self, phone, password):
        """Login user"""
        data = {'phone': phone, 'password': password}
        try:
            async with self.session.post("/login_user", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('message') == 'LOGIN_SUCCESS':
                        token = result.get('token')
                        if token:
                            self.set_auth_token(token)
                        return result
        except Exception as e:
            print(f"Error logging in: {e}")
        return None
    
    async def get_user_info(self):
        """Get user information"""
        try:
            async with self.session.get("/user") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
        return None
    
    # Game APIs
    async def get_game_categories(self):
        """Get game categories"""
        try:
            async with self.session.get("/player/game_categories") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting game categories: {e}")
        return None
    
    async def get_all_category_games(self):
        """Get all games across categories"""
        try:
            async with self.session.get("/player/game_categories_items_v2") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting all games: {e}")
        return None
    
    async def get_trending_games(self):
        """Get trending games"""
        try:
            async with self.session.get("/player/trending_games") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting trending games: {e}")
        return None
    
    async def get_game_balance(self, game_id):
        """Get game balance"""
        try:
            async with self.session.get(f"/player/game_balance/{game_id}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting game balance: {e}")
        return None
    
    # Transaction APIs
    async def make_deposit_request(self, amount, bank_id, payment_method, payment_method_code, category_id, category_code):
        """Make deposit request"""
        data = {
            'amount': amount,
            'bank_id': bank_id,
            'payment_method': payment_method,
            'payment_method_code': payment_method_code,
            'category_id': category_id,
            'category_code': category_code
        }
        try:
            async with self.session.post("/account/deposit", json=data) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error making deposit: {e}")
        return None
    
    async def get_all_transactions(self):
        """Get all transactions"""
        try:
            async with self.session.get("/account/transactions") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting transactions: {e}")
        return None
    
    # Content APIs
    async def get_banner_images(self, device="desktop"):
        """Get banner images"""
        try:
            async with self.session.get(f"/image-slider/list?device={device}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting banners: {e}")
        return None
    
    async def get_bank_list(self):
        """Get bank list"""
        try:
            async with self.session.get("/banks") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting banks: {e}")
        return None
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

class EnhancedDolaExtractor:
    def __init__(self, url="https://www.dolaa789.cc/"):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.downloaded_assets = set()
        self.failed_downloads = []
        
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver for dynamic content extraction"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Warning: Could not initialize Selenium driver: {e}")
            print("Falling back to requests-only mode. Some dynamic content may be missed.")
            return None
    
    def extract_with_selenium(self):
        """Extract homepage using Selenium for dynamic content"""
        driver = self.setup_selenium_driver()
        if not driver:
            return self.extract_homepage_static()
        
        try:
            print(f"Loading page with Selenium: {self.url}")
            driver.get(self.url)
            
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for React/Vue to render
            time.sleep(5)
            
            # Try to trigger modals and dynamic content
            self.trigger_dynamic_content(driver)
            
            # Get final HTML after all dynamic content is loaded
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all assets
            self.process_all_assets(soup, driver)
            
            # Save the main HTML
            os.makedirs('extracted_homepage_enhanced', exist_ok=True)
            with open('extracted_homepage_enhanced/index.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print("✅ Enhanced extraction with Selenium completed!")
            return html_content
            
        except Exception as e:
            print(f"Error with Selenium extraction: {e}")
            return self.extract_homepage_static()
        finally:
            if driver:
                driver.quit()
    
    def trigger_dynamic_content(self, driver):
        """Trigger modals and dynamic content"""
        try:
            # Look for common modal triggers
            modal_triggers = [
                "[data-toggle='modal']",
                ".modal-trigger",
                "[onclick*='modal']",
                "[onclick*='Modal']",
                "[onclick*='popup']",
                "[onclick*='Popup']",
                ".login-btn",
                ".register-btn",
                ".play-btn",
                "[onclick*='checkLoginAndPlay']",
                "[onclick*='showLogin']",
                "[onclick*='showRegister']"
            ]
            
            for selector in modal_triggers:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:3]:  # Limit to first 3 to avoid too many clicks
                        try:
                            driver.execute_script("arguments[0].click();", element)
                            time.sleep(1)  # Wait for modal to appear
                        except:
                            continue
                except:
                    continue
            
            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            print(f"Warning: Error triggering dynamic content: {e}")
    
    def extract_homepage_static(self):
        """Fallback static extraction method"""
        try:
            print(f"Fetching homepage statically from {self.url}...")
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract and download assets
            self.process_all_assets(soup)
            
            # Save the main HTML
            html_content = soup.prettify()
            os.makedirs('extracted_homepage_enhanced', exist_ok=True)
            
            with open('extracted_homepage_enhanced/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("✅ Static homepage extraction completed!")
            return html_content
            
        except Exception as e:
            print(f"Error extracting homepage: {e}")
            return None
    
    def process_all_assets(self, soup, driver=None):
        """Comprehensive asset processing"""
        base_url = self.url
        
        # Create asset directories
        directories = ['css', 'js', 'images', 'fonts', 'videos', 'audio', 'documents']
        for directory in directories:
            os.makedirs(f'extracted_homepage_enhanced/{directory}', exist_ok=True)
        
        print("\n=== Processing Assets ===")
        
        # Process CSS files
        print("Processing CSS files...")
        css_links = soup.find_all('link', rel='stylesheet') + soup.find_all('link', type='text/css')
        for link in css_links:
            href = link.get('href')
            if href:
                self.download_asset(href, base_url, 'css')
        
        # Process JavaScript files
        print("Processing JavaScript files...")
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                self.download_asset(src, base_url, 'js')
        
        # Process all images (including lazy-loaded ones)
        print("Processing images...")
        image_selectors = ['img[src]', 'img[data-src]', 'img[data-lazy]', '[style*="background-image"]']
        for selector in image_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Regular src
                src = element.get('src')
                if src:
                    self.download_asset(src, base_url, 'images')
                
                # Data attributes for lazy loading
                for attr in ['data-src', 'data-lazy', 'data-original']:
                    data_src = element.get(attr)
                    if data_src:
                        self.download_asset(data_src, base_url, 'images')
                
                # Background images from style
                style = element.get('style', '')
                bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)', style)
                for bg_url in bg_matches:
                    self.download_asset(bg_url, base_url, 'images')
        
        # Process fonts
        print("Processing fonts...")
        font_links = soup.find_all('link', href=re.compile(r'\.(woff|woff2|ttf|otf|eot)$', re.I))
        for link in font_links:
            href = link.get('href')
            if href:
                self.download_asset(href, base_url, 'fonts')
        
        # Process videos
        print("Processing videos...")
        for video in soup.find_all(['video', 'source']):
            src = video.get('src')
            if src:
                self.download_asset(src, base_url, 'videos')
        
        # Process audio
        print("Processing audio...")
        for audio in soup.find_all(['audio', 'source']):
            src = audio.get('src')
            if src and any(ext in src.lower() for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                self.download_asset(src, base_url, 'audio')
        
        # Extract inline CSS and JS
        self.extract_inline_assets(soup)
        
        # Generate asset manifest
        self.generate_asset_manifest()
        
        print(f"\n✅ Asset processing completed!")
        print(f"Downloaded: {len(self.downloaded_assets)} assets")
        if self.failed_downloads:
            print(f"Failed: {len(self.failed_downloads)} assets")
    
    def download_asset(self, asset_url, base_url, asset_type):
        """Enhanced asset download with better error handling"""
        try:
            # Skip if already downloaded
            if asset_url in self.downloaded_assets:
                return
            
            # Skip data URLs
            if asset_url.startswith('data:'):
                return
            
            full_url = urljoin(base_url, asset_url)
            
            # Generate filename
            parsed_url = urlparse(asset_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                # Generate filename from URL hash
                url_hash = hashlib.md5(asset_url.encode()).hexdigest()[:8]
                extensions = {
                    'css': '.css',
                    'js': '.js',
                    'images': '.jpg',
                    'fonts': '.woff',
                    'videos': '.mp4',
                    'audio': '.mp3'
                }
                filename = f"asset_{url_hash}{extensions.get(asset_type, '')}"
            
            # Ensure proper extension
            if asset_type == 'css' and not filename.endswith('.css'):
                filename += '.css'
            elif asset_type == 'js' and not filename.endswith('.js'):
                filename += '.js'
            
            filepath = os.path.join('extracted_homepage_enhanced', asset_type, filename)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                self.downloaded_assets.add(asset_url)
                return
            
            # Download with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(full_url, timeout=15, stream=True)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    self.downloaded_assets.add(asset_url)
                    print(f"✅ Downloaded: {filename} ({asset_type})")
                    return
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.failed_downloads.append({'url': asset_url, 'error': str(e)})
                        print(f"❌ Failed: {filename} - {e}")
                    else:
                        time.sleep(1)  # Wait before retry
            
        except Exception as e:
            self.failed_downloads.append({'url': asset_url, 'error': str(e)})
            print(f"❌ Error downloading {asset_url}: {e}")
    
    def extract_inline_assets(self, soup):
        """Extract inline CSS and JavaScript"""
        # Extract inline CSS
        inline_css = []
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                inline_css.append(style_tag.string)
        
        if inline_css:
            with open('extracted_homepage_enhanced/css/inline_styles.css', 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(inline_css))
            print("✅ Extracted inline CSS")
        
        # Extract inline JavaScript
        inline_js = []
        for script_tag in soup.find_all('script'):
            if script_tag.string and not script_tag.get('src'):
                inline_js.append(script_tag.string)
        
        if inline_js:
            with open('extracted_homepage_enhanced/js/inline_scripts.js', 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(inline_js))
            print("✅ Extracted inline JavaScript")
    
    def generate_asset_manifest(self):
        """Generate manifest of all downloaded assets"""
        manifest = {
            'extracted_at': datetime.now().isoformat(),
            'source_url': self.url,
            'total_assets': len(self.downloaded_assets),
            'failed_downloads': len(self.failed_downloads),
            'downloaded_assets': list(self.downloaded_assets),
            'failed_assets': self.failed_downloads
        }
        
        with open('extracted_homepage_enhanced/asset_manifest.json', 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print("✅ Generated asset manifest")
    
    def generate_browser_script(self, soup):
        """Generate browser console script for CORS-free asset download"""
        assets = {
            'css': [],
            'js': [],
            'images': []
        }
        
        # Extract asset URLs
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and not href.startswith('data:'):
                assets['css'].append(href)
        
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.startswith('data:'):
                assets['js'].append(src)
        
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and not src.startswith('data:'):
                assets['images'].append(src)
        
        browser_script = f"""
// DOLA Homepage Asset Downloader - Run in Browser Console
// This script downloads assets directly from the browser to avoid CORS issues

const assets = {json.dumps(assets, indent=2)};

async function downloadAsset(url, filename, type) {{
    try {{
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        
        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename || `asset_${{Date.now()}}.${{type}}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        
        console.log(`✅ Downloaded: ${{filename}}`);
    }} catch (error) {{
        console.error(`❌ Failed to download ${{url}}:`, error);
    }}
}}

async function downloadAllAssets() {{
    console.log('🚀 Starting asset download...');
    
    for (const [type, urls] of Object.entries(assets)) {{
        console.log(`Downloading ${{urls.length}} ${{type}} files...`);
        
        for (let i = 0; i < urls.length; i++) {{
            const url = urls[i];
            const filename = url.split('/').pop() || `${{type}}_${{i}}`;
            
            await downloadAsset(url, filename, type);
            
            // Add delay to avoid overwhelming the browser
            if (i % 5 === 0) await new Promise(resolve => setTimeout(resolve, 1000));
        }}
    }}
    
    console.log('✅ Asset download completed!');
}}

// Start download
downloadAllAssets();
"""
        
        with open('extracted_homepage_enhanced/browser_asset_downloader.js', 'w', encoding='utf-8') as f:
            f.write(browser_script)
        
        print("✅ Generated browser asset downloader script")

async def main():
    """Enhanced main function"""
    print("=== ENHANCED DOLA Homepage Extractor with Comprehensive API Implementation ===")
    print("This enhanced version includes:")
    print("- Selenium-based dynamic content extraction")
    print("- Modal and popup detection")
    print("- Comprehensive asset downloading (CSS, JS, images, fonts, videos)")
    print("- Inline asset extraction")
    print("- Browser console script generation")
    print("- Enhanced error handling and retry logic")
    print("- Asset manifest generation")
    print()
    
    # Extract homepage with enhanced features
    extractor = EnhancedDolaExtractor()
    
    # Try Selenium first, fallback to static
    homepage_content = extractor.extract_with_selenium()
    
    if homepage_content:
        print("\n✅ Enhanced homepage extraction completed!")
        print("Files saved in 'extracted_homepage_enhanced' directory")
        
        # Generate browser script
        soup = BeautifulSoup(homepage_content, 'html.parser')
        extractor.generate_browser_script(soup)
    
    # Initialize API clients for both projects
    print("\n=== Initializing Enhanced API Clients ===")
    
    # GASV API Client (gavn138 site code)
    gasv_client = DolaAPIClient(site_code="gavn138")
    await gasv_client.init_session()
    
    # SVW38 API Client (staging site code)
    svw38_client = DolaAPIClient(site_code="staging")
    await svw38_client.init_session()
    
    print(f"GASV Base URL: {gasv_client.base_url}")
    print(f"SVW38 Base URL: {svw38_client.base_url}")
    
    # Test API endpoints with enhanced error handling
    print("\n=== Testing Enhanced API Endpoints ===")
    
    api_test_results = {}
    
    try:
        # Test banner images
        print("Fetching banner images...")
        banners = await gasv_client.get_banner_images()
        api_test_results['banners'] = banners is not None
        if banners:
            print(f"✅ Found {len(banners.get('data', []))} banners")
        
        # Test game categories
        print("Fetching game categories...")
        categories = await gasv_client.get_game_categories()
        api_test_results['categories'] = categories is not None
        if categories:
            print(f"✅ Found game categories")
        
        # Test all games
        print("Fetching all games...")
        all_games = await gasv_client.get_all_category_games()
        api_test_results['all_games'] = all_games is not None
        if all_games:
            print(f"✅ Found all games data")
        
        # Test trending games
        print("Fetching trending games...")
        trending = await gasv_client.get_trending_games()
        api_test_results['trending'] = trending is not None
        if trending:
            print(f"✅ Found trending games")
        
        # Test bank list
        print("Fetching bank list...")
        banks = await gasv_client.get_bank_list()
        api_test_results['banks'] = banks is not None
        if banks:
            print(f"✅ Found bank information")
        
        # Test SVW38 APIs
        print("Testing SVW38 APIs...")
        svw38_banners = await svw38_client.get_banner_images()
        api_test_results['svw38_banners'] = svw38_banners is not None
        if svw38_banners:
            print(f"✅ SVW38 banners working")
        
    except Exception as e:
        print(f"Error testing APIs: {e}")
    
    # Save comprehensive API documentation
    api_docs = {
        "endpoints": {
            "user_management": {
                "check_phone": "/check_phone/{phone}",
                "register": "/register_user",
                "login": "/login_user",
                "user_info": "/user"
            },
            "games": {
                "categories": "/player/game_categories",
                "all_games": "/player/game_categories_items_v2",
                "trending": "/player/trending_games",
                "balance": "/player/game_balance/{game_id}"
            },
            "transactions": {
                "deposit": "/account/deposit",
                "all_transactions": "/account/transactions",
                "check_transaction": "/account/transaction/{id}"
            },
            "content": {
                "banners": "/image-slider/list",
                "banks": "/banks",
                "announcements": "/announcements"
            }
        },
        "base_urls": {
            "gasv": gasv_client.base_url,
            "svw38": svw38_client.base_url
        },
        "api_test_results": api_test_results,
        "extracted_at": datetime.now().isoformat(),
        "features": [
            "Dynamic content extraction with Selenium",
            "Modal and popup detection",
            "Comprehensive asset downloading",
            "Inline asset extraction",
            "Browser console script generation",
            "Enhanced error handling",
            "Asset manifest generation",
            "API endpoint testing"
        ]
    }
    
    with open('extracted_homepage_enhanced/comprehensive_api_documentation.json', 'w', encoding='utf-8') as f:
        json.dump(api_docs, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Comprehensive API documentation saved")
    
    # Clean up
    await gasv_client.close()
    await svw38_client.close()
    
    print("\n🎉 Enhanced script completed successfully!")
    print("\nFiles created:")
    print("- extracted_homepage_enhanced/index.html (complete homepage with modals)")
    print("- extracted_homepage_enhanced/css/ (all stylesheets + inline CSS)")
    print("- extracted_homepage_enhanced/js/ (all javascript + inline JS)")
    print("- extracted_homepage_enhanced/images/ (all images including lazy-loaded)")
    print("- extracted_homepage_enhanced/fonts/ (web fonts)")
    print("- extracted_homepage_enhanced/videos/ (video files)")
    print("- extracted_homepage_enhanced/audio/ (audio files)")
    print("- extracted_homepage_enhanced/asset_manifest.json (download report)")
    print("- extracted_homepage_enhanced/browser_asset_downloader.js (CORS-free downloader)")
    print("- extracted_homepage_enhanced/comprehensive_api_documentation.json (complete API docs)")
    print("\nTo use the browser script:")
    print("1. Open https://www.dolaa789.cc/ in your browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Console tab")
    print("4. Copy and paste the content of browser_asset_downloader.js")
    print("5. Press Enter to start downloading assets directly from browser")

if __name__ == "__main__":
    print("Enhanced DOLA Homepage Extractor")
    print("Required packages: requests, beautifulsoup4, aiohttp, selenium")
    print("Install with: pip install requests beautifulsoup4 aiohttp selenium")
    print("Note: Chrome/Chromium browser required for Selenium features")
    print()
    
    # Run the enhanced main function
    asyncio.run(main())