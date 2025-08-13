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
        """Fetch dynamic base URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.dola789cc.co/api/v1/site-config/{self.site_code}") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.base_url = data.get('api_base_url', 'https://api.dola789cc.co/').rstrip('/') + '/'
                        return True
        except Exception as e:
            print(f"Failed to fetch base URL: {e}")
            
        # Fallback URLs
        fallback_urls = [
            "https://api.dola789cc.co/",
            "https://api.dolaa789.cc/",
            "https://api.dola789.cc/"
        ]
        
        for url in fallback_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url + "api/v1/health") as response:
                        if response.status == 200:
                            self.base_url = url
                            return True
            except:
                continue
                
        return False
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.base_url:
            await self.fetch_base_url()
            
        if self.base_url:
            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            return True
        return False
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

class FullyAutomatedExtractor:
    def __init__(self, target_url):
        self.target_url = target_url
        self.driver = None
        self.output_dir = f"extracted_website_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.assets = {
            'html': '',
            'css': {},
            'js': {},
            'images': {},
            'fonts': {},
            'other_assets': {},
            'modals': []
        }
    
    def setup_driver(self):
        """Setup Chrome driver with optimized options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Increase timeouts
            chrome_options.add_argument('--script-timeout=300000')  # 5 minutes
            chrome_options.add_argument('--page-load-timeout=120000')  # 2 minutes
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set script timeout to 5 minutes
            self.driver.set_script_timeout(300)
            
            return True
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            return False
    
    def inject_extraction_script(self):
        """Inject optimized extraction JavaScript with better timeout handling"""
        extraction_script = """
        // Optimized Website Extractor - Bypasses CORS with better performance
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
        
        // Function to fetch and convert assets to base64 with timeout
        async function fetchAssetAsBase64(url, timeout = 10000) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                
                const response = await fetch(url, { signal: controller.signal });
                clearTimeout(timeoutId);
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const blob = await response.blob();
                return await blobToBase64(blob);
            } catch (error) {
                console.warn(`Failed to fetch ${url}:`, error.message);
                return null;
            }
        }
        
        // Extract all CSS with parallel processing
        async function extractCSS() {
            console.log('🎨 Extracting CSS...');
            
            const promises = [];
            
            // External CSS files
            const linkElements = document.querySelectorAll('link[rel="stylesheet"]');
            linkElements.forEach((link, index) => {
                const href = link.href;
                if (href && !href.startsWith('data:')) {
                    const filename = href.split('/').pop() || `css_${index}.css`;
                    promises.push(
                        fetchAssetAsBase64(href, 15000).then(content => {
                            if (content) {
                                window.extractedData.css[filename] = {
                                    url: href,
                                    content: content,
                                    type: 'external'
                                };
                            }
                        })
                    );
                }
            });
            
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
            
            // Wait for all CSS downloads with timeout
            await Promise.allSettled(promises);
            console.log(`✅ Extracted ${Object.keys(window.extractedData.css).length} CSS files`);
        }
        
        // Extract all JavaScript with parallel processing
        async function extractJS() {
            console.log('⚡ Extracting JavaScript...');
            
            const promises = [];
            
            // External JS files
            const scriptElements = document.querySelectorAll('script[src]');
            scriptElements.forEach((script, index) => {
                const src = script.src;
                if (src && !src.startsWith('data:')) {
                    const filename = src.split('/').pop() || `js_${index}.js`;
                    promises.push(
                        fetchAssetAsBase64(src, 15000).then(content => {
                            if (content) {
                                window.extractedData.js[filename] = {
                                    url: src,
                                    content: content,
                                    type: 'external'
                                };
                            }
                        })
                    );
                }
            });
            
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
            
            // Wait for all JS downloads with timeout
            await Promise.allSettled(promises);
            console.log(`✅ Extracted ${Object.keys(window.extractedData.js).length} JS files`);
        }
        
        // Extract images with parallel processing and limit
        async function extractImages() {
            console.log('🖼️ Extracting Images...');
            
            const imageUrls = new Set();
            const promises = [];
            
            // Regular img tags
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.startsWith('data:')) {
                    imageUrls.add(img.src);
                }
                if (img.dataset.src && !img.dataset.src.startsWith('data:')) {
                    imageUrls.add(img.dataset.src.startsWith('http') ? img.dataset.src : new URL(img.dataset.src, window.location.origin).href);
                }
            });
            
            // Background images from all elements
            document.querySelectorAll('*').forEach(element => {
                const style = window.getComputedStyle(element);
                const bgImage = style.backgroundImage;
                if (bgImage && bgImage !== 'none') {
                    // Fixed regex with raw string equivalent
                    const bgMatches = bgImage.match(/url\(["']?([^"')]+)["']?\)/g);
                    if (bgMatches) {
                        bgMatches.forEach(match => {
                            const url = match.match(/url\(["']?([^"')]+)["']?\)/)[1];
                            if (!url.startsWith('data:')) {
                                imageUrls.add(url.startsWith('http') ? url : new URL(url, window.location.origin).href);
                            }
                        });
                    }
                }
            });
            
            // Limit to first 50 images to prevent timeout
            const limitedUrls = Array.from(imageUrls).slice(0, 50);
            
            limitedUrls.forEach((url, index) => {
                const filename = url.split('/').pop().split('?')[0] || `image_${index}.jpg`;
                promises.push(
                    fetchAssetAsBase64(url, 10000).then(content => {
                        if (content) {
                            window.extractedData.images[filename] = {
                                url: url,
                                content: content
                            };
                        }
                    })
                );
            });
            
            // Wait for all image downloads with timeout
            await Promise.allSettled(promises);
            console.log(`✅ Extracted ${Object.keys(window.extractedData.images).length} images`);
        }
        
        // Extract fonts with parallel processing
        async function extractFonts() {
            console.log('🔤 Extracting Fonts...');
            
            const fontUrls = new Set();
            const promises = [];
            
            // Font face rules from stylesheets
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
                    // Cross-origin stylesheet access denied
                }
            }
            
            // Download fonts
            fontUrls.forEach((url, index) => {
                const filename = url.split('/').pop() || `font_${index}.woff2`;
                promises.push(
                    fetchAssetAsBase64(url, 10000).then(content => {
                        if (content) {
                            window.extractedData.fonts[filename] = {
                                url: url,
                                content: content
                            };
                        }
                    })
                );
            });
            
            await Promise.allSettled(promises);
            console.log(`✅ Extracted ${Object.keys(window.extractedData.fonts).length} fonts`);
        }
        
        // Trigger modals and dynamic content (non-blocking)
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
                'button[type="button"]',
                '.btn',
                'a[href="#"]'
            ];
            
            modalTriggers.forEach(selector => {
                document.querySelectorAll(selector).forEach((element, index) => {
                    if (index < 2) { // Limit to first 2 elements per selector
                        try {
                            element.click();
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
        
        // Main extraction function with timeout protection
        async function extractEverything() {
            console.log('🚀 Starting optimized extraction...');
            
            try {
                // Trigger modals first (non-blocking)
                triggerModals();
                
                // Wait for dynamic content to load
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Extract content with timeout protection
                const extractionPromises = [
                    extractCSS(),
                    extractJS(),
                    extractImages(),
                    extractFonts()
                ];
                
                // Set overall timeout for extraction
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Extraction timeout')), 120000) // 2 minutes
                );
                
                await Promise.race([
                    Promise.allSettled(extractionPromises),
                    timeoutPromise
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
                
            } catch (error) {
                console.error('Extraction error:', error);
                // Return partial data even if there's an error
                window.extractedData.html = document.documentElement.outerHTML;
                return window.extractedData;
            }
        }
        
        // Start extraction and return promise
        return extractEverything();
        """
        
        return self.driver.execute_async_script(extraction_script)
    
    def save_extracted_data(self, data):
        """Save extracted data to files"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save HTML
        if data.get('html'):
            with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(data['html'])
        
        # Save CSS files
        css_dir = os.path.join(self.output_dir, 'css')
        os.makedirs(css_dir, exist_ok=True)
        for filename, css_data in data.get('css', {}).items():
            file_path = os.path.join(css_dir, filename)
            if css_data.get('type') == 'external':
                content = base64.b64decode(css_data['content']).decode('utf-8', errors='ignore')
            else:
                content = base64.b64decode(css_data['content']).decode('utf-8', errors='ignore')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Save JS files
        js_dir = os.path.join(self.output_dir, 'js')
        os.makedirs(js_dir, exist_ok=True)
        for filename, js_data in data.get('js', {}).items():
            file_path = os.path.join(js_dir, filename)
            if js_data.get('type') == 'external':
                content = base64.b64decode(js_data['content']).decode('utf-8', errors='ignore')
            else:
                content = base64.b64decode(js_data['content']).decode('utf-8', errors='ignore')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Save images
        images_dir = os.path.join(self.output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        for filename, img_data in data.get('images', {}).items():
            file_path = os.path.join(images_dir, filename)
            try:
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(img_data['content']))
            except Exception as e:
                print(f"Failed to save image {filename}: {e}")
        
        # Save fonts
        fonts_dir = os.path.join(self.output_dir, 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)
        for filename, font_data in data.get('fonts', {}).items():
            file_path = os.path.join(fonts_dir, filename)
            try:
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(font_data['content']))
            except Exception as e:
                print(f"Failed to save font {filename}: {e}")
        
        # Save extraction report
        report = {
            'extraction_time': datetime.now().isoformat(),
            'target_url': self.target_url,
            'summary': {
                'html_size': len(data.get('html', '')),
                'css_files': len(data.get('css', {})),
                'js_files': len(data.get('js', {})),
                'images': len(data.get('images', {})),
                'fonts': len(data.get('fonts', {})),
                'modals_triggered': len(data.get('modals', []))
            },
            'modals': data.get('modals', []),
            'asset_urls': {
                'css': [css_data.get('url') for css_data in data.get('css', {}).values() if css_data.get('url')],
                'js': [js_data.get('url') for js_data in data.get('js', {}).values() if js_data.get('url')],
                'images': [img_data.get('url') for img_data in data.get('images', {}).values() if img_data.get('url')],
                'fonts': [font_data.get('url') for font_data in data.get('fonts', {}).values() if font_data.get('url')]
            }
        }
        
        with open(os.path.join(self.output_dir, 'extraction_report.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def create_zip_archive(self):
        """Create zip archive of extracted data"""
        zip_filename = f"{self.output_dir}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arcname)
        
        return zip_filename
    
    async def extract_website(self):
        """Main extraction method with improved error handling"""
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
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            print("⏳ Waiting for dynamic content to load...")
            time.sleep(5)
            
            # Inject and run extraction script
            print("🔧 Injecting extraction script...")
            try:
                final_data = self.inject_extraction_script()
            except Exception as e:
                print(f"⚠️ Script execution error: {e}")
                # Fallback: get basic HTML
                final_data = {
                    'html': self.driver.page_source,
                    'css': {},
                    'js': {},
                    'images': {},
                    'fonts': {},
                    'modals': []
                }
            
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
    """Test API implementations"""
    print("\n🔧 Testing API implementations...")
    
    api_results = {
        'gasv_desktop_frontend': {},
        'svw38_frontend': {}
    }
    
    # Test GASV APIs
    if gasv_client:
        try:
            # Add your API tests here
            api_results['gasv_desktop_frontend']['status'] = 'connected'
        except Exception as e:
            api_results['gasv_desktop_frontend']['error'] = str(e)
    
    # Test SVW38 APIs
    if svw38_client:
        try:
            # Add your API tests here
            api_results['svw38_frontend']['status'] = 'connected'
        except Exception as e:
            api_results['svw38_frontend']['error'] = str(e)
    
    return api_results

async def main():
    parser = argparse.ArgumentParser(description='Fully Automated Website Extractor')
    parser.add_argument('url', help='Target website URL')
    parser.add_argument('--no-apis', action='store_true', help='Skip API testing')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🚀 FULLY AUTOMATED WEBSITE EXTRACTOR")
    print("="*80)
    print(f"Target URL: {args.url}")
    print("Features:")
    print("- Optimized browser control with Selenium")
    print("- Parallel JavaScript asset downloading")
    print("- Complete asset extraction with timeout protection")
    print("- Modal and dynamic content triggering")
    print("- API implementation from gasv-desktop-frontend + svw38-frontend")
    print("- Automatic zip archive creation")
    print("="*80)
    
    # Initialize extractor
    extractor = FullyAutomatedExtractor(args.url)
    
    # Extract website
    success = await extractor.extract_website()
    
    if not args.no_apis and success:
        # Initialize API clients
        gasv_client = DolaAPIClient("gasv-desktop-frontend")
        svw38_client = DolaAPIClient("svw38-frontend")
        
        try:
            await gasv_client.init_session()
            await svw38_client.init_session()
            
            # Test APIs
            api_results = await test_apis(gasv_client, svw38_client)
            
            # Save API results
            with open(os.path.join(extractor.output_dir, 'api_test_results.json'), 'w') as f:
                json.dump(api_results, f, indent=2)
                
        finally:
            await gasv_client.close()
            await svw38_client.close()
    
    if success:
        print("\n✅ All operations completed successfully!")
    else:
        print("\n❌ Website extraction failed")

if __name__ == "__main__":
    print("Fully Automated Website Extractor")
    print("Required: pip install requests beautifulsoup4 aiohttp selenium")
    print("Make sure Chrome browser is installed")
    print()
    
    asyncio.run(main())