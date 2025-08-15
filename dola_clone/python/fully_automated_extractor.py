import requests
from bs4 import BeautifulSoup
import json
import asyncio
import aiohttp
from datetime import datetime
import os
from urllib.parse import urljoin, urlparse
import re
import time
import base64
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import zipfile
import argparse

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
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

class FullyAutomatedExtractor:
    def __init__(self, target_url):
        self.target_url = target_url
        self.driver = None
        self.extracted_data = {
            'html': '',
            'css': {},
            'js': {},
            'images': {},
            'fonts': {},
            'other_assets': {}
        }
        self.output_dir = f"extracted_{urlparse(target_url).netloc.replace('.', '_')}"
        
    def setup_driver(self):
        """Setup Chrome driver with optimal settings"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            return False
    
    def inject_extraction_script(self):
        """Inject comprehensive extraction JavaScript"""
        extraction_script = """
        // Comprehensive Website Extractor - Bypasses CORS
        window.extractedData = {
            html: '',
            css: {},
            js: {},
            images: {},
            fonts: {},
            other_assets: {},
            modals: []
        };
        
        // Function to convert blob/file to base64
        async function blobToBase64(blob) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
        }
        
        // Function to fetch and convert assets to base64
        async function fetchAssetAsBase64(url) {
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const blob = await response.blob();
                return await blobToBase64(blob);
            } catch (error) {
                console.warn(`Failed to fetch ${url}:`, error);
                return null;
            }
        }
        
        // Extract all CSS
        async function extractCSS() {
            console.log('🎨 Extracting CSS...');
            
            // External CSS files
            const linkElements = document.querySelectorAll('link[rel="stylesheet"]');
            for (let link of linkElements) {
                const href = link.href;
                if (href && !href.startsWith('data:')) {
                    const filename = href.split('/').pop() || `css_${Date.now()}.css`;
                    const content = await fetchAssetAsBase64(href);
                    if (content) {
                        window.extractedData.css[filename] = {
                            url: href,
                            content: content,
                            type: 'external'
                        };
                    }
                }
            }
            
            // Inline CSS
            const styleElements = document.querySelectorAll('style');
            styleElements.forEach((style, index) => {
                if (style.textContent.trim()) {
                    window.extractedData.css[`inline_${index}.css`] = {
                        content: btoa(style.textContent),
                        type: 'inline'
                    };
                }
            });
            
            console.log(`✅ Extracted ${Object.keys(window.extractedData.css).length} CSS files`);
        }
        
        // Extract all JavaScript
        async function extractJS() {
            console.log('⚡ Extracting JavaScript...');
            
            // External JS files
            const scriptElements = document.querySelectorAll('script[src]');
            for (let script of scriptElements) {
                const src = script.src;
                if (src && !src.startsWith('data:')) {
                    const filename = src.split('/').pop() || `js_${Date.now()}.js`;
                    const content = await fetchAssetAsBase64(src);
                    if (content) {
                        window.extractedData.js[filename] = {
                            url: src,
                            content: content,
                            type: 'external'
                        };
                    }
                }
            }
            
            // Inline JavaScript
            const inlineScripts = document.querySelectorAll('script:not([src])');
            inlineScripts.forEach((script, index) => {
                if (script.textContent.trim()) {
                    window.extractedData.js[`inline_${index}.js`] = {
                        content: btoa(script.textContent),
                        type: 'inline'
                    };
                }
            });
            
            console.log(`✅ Extracted ${Object.keys(window.extractedData.js).length} JS files`);
        }
        
        // Extract all images
        async function extractImages() {
            console.log('🖼️ Extracting Images...');
            
            const imageSelectors = [
                'img[src]',
                'img[data-src]',
                'img[data-lazy]',
                '[style*="background-image"]'
            ];
            
            const imageUrls = new Set();
            
            // Regular img tags
            imageSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(element => {
                    // Regular src
                    const src = element.src || element.getAttribute('src');
                    if (src && !src.startsWith('data:')) imageUrls.add(src);
                    
                    // Data attributes
                    ['data-src', 'data-lazy', 'data-original'].forEach(attr => {
                        const dataSrc = element.getAttribute(attr);
                        if (dataSrc && !dataSrc.startsWith('data:')) {
                            imageUrls.add(dataSrc.startsWith('http') ? dataSrc : new URL(dataSrc, window.location.origin).href);
                        }
                    });
                    
                    // Background images
                    const style = element.getAttribute('style') || '';
                    const bgMatches = style.match(/background-image:\s*url\(["']?([^"')]+)["']?\)/g);
                    if (bgMatches) {
                        bgMatches.forEach(match => {
                            const url = match.match(/url\(["']?([^"')]+)["']?\)/)[1];
                            if (!url.startsWith('data:')) {
                                imageUrls.add(url.startsWith('http') ? url : new URL(url, window.location.origin).href);
                            }
                        });
                    }
                });
            });
            
            // Download images
            for (let url of imageUrls) {
                const filename = url.split('/').pop().split('?')[0] || `image_${Date.now()}.jpg`;
                const content = await fetchAssetAsBase64(url);
                if (content) {
                    window.extractedData.images[filename] = {
                        url: url,
                        content: content
                    };
                }
            }
            
            console.log(`✅ Extracted ${Object.keys(window.extractedData.images).length} images`);
        }
        
        // Extract fonts
        async function extractFonts() {
            console.log('🔤 Extracting Fonts...');
            
            // Font face rules from stylesheets
            const fontUrls = new Set();
            
            for (let stylesheet of document.styleSheets) {
                try {
                    for (let rule of stylesheet.cssRules || stylesheet.rules || []) {
                        if (rule.type === CSSRule.FONT_FACE_RULE) {
                            const src = rule.style.src;
                            if (src) {
                                const urlMatches = src.match(/url\(["']?([^"')]+)["']?\)/g);
                                if (urlMatches) {
                                    urlMatches.forEach(match => {
                                        const url = match.match(/url\(["']?([^"')]+)["']?\)/)[1];
                                        if (!url.startsWith('data:')) {
                                            fontUrls.add(url.startsWith('http') ? url : new URL(url, window.location.origin).href);
                                        }
                                    });
                                }
                            }
                        }
                    }
                } catch (e) {
                    // Cross-origin stylesheet, skip
                }
            }
            
            // Download fonts
            for (let url of fontUrls) {
                const filename = url.split('/').pop().split('?')[0] || `font_${Date.now()}.woff`;
                const content = await fetchAssetAsBase64(url);
                if (content) {
                    window.extractedData.fonts[filename] = {
                        url: url,
                        content: content
                    };
                }
            }
            
            console.log(`✅ Extracted ${Object.keys(window.extractedData.fonts).length} fonts`);
        }
        
        // Trigger modals and dynamic content
        function triggerModals() {
            console.log('🎭 Triggering modals and dynamic content...');
            
            const modalTriggers = [
                '[data-toggle="modal"]',
                '.modal-trigger',
                '[onclick*="modal"]',
                '[onclick*="Modal"]',
                '[onclick*="popup"]',
                '[onclick*="Popup"]',
                '.login-btn',
                '.register-btn',
                '.play-btn',
                '[onclick*="checkLoginAndPlay"]',
                '[onclick*="showLogin"]',
                '[onclick*="showRegister"]',
                'button[type="button"]',
                '.btn',
                'a[href="#"]'
            ];
            
            modalTriggers.forEach(selector => {
                document.querySelectorAll(selector).forEach((element, index) => {
                    if (index < 3) { // Limit to first 3 elements per selector
                        try {
                            element.click();
                            // Record modal information
                            window.extractedData.modals.push({
                                trigger: selector,
                                element: element.outerHTML,
                                timestamp: Date.now()
                            });
                        } catch (e) {
                            // Element might not be clickable
                        }
                    }
                });
            });
            
            // Scroll to trigger lazy loading
            window.scrollTo(0, document.body.scrollHeight);
            setTimeout(() => window.scrollTo(0, 0), 1000);
        }
        
        // Main extraction function
        async function extractEverything() {
            console.log('🚀 Starting comprehensive extraction...');
            
            // Trigger modals first
            triggerModals();
            
            // Wait for dynamic content to load
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            // Extract all content
            await Promise.all([
                extractCSS(),
                extractJS(),
                extractImages(),
                extractFonts()
            ]);
            
            // Get final HTML
            window.extractedData.html = document.documentElement.outerHTML;
            
            console.log('✅ Extraction completed!');
            console.log('📊 Extraction Summary:');
            console.log(`- HTML: ${window.extractedData.html.length} characters`);
            console.log(`- CSS files: ${Object.keys(window.extractedData.css).length}`);
            console.log(`- JS files: ${Object.keys(window.extractedData.js).length}`);
            console.log(`- Images: ${Object.keys(window.extractedData.images).length}`);
            console.log(`- Fonts: ${Object.keys(window.extractedData.fonts).length}`);
            console.log(`- Modals triggered: ${window.extractedData.modals.length}`);
            
            return window.extractedData;
        }
        
        // Start extraction
        return extractEverything();
        """
        
        return self.driver.execute_script(extraction_script)
    
    def save_extracted_data(self, data):
        """Save all extracted data to files"""
        print(f"\n💾 Saving extracted data to '{self.output_dir}'...")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ['css', 'js', 'images', 'fonts', 'other_assets']
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
        
        # Save HTML
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(data['html'])
        print("✅ Saved index.html")
        
        # Save CSS files
        for filename, css_data in data['css'].items():
            filepath = os.path.join(self.output_dir, 'css', filename)
            content = base64.b64decode(css_data['content']).decode('utf-8', errors='ignore')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f"✅ Saved {len(data['css'])} CSS files")
        
        # Save JS files
        for filename, js_data in data['js'].items():
            filepath = os.path.join(self.output_dir, 'js', filename)
            content = base64.b64decode(js_data['content']).decode('utf-8', errors='ignore')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f"✅ Saved {len(data['js'])} JS files")
        
        # Save images
        for filename, img_data in data['images'].items():
            filepath = os.path.join(self.output_dir, 'images', filename)
            content = base64.b64decode(img_data['content'])
            with open(filepath, 'wb') as f:
                f.write(content)
        print(f"✅ Saved {len(data['images'])} images")
        
        # Save fonts
        for filename, font_data in data['fonts'].items():
            filepath = os.path.join(self.output_dir, 'fonts', filename)
            content = base64.b64decode(font_data['content'])
            with open(filepath, 'wb') as f:
                f.write(content)
        print(f"✅ Saved {len(data['fonts'])} fonts")
        
        # Save extraction report
        report = {
            'extraction_date': datetime.now().isoformat(),
            'target_url': self.target_url,
            'summary': {
                'html_size': len(data['html']),
                'css_files': len(data['css']),
                'js_files': len(data['js']),
                'images': len(data['images']),
                'fonts': len(data['fonts']),
                'modals_triggered': len(data.get('modals', []))
            },
            'modals_triggered': data.get('modals', [])
        }
        
        with open(os.path.join(self.output_dir, 'extraction_report.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("✅ Saved extraction report")
    
    def create_zip_archive(self):
        """Create a zip archive of all extracted files"""
        zip_filename = f"{self.output_dir}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arcname)
        print(f"✅ Created zip archive: {zip_filename}")
        return zip_filename
    
    async def extract_website(self):
        """Main extraction method"""
        print(f"🎯 Starting automated extraction of: {self.target_url}")
        
        # Setup driver
        if not self.setup_driver():
            print("❌ Failed to setup Chrome driver")
            return False
        
        try:
            # Load the website
            print(f"🌐 Loading website: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            print("⏳ Waiting for dynamic content to load...")
            time.sleep(5)
            
            # Inject and run extraction script
            print("🔧 Injecting extraction script...")
            extracted_data = await asyncio.get_event_loop().run_in_executor(
                None, self.inject_extraction_script
            )
            
            # Wait for extraction to complete
            print("⏳ Waiting for extraction to complete...")
            time.sleep(10)
            
            # Get the extracted data
            final_data = self.driver.execute_script("return window.extractedData;")
            
            if final_data and final_data.get('html'):
                # Save all data
                self.save_extracted_data(final_data)
                
                # Create zip archive
                zip_file = self.create_zip_archive()
                
                print(f"\n🎉 Extraction completed successfully!")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📦 Zip archive: {zip_file}")
                
                return True
            else:
                print("❌ No data extracted")
                return False
                
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

async def test_apis(gasv_client, svw38_client):
    """Test API endpoints from both frontend projects"""
    print("\n🔌 Testing API endpoints...")
    
    api_results = {}
    
    try:
        # Test GASV APIs
        print("Testing GASV APIs...")
        banners = await gasv_client.get_banner_images()
        api_results['gasv_banners'] = banners is not None
        
        categories = await gasv_client.get_game_categories()
        api_results['gasv_categories'] = categories is not None
        
        # Test SVW38 APIs
        print("Testing SVW38 APIs...")
        svw38_banners = await svw38_client.get_banner_images()
        api_results['svw38_banners'] = svw38_banners is not None
        
        print("✅ API testing completed")
        
    except Exception as e:
        print(f"❌ API testing error: {e}")
    
    return api_results

async def main():
    """Main function with command line support"""
    parser = argparse.ArgumentParser(description='Fully Automated Website Extractor with API Implementation')
    parser.add_argument('url', nargs='?', default='https://www.dolaa789.cc/', help='Target website URL')
    parser.add_argument('--no-apis', action='store_true', help='Skip API testing')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🚀 FULLY AUTOMATED WEBSITE EXTRACTOR")
    print("="*80)
    print(f"Target URL: {args.url}")
    print("Features:")
    print("- Automated browser control with Selenium")
    print("- JavaScript injection to bypass CORS")
    print("- Complete asset extraction (HTML, CSS, JS, images, fonts)")
    print("- Modal and dynamic content triggering")
    print("- API implementation from gasv-desktop-frontend + svw38-frontend")
    print("- Automatic zip archive creation")
    print("="*80)
    
    # Extract website
    extractor = FullyAutomatedExtractor(args.url)
    success = await extractor.extract_website()
    
    if not success:
        print("❌ Website extraction failed")
        return
    
    # Test APIs if requested
    if not args.no_apis:
        print("\n🔌 Initializing API clients...")
        
        # Initialize API clients
        gasv_client = DolaAPIClient(site_code="gavn138")
        await gasv_client.init_session()
        
        svw38_client = DolaAPIClient(site_code="staging")
        await svw38_client.init_session()
        
        # Test APIs
        api_results = await test_apis(gasv_client, svw38_client)
        
        # Save API documentation
        api_docs = {
            "extraction_date": datetime.now().isoformat(),
            "target_url": args.url,
            "api_endpoints": {
                "gasv_base_url": gasv_client.base_url,
                "svw38_base_url": svw38_client.base_url,
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
                        "all_transactions": "/account/transactions"
                    },
                    "content": {
                        "banners": "/image-slider/list",
                        "banks": "/banks"
                    }
                }
            },
            "api_test_results": api_results
        }
        
        with open(os.path.join(extractor.output_dir, 'api_documentation.json'), 'w', encoding='utf-8') as f:
            json.dump(api_docs, f, indent=2, ensure_ascii=False)
        
        # Clean up
        await gasv_client.close()
        await svw38_client.close()
        
        print("✅ API documentation saved")
    
    print("\n🎉 FULLY AUTOMATED EXTRACTION COMPLETED!")
    print(f"\n📁 All files saved in: {extractor.output_dir}")
    print(f"📦 Zip archive: {extractor.output_dir}.zip")
    print("\n🚀 Usage for other websites:")
    print(f"python fully_automated_extractor.py https://example.com")

if __name__ == "__main__":
    print("Fully Automated Website Extractor")
    print("Required: pip install requests beautifulsoup4 aiohttp selenium")
    print("Make sure Chrome browser is installed")
    print()
    
    asyncio.run(main())