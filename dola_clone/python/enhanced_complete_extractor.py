import os
import json
import zipfile
import asyncio
import aiohttp
import aiofiles
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path
import time
from datetime import datetime

class EnhancedWebsiteExtractor:
    def __init__(self, base_url, output_dir="extracted_website"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = None
        self.driver = None
        self.extracted_data = {
            'html': '',
            'css_files': [],
            'js_files': [],
            'images': [],
            'fonts': [],
            'external_assets': []
        }
        
    async def setup_session(self):
        """Setup aiohttp session"""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def close_driver(self):
        """Close Chrome driver"""
        if self.driver:
            self.driver.quit()
            
    async def download_asset(self, url, filepath):
        """Download asset with error handling"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(content)
                    return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
        return False
        
    def extract_external_images_from_css(self, css_content, css_url):
        """Extract external image URLs from CSS content"""
        image_urls = []
        # Find all url() references in CSS
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if match.startswith('http'):
                image_urls.append(match)
            elif match.startswith('//'):
                image_urls.append('https:' + match)
            elif match.startswith('/'):
                base_domain = f"{urlparse(css_url).scheme}://{urlparse(css_url).netloc}"
                image_urls.append(base_domain + match)
            else:
                image_urls.append(urljoin(css_url, match))
                
        return image_urls
        
    async def inject_enhanced_extraction_script(self):
        """Inject comprehensive extraction script with modal handling"""
        script = """
        // Initialize extraction data
        window.extractedData = {
            html: '',
            css: [],
            js: [],
            images: [],
            fonts: [],
            modals: [],
            modalTriggers: []
        };
        
        // Enhanced asset conversion
        async function fetchAssetAsBase64(url) {
            try {
                const response = await fetch(url, { mode: 'cors' });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const blob = await response.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
            } catch (error) {
                console.warn('Failed to fetch asset:', url, error);
                return null;
            }
        }
        
        // Extract all images including background images
        async function extractAllImages() {
            const images = new Set();
            
            // Regular img tags
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.startsWith('data:')) {
                    images.add(img.src);
                }
            });
            
            // Background images from computed styles
            document.querySelectorAll('*').forEach(element => {
                const style = window.getComputedStyle(element);
                const bgImage = style.backgroundImage;
                if (bgImage && bgImage !== 'none') {
                    const matches = bgImage.match(/url\(["']?([^"')]+)["']?\)/g);
                    if (matches) {
                        matches.forEach(match => {
                            const url = match.replace(/url\(["']?([^"')]+)["']?\)/, '$1');
                            if (!url.startsWith('data:')) {
                                images.add(url);
                            }
                        });
                    }
                }
            });
            
            // Convert to base64
            const imagePromises = Array.from(images).slice(0, 200).map(async (url) => {
                const base64 = await fetchAssetAsBase64(url);
                if (base64) {
                    const filename = url.split('/').pop().split('?')[0] || 'image.jpg';
                    return { url, filename, data: base64 };
                }
                return null;
            });
            
            const results = await Promise.allSettled(imagePromises);
            return results
                .filter(result => result.status === 'fulfilled' && result.value)
                .map(result => result.value);
        }
        
        // Enhanced modal detection and activation
        function detectAndActivateModals() {
            const modalSelectors = [
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '[class*="overlay"]',
                '[id*="modal"]',
                '[id*="popup"]'
            ];
            
            const triggerSelectors = [
                'button[data-toggle="modal"]',
                '[data-target*="modal"]',
                '.login',
                '.signup',
                '.register',
                '.btn-login',
                '.btn-register',
                '.header-btn',
                '[class*="login"]',
                '[class*="register"]'
            ];
            
            // Find modals
            modalSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(modal => {
                    if (modal.offsetParent === null || window.getComputedStyle(modal).display === 'none') {
                        window.extractedData.modals.push({
                            selector: selector,
                            id: modal.id || '',
                            className: modal.className || '',
                            hidden: true
                        });
                    }
                });
            });
            
            // Find and click triggers
            triggerSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(trigger => {
                    window.extractedData.modalTriggers.push({
                        selector: selector,
                        text: trigger.textContent?.trim() || '',
                        id: trigger.id || '',
                        className: trigger.className || ''
                    });
                    
                    // Try to activate modal
                    try {
                        trigger.click();
                        setTimeout(() => {
                            // Check if modal appeared
                            modalSelectors.forEach(modalSelector => {
                                document.querySelectorAll(modalSelector).forEach(modal => {
                                    if (modal.offsetParent !== null && window.getComputedStyle(modal).display !== 'none') {
                                        modal.style.display = 'block';
                                        modal.style.visibility = 'visible';
                                        modal.style.opacity = '1';
                                    }
                                });
                            });
                        }, 500);
                    } catch (e) {
                        console.warn('Failed to click trigger:', e);
                    }
                });
            });
        }
        
        // Main extraction function
        async function extractEverything() {
            try {
                // Get HTML
                window.extractedData.html = document.documentElement.outerHTML;
                
                // Extract CSS
                document.querySelectorAll('link[rel="stylesheet"], style').forEach(element => {
                    if (element.tagName === 'LINK') {
                        window.extractedData.css.push({
                            url: element.href,
                            type: 'external'
                        });
                    } else {
                        window.extractedData.css.push({
                            content: element.textContent,
                            type: 'inline'
                        });
                    }
                });
                
                // Extract JS
                document.querySelectorAll('script').forEach(script => {
                    if (script.src) {
                        window.extractedData.js.push({
                            url: script.src,
                            type: 'external'
                        });
                    } else if (script.textContent.trim()) {
                        window.extractedData.js.push({
                            content: script.textContent,
                            type: 'inline'
                        });
                    }
                });
                
                // Detect and activate modals
                detectAndActivateModals();
                
                // Wait for modals to appear
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Extract images
                window.extractedData.images = await extractAllImages();
                
                return window.extractedData;
            } catch (error) {
                console.error('Extraction error:', error);
                return window.extractedData;
            }
        }
        
        // Execute extraction
        return extractEverything();
        """
        
        return self.driver.execute_async_script(f"""
        const callback = arguments[arguments.length - 1];
        ({script}).then(callback).catch(callback);
        """, script=script)
        
    async def process_extracted_data(self, data):
        """Process and save extracted data"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save HTML
        html_path = os.path.join(self.output_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(data.get('html', ''))
        
        # Process CSS files
        css_dir = os.path.join(self.output_dir, 'css')
        os.makedirs(css_dir, exist_ok=True)
        
        css_tasks = []
        for i, css_item in enumerate(data.get('css', [])):
            if css_item.get('type') == 'external' and css_item.get('url'):
                filename = f"style_{i}.css"
                filepath = os.path.join(css_dir, filename)
                css_tasks.append(self.download_asset(css_item['url'], filepath))
                self.extracted_data['css_files'].append(filename)
            elif css_item.get('type') == 'inline':
                filename = f"inline_{i}.css"
                filepath = os.path.join(css_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(css_item.get('content', ''))
                self.extracted_data['css_files'].append(filename)
        
        # Process JS files
        js_dir = os.path.join(self.output_dir, 'js')
        os.makedirs(js_dir, exist_ok=True)
        
        js_tasks = []
        for i, js_item in enumerate(data.get('js', [])):
            if js_item.get('type') == 'external' and js_item.get('url'):
                filename = f"script_{i}.js"
                filepath = os.path.join(js_dir, filename)
                js_tasks.append(self.download_asset(js_item['url'], filepath))
                self.extracted_data['js_files'].append(filename)
            elif js_item.get('type') == 'inline':
                filename = f"inline_{i}.js"
                filepath = os.path.join(js_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(js_item.get('content', ''))
                self.extracted_data['js_files'].append(filename)
        
        # Process images
        images_dir = os.path.join(self.output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        for image_data in data.get('images', []):
            if image_data and image_data.get('data'):
                filename = image_data.get('filename', 'image.jpg')
                filepath = os.path.join(images_dir, filename)
                
                # Convert base64 to file
                try:
                    import base64
                    base64_data = image_data['data'].split(',')[1]
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(base64_data))
                    self.extracted_data['images'].append(filename)
                except Exception as e:
                    print(f"Failed to save image {filename}: {e}")
        
        # Execute download tasks
        if css_tasks:
            await asyncio.gather(*css_tasks, return_exceptions=True)
        if js_tasks:
            await asyncio.gather(*js_tasks, return_exceptions=True)
            
    def fix_asset_paths(self):
        """Fix asset paths in HTML and CSS files"""
        html_path = os.path.join(self.output_dir, 'index.html')
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Fix CSS links
            html_content = re.sub(
                r'<link[^>]*href=["\']([^"\'>]+\.css)["\'][^>]*>',
                lambda m: m.group(0).replace(m.group(1), f'css/{os.path.basename(m.group(1))}'),
                html_content
            )
            
            # Fix JS links
            html_content = re.sub(
                r'<script[^>]*src=["\']([^"\'>]+\.js)["\'][^>]*>',
                lambda m: m.group(0).replace(m.group(1), f'js/{os.path.basename(m.group(1))}'),
                html_content
            )
            
            # Fix image sources
            html_content = re.sub(
                r'src=["\']https?://[^"\'>]+/([^/"\'>]+\.(jpg|jpeg|png|gif|webp|svg))["\']',
                r'src="images/\1"',
                html_content,
                flags=re.IGNORECASE
            )
            
            # Fix background images in style attributes
            html_content = re.sub(
                r'background-image:\s*url\(["\']?https?://[^"\'>)]+/([^/"\'>)]+\.(jpg|jpeg|png|gif|webp|svg))["\']?\)',
                r'background-image: url("images/\1.\2")',
                html_content,
                flags=re.IGNORECASE
            )
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
    def add_modal_functionality(self):
        """Add JavaScript to make modals functional"""
        modal_js = """
        // Enhanced Modal Functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Login modal functionality
            const loginBtns = document.querySelectorAll('.login, .btn-login, .header-btn.login');
            const signupBtns = document.querySelectorAll('.signup, .btn-signup, .header-btn.signup, .register');
            
            // Create login modal if it doesn't exist
            if (!document.querySelector('#loginModal')) {
                const loginModal = document.createElement('div');
                loginModal.id = 'loginModal';
                loginModal.className = 'modal';
                loginModal.innerHTML = `
                    <div class="modal-content">
                        <span class="close">&times;</span>
                        <h2>Đăng nhập</h2>
                        <form>
                            <input type="text" placeholder="Tên đăng nhập" required>
                            <input type="password" placeholder="Mật khẩu" required>
                            <button type="submit">Đăng nhập</button>
                        </form>
                    </div>
                `;
                document.body.appendChild(loginModal);
            }
            
            // Create signup modal if it doesn't exist
            if (!document.querySelector('#signupModal')) {
                const signupModal = document.createElement('div');
                signupModal.id = 'signupModal';
                signupModal.className = 'modal';
                signupModal.innerHTML = `
                    <div class="modal-content">
                        <span class="close">&times;</span>
                        <h2>Đăng ký</h2>
                        <form>
                            <input type="text" placeholder="Tên đăng nhập" required>
                            <input type="email" placeholder="Email" required>
                            <input type="password" placeholder="Mật khẩu" required>
                            <input type="password" placeholder="Xác nhận mật khẩu" required>
                            <button type="submit">Đăng ký</button>
                        </form>
                    </div>
                `;
                document.body.appendChild(signupModal);
            }
            
            // Add modal styles
            const modalStyles = document.createElement('style');
            modalStyles.textContent = `
                .modal {
                    display: none;
                    position: fixed;
                    z-index: 10000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.5);
                }
                .modal-content {
                    background-color: #fefefe;
                    margin: 15% auto;
                    padding: 20px;
                    border: 1px solid #888;
                    width: 300px;
                    border-radius: 5px;
                }
                .close {
                    color: #aaa;
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                }
                .close:hover { color: black; }
                .modal form input {
                    width: 100%;
                    padding: 10px;
                    margin: 5px 0;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                .modal form button {
                    width: 100%;
                    padding: 10px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }
            `;
            document.head.appendChild(modalStyles);
            
            // Event listeners
            loginBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    document.getElementById('loginModal').style.display = 'block';
                });
            });
            
            signupBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    document.getElementById('signupModal').style.display = 'block';
                });
            });
            
            // Close modals
            document.querySelectorAll('.close').forEach(closeBtn => {
                closeBtn.addEventListener('click', function() {
                    this.closest('.modal').style.display = 'none';
                });
            });
            
            // Close modal when clicking outside
            window.addEventListener('click', function(event) {
                if (event.target.classList.contains('modal')) {
                    event.target.style.display = 'none';
                }
            });
        });
        """
        
        js_dir = os.path.join(self.output_dir, 'js')
        os.makedirs(js_dir, exist_ok=True)
        
        modal_js_path = os.path.join(js_dir, 'modal-functionality.js')
        with open(modal_js_path, 'w', encoding='utf-8') as f:
            f.write(modal_js)
            
        # Add script tag to HTML
        html_path = os.path.join(self.output_dir, 'index.html')
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add modal script before closing body tag
            html_content = html_content.replace(
                '</body>',
                '<script src="js/modal-functionality.js"></script></body>'
            )
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
    def create_extraction_report(self, modal_data):
        """Create detailed extraction report"""
        report = {
            'extraction_time': datetime.now().isoformat(),
            'source_url': self.base_url,
            'extracted_files': {
                'html': 1,
                'css_files': len(self.extracted_data['css_files']),
                'js_files': len(self.extracted_data['js_files']),
                'images': len(self.extracted_data['images']),
                'fonts': len(self.extracted_data['fonts'])
            },
            'modals': {
                'detected': len(modal_data.get('modals', [])),
                'triggers_found': len(modal_data.get('modalTriggers', [])),
                'functional': True
            },
            'status': 'completed'
        }
        
        report_path = os.path.join(self.output_dir, 'extraction_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
    def create_zip_archive(self):
        """Create zip archive of extracted website"""
        zip_path = f"{self.output_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arc_path)
        return zip_path
        
    async def extract_website(self):
        """Main extraction method"""
        try:
            await self.setup_session()
            self.setup_driver()
            
            print(f"Loading website: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            time.sleep(5)
            
            print("Injecting extraction script...")
            extracted_data = await self.inject_enhanced_extraction_script()
            
            print("Processing extracted data...")
            await self.process_extracted_data(extracted_data)
            
            print("Fixing asset paths...")
            self.fix_asset_paths()
            
            print("Adding modal functionality...")
            self.add_modal_functionality()
            
            print("Creating extraction report...")
            self.create_extraction_report(extracted_data)
            
            print("Creating zip archive...")
            zip_path = self.create_zip_archive()
            
            print(f"\n✅ Extraction completed successfully!")
            print(f"📁 Output directory: {self.output_dir}")
            print(f"📦 Zip archive: {zip_path}")
            print(f"🖼️ Images extracted: {len(self.extracted_data['images'])}")
            print(f"🎨 CSS files: {len(self.extracted_data['css_files'])}")
            print(f"📜 JS files: {len(self.extracted_data['js_files'])}")
            print(f"🔧 Modals: Functional")
            
            return True
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return False
        finally:
            await self.close_session()
            self.close_driver()

# Usage
async def main():
    extractor = EnhancedWebsiteExtractor(
        base_url="https://dola789cc.co",
        output_dir="extracted_dolaa_complete"
    )
    
    success = await extractor.extract_website()
    if success:
        print("\n🎉 Website extraction completed with full functionality!")
    else:
        print("\n❌ Extraction failed. Please check the logs.")

if __name__ == "__main__":
    asyncio.run(main())