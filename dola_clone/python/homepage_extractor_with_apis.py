import requests
from bs4 import BeautifulSoup
import json
import asyncio
import aiohttp
from datetime import datetime
import os
from urllib.parse import urljoin, urlparse
import re

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
                            self.base_url = f"{data['url']}/api"
                            return self.base_url
                    raise Exception("Invalid response for base URL")
        except Exception as e:
            print(f"Error fetching base URL: {e}")
            # Fallback URLs
            fallback_urls = {
                "gavn138": "https://bo.gavn138.com/api",
                "staging": "https://staging.gasv388.net/api"
            }
            self.base_url = fallback_urls.get(self.site_code, "https://bo.gavn138.com/api")
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
        """Get current user information"""
        try:
            async with self.session.get("/user") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
        return None
    
    # Game APIs
    async def get_game_categories(self):
        """Get all game categories"""
        try:
            async with self.session.get("/player/game_categories") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting game categories: {e}")
        return None
    
    async def get_all_category_games(self):
        """Get games from all categories"""
        try:
            async with self.session.get("/player/game_categories_items_v2") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting category games: {e}")
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
        """Get balance for specific game"""
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
            'transaction_amount': amount * 1000,
            'bank_id': bank_id,
            'payment_method': payment_method,
            'payment_method_code': payment_method_code,
            'category_id': category_id,
            'category_code': category_code
        }
        try:
            async with self.session.post("/account/deposit", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data')
        except Exception as e:
            print(f"Error making deposit: {e}")
        return None
    
    async def get_all_transactions(self):
        """Get all user transactions"""
        try:
            async with self.session.get("/account/transactions") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting transactions: {e}")
        return None
    
    # Banner APIs
    async def get_banner_images(self, device="desktop"):
        """Get banner images"""
        try:
            async with self.session.get(f"/image-slider/list?device={device}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting banners: {e}")
        return None
    
    # Bank APIs
    async def get_bank_list(self):
        """Get available banks"""
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

class DolaHomepageExtractor:
    def __init__(self, url="https://www.dolaa789.cc/"):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_homepage(self):
        """Extract complete homepage HTML and assets"""
        try:
            print(f"Fetching homepage from {self.url}...")
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract and download assets
            self.process_assets(soup)
            
            # Save the main HTML
            html_content = soup.prettify()
            
            # Create output directory
            os.makedirs('extracted_homepage', exist_ok=True)
            
            # Save main HTML file
            with open('extracted_homepage/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print("Homepage extracted successfully!")
            return html_content
            
        except Exception as e:
            print(f"Error extracting homepage: {e}")
            return None
    
    def process_assets(self, soup):
        """Download and process CSS, JS, and image assets"""
        base_url = self.url
        
        # Create asset directories
        os.makedirs('extracted_homepage/css', exist_ok=True)
        os.makedirs('extracted_homepage/js', exist_ok=True)
        os.makedirs('extracted_homepage/images', exist_ok=True)
        
        # Process CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                self.download_asset(href, base_url, 'css')
        
        # Process JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                self.download_asset(src, base_url, 'js')
        
        # Process images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                self.download_asset(src, base_url, 'images')
    
    def download_asset(self, asset_url, base_url, asset_type):
        """Download individual asset file"""
        try:
            full_url = urljoin(base_url, asset_url)
            filename = os.path.basename(urlparse(asset_url).path)
            
            if not filename:
                filename = f"asset_{hash(asset_url)}"
            
            # Add appropriate extension if missing
            if asset_type == 'css' and not filename.endswith('.css'):
                filename += '.css'
            elif asset_type == 'js' and not filename.endswith('.js'):
                filename += '.js'
            
            filepath = os.path.join('extracted_homepage', asset_type, filename)
            
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filename}")
            
        except Exception as e:
            print(f"Error downloading {asset_url}: {e}")

async def main():
    """Main function to demonstrate usage"""
    print("=== DOLA Homepage Extractor with API Implementation ===")
    
    # Extract homepage
    extractor = DolaHomepageExtractor()
    homepage_content = extractor.extract_homepage()
    
    if homepage_content:
        print("\n✅ Homepage extraction completed!")
        print("Files saved in 'extracted_homepage' directory")
    
    # Initialize API clients for both projects
    print("\n=== Initializing API Clients ===")
    
    # GASV API Client (gavn138 site code)
    gasv_client = DolaAPIClient(site_code="gavn138")
    await gasv_client.init_session()
    
    # SVW38 API Client (staging site code)
    svw38_client = DolaAPIClient(site_code="staging")
    await svw38_client.init_session()
    
    print(f"GASV Base URL: {gasv_client.base_url}")
    print(f"SVW38 Base URL: {svw38_client.base_url}")
    
    # Test API endpoints
    print("\n=== Testing API Endpoints ===")
    
    try:
        # Test banner images
        print("Fetching banner images...")
        banners = await gasv_client.get_banner_images()
        if banners:
            print(f"✅ Found {len(banners.get('data', []))} banners")
        
        # Test game categories
        print("Fetching game categories...")
        categories = await gasv_client.get_game_categories()
        if categories:
            print(f"✅ Found game categories")
        
        # Test bank list
        print("Fetching bank list...")
        banks = await gasv_client.get_bank_list()
        if banks:
            print(f"✅ Found bank information")
        
        # Example user registration (commented out for safety)
        # print("Testing user registration...")
        # result = await gasv_client.register_user("1234567890", "password123")
        
        # Example login (commented out for safety)
        # print("Testing user login...")
        # login_result = await gasv_client.login_user("1234567890", "password123")
        
    except Exception as e:
        print(f"Error testing APIs: {e}")
    
    # Save API documentation
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
        "extracted_at": datetime.now().isoformat()
    }
    
    with open('extracted_homepage/api_documentation.json', 'w', encoding='utf-8') as f:
        json.dump(api_docs, f, indent=2, ensure_ascii=False)
    
    print("\n✅ API documentation saved to 'extracted_homepage/api_documentation.json'")
    
    # Clean up
    await gasv_client.close()
    await svw38_client.close()
    
    print("\n🎉 Script completed successfully!")
    print("\nFiles created:")
    print("- extracted_homepage/index.html (main homepage)")
    print("- extracted_homepage/css/ (stylesheets)")
    print("- extracted_homepage/js/ (javascript files)")
    print("- extracted_homepage/images/ (images)")
    print("- extracted_homepage/api_documentation.json (API endpoints)")

if __name__ == "__main__":
    # Install required packages
    print("Required packages: requests, beautifulsoup4, aiohttp")
    print("Install with: pip install requests beautifulsoup4 aiohttp")
    print()
    
    # Run the main function
    asyncio.run(main())