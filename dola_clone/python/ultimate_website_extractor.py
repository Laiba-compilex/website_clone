import os
import time
import json
import base64
import zipfile
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import argparse
from pathlib import Path
import re
from bs4 import BeautifulSoup

class WebsiteExtractor:
    def __init__(self, url, output_dir="extracted_website", headless=True):
        self.url = url
        self.output_dir = output_dir
        self.headless = headless
        self.driver = None
        self.extracted_data = {
            'html': '',
            'css': [],
            'js': [],
            'images': [],
            'fonts': [],
            'modals': [],
            'apis': {}
        }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/css", exist_ok=True)
        os.makedirs(f"{output_dir}/js", exist_ok=True)
        os.makedirs(f"{output_dir}/images", exist_ok=True)
        os.makedirs(f"{output_dir}/fonts", exist_ok=True)
        os.makedirs(f"{output_dir}/api_implementations", exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver with optimal settings"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

    def inject_js_for_extraction(self):
        """Inject JavaScript to extract images, modals, and background assets"""
        script = """
        window.extractedImages = [];
        window.imageExtractionComplete = false;
        
        async function extractAllImages() {
            const images = new Set();
            
            // Get images from img tags
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.startsWith('data:')) {
                    images.add(img.src);
                }
                if (img.dataset.src) {
                    images.add(img.dataset.src);
                }
                if (img.srcset) {
                    img.srcset.split(',').forEach(src => {
                        const url = src.trim().split(' ')[0];
                        if (url && !url.startsWith('data:')) {
                            images.add(url);
                        }
                    });
                }
            });
            
            // Get background images from CSS
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const bgImage = style.backgroundImage;
                if (bgImage && bgImage !== 'none') {
                    const matches = bgImage.match(/url\(['"]?([^"')]+)['"]?\)/g);
                    if (matches) {
                        matches.forEach(match => {
                            const url = match.replace(/url\(['"]?([^"')]+)['"]?\)/, '$1');
                            if (!url.startsWith('data:')) {
                                images.add(url);
                            }
                        });
                    }
                }
            });

            // Convert images to base64
            const imagePromises = Array.from(images).map(async (imageUrl) => {
                try {
                    const response = await fetch(imageUrl);
                    if (response.ok) {
                        const blob = await response.blob();
                        return new Promise((resolve) => {
                            const reader = new FileReader();
                            reader.onloadend = () => {
                                const base64 = reader.result.split(',')[1];
                                resolve({
                                    url: imageUrl,
                                    base64: base64,
                                    type: blob.type
                                });
                            };
                            reader.readAsDataURL(blob);
                        });
                    }
                } catch (error) {
                    console.log('Failed to fetch image:', imageUrl, error);
                    return null;
                }
            });

            const results = await Promise.allSettled(imagePromises);
            window.extractedImages = results
                .filter(result => result.status === 'fulfilled' && result.value)
                .map(result => result.value);
            
            window.imageExtractionComplete = true;
            return window.extractedImages;
        }
        
        extractAllImages();
        """
        self.driver.execute_script(script)

    def inject_js_for_modals(self):
        """Inject JavaScript to detect and trigger modals with enhanced close button handling"""
        script = """
        window.detectedModals = [];
        window.modalDetectionComplete = false;
        window.modalInteractionLog = [];
        
        function detectModals() {
            const modalSelectors = [
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '[class*="overlay"]',
                '[id*="modal"]',
                '[id*="popup"]',
                '[id*="dialog"]'
            ];
            
            const modals = [];
            
            modalSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(modal => {
                    if (!modals.find(m => m.element === modal)) {
                        modals.push({
                            element: modal,
                            id: modal.id || '',
                            className: modal.className || '',
                            innerHTML: modal.innerHTML,
                            isVisible: window.getComputedStyle(modal).display !== 'none'
                        });
                    }
                });
            });
            
            // Find modal triggers
            const triggers = [];
            document.querySelectorAll('[data-toggle], [data-target], [onclick*="modal"], [onclick*="popup"]').forEach(trigger => {
                triggers.push({
                    element: trigger,
                    attributes: {
                        'data-toggle': trigger.getAttribute('data-toggle'),
                        'data-target': trigger.getAttribute('data-target'),
                        'onclick': trigger.getAttribute('onclick')
                    },
                    text: trigger.textContent.trim()
                });
            });
            
            window.detectedModals = {
                modals: modals,
                triggers: triggers
            };
            
            window.modalDetectionComplete = true;
            return window.detectedModals;
        }
        
        // Enhanced modal interaction with better close button handling
        function triggerModalsWithCloseHandling() {
            const potentialTriggers = document.querySelectorAll(
                'button[class*="modal"], a[class*="modal"], [data-toggle="modal"], [onclick*="modal"], button[class*="login"], button[class*="register"]'
            );
            
            let triggerIndex = 0;
            
            function processNextTrigger() {
                if (triggerIndex >= potentialTriggers.length) {
                    window.modalInteractionLog.push('All modal triggers processed');
                    return;
                }
                
                const trigger = potentialTriggers[triggerIndex];
                window.modalInteractionLog.push(`Processing trigger ${triggerIndex}: ${trigger.textContent.trim()}`);
                
                try {
                    // Click the trigger
                    trigger.click();
                    window.modalInteractionLog.push(`Clicked trigger: ${trigger.textContent.trim()}`);
                    
                    // Wait for modal to appear and then close it
                    setTimeout(() => {
                        // Try multiple close button selectors
                        const closeSelectors = [
                            '.close',
                            '[data-dismiss="modal"]',
                            '.modal-close',
                            'button[class*="close"]',
                            '[aria-label="Close"]',
                            '.btn-close',
                            'button[type="button"][class*="close"]',
                            '.modal-header .close',
                            '.popup-close',
                            '.dialog-close',
                            'button[onclick*="close"]',
                            'span[class*="close"]',
                            '.fa-times',
                            '.fa-close',
                            'i[class*="close"]'
                        ];
                        
                        let closed = false;
                        
                        for (const selector of closeSelectors) {
                            const closeButtons = document.querySelectorAll(selector);
                            closeButtons.forEach(btn => {
                                if (btn.offsetParent !== null) { // Check if visible
                                    try {
                                        btn.click();
                                        window.modalInteractionLog.push(`Closed modal using selector: ${selector}`);
                                        closed = true;
                                    } catch (e) {
                                        window.modalInteractionLog.push(`Failed to click close button: ${e.message}`);
                                    }
                                }
                            });
                            if (closed) break;
                        }
                        
                        // If no close button worked, try ESC key
                        if (!closed) {
                            try {
                                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27 }));
                                window.modalInteractionLog.push('Attempted to close modal with ESC key');
                            } catch (e) {
                                window.modalInteractionLog.push(`ESC key failed: ${e.message}`);
                            }
                        }
                        
                        // Try clicking on overlay/backdrop
                        if (!closed) {
                            const overlays = document.querySelectorAll('.modal-backdrop, .overlay, .modal-overlay');
                            overlays.forEach(overlay => {
                                try {
                                    overlay.click();
                                    window.modalInteractionLog.push('Clicked on modal overlay to close');
                                } catch (e) {
                                    window.modalInteractionLog.push(`Overlay click failed: ${e.message}`);
                                }
                            });
                        }
                        
                        // Process next trigger
                        triggerIndex++;
                        setTimeout(processNextTrigger, 1000);
                    }, 2000); // Wait 2 seconds for modal to fully load
                    
                } catch (e) {
                    window.modalInteractionLog.push(`Failed to trigger modal: ${e.message}`);
                    triggerIndex++;
                    setTimeout(processNextTrigger, 500);
                }
            }
            
            // Start processing triggers
            processNextTrigger();
        }
        
        detectModals();
        triggerModalsWithCloseHandling();
        """
        self.driver.execute_script(script)

    def wait_for_extraction_complete(self, timeout=180):
        """Wait for the extraction to complete with extended timeout for modal interactions"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                image_complete = self.driver.execute_script("return window.imageExtractionComplete;")
                modal_complete = self.driver.execute_script("return window.modalDetectionComplete;")
                
                # Check modal interaction progress
                modal_log = self.driver.execute_script("return window.modalInteractionLog || [];")
                if modal_log:
                    print(f"Modal interaction progress: {len(modal_log)} actions completed")
                
                if image_complete and modal_complete:
                    # Wait a bit more for modal interactions to complete
                    time.sleep(10)
                    return True
                time.sleep(3)
            except WebDriverException:
                time.sleep(3)
        return False

    def get_extracted_data(self):
        """Get all extracted data including modal interaction logs"""
        try:
            self.extracted_data['html'] = self.driver.page_source
            images = self.driver.execute_script("return window.extractedImages || [];")
            self.extracted_data['images'] = images
            modals = self.driver.execute_script("return window.detectedModals || {};")
            self.extracted_data['modals'] = modals
            
            # Get modal interaction log
            modal_log = self.driver.execute_script("return window.modalInteractionLog || [];")
            self.extracted_data['modal_interactions'] = modal_log
            
            print(f"Extracted {len(images)} images and {len(modals.get('modals', []))} modals")
            print(f"Modal interactions: {len(modal_log)} actions performed")
            
            # Print modal interaction summary
            if modal_log:
                print("Modal interaction summary:")
                for log_entry in modal_log[-5:]:  # Show last 5 entries
                    print(f"  - {log_entry}")
                    
        except WebDriverException as e:
            print(f"Error getting extracted data: {e}")

    def download_images_from_console(self):
        """Save images from extracted data"""
        for i, image_data in enumerate(self.extracted_data['images']):
            try:
                image_bytes = base64.b64decode(image_data['base64'])
                ext = 'jpg'
                if 'png' in image_data['type']:
                    ext = 'png'
                elif 'gif' in image_data['type']:
                    ext = 'gif'
                elif 'webp' in image_data['type']:
                    ext = 'webp'
                
                url_path = urlparse(image_data['url']).path
                filename = os.path.basename(url_path) or f"image_{i}.{ext}"
                if not any(filename.endswith(e) for e in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    filename += f'.{ext}'

                filepath = os.path.join(self.output_dir, 'images', filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

                print(f"Saved image: {filename} ({len(image_bytes)} bytes)")
            except Exception as e:
                print(f"Failed to save image {i}: {e}")

    def download_assets(self):
        """Download all CSS, JS, and images"""
        soup = BeautifulSoup(self.extracted_data['html'], 'html.parser')
        
        # Download CSS
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            href = link.get('href')
            if href:
                css_url = urljoin(self.url, href)
                self.download_asset(css_url, 'css')
        
        # Download JS
        js_scripts = soup.find_all('script', src=True)
        for script in js_scripts:
            src = script.get('src')
            if src:
                js_url = urljoin(self.url, src)
                self.download_asset(js_url, 'js')

    def download_asset(self, url, asset_type):
        """Download an individual asset"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.url
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                filename = os.path.basename(urlparse(url).path)
                filepath = os.path.join(self.output_dir, asset_type, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                self.extracted_data[asset_type].append({'url': url, 'filename': filename})
                print(f"Downloaded {asset_type}: {filename}")
        except Exception as e:
            print(f"Failed to download {asset_type} {url}: {e}")

    def fix_asset_paths(self):
        """Fix asset paths in HTML to point to local files"""
        soup = BeautifulSoup(self.extracted_data['html'], 'html.parser')
        
        # Fix CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                filename = os.path.basename(urlparse(href).path)
                link['href'] = f'css/{filename}'
        
        # Fix JS scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                filename = os.path.basename(urlparse(src).path)
                script['src'] = f'js/{filename}'
        
        # Fix image sources
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith('data:'):
                filename = os.path.basename(urlparse(src).path)
                img['src'] = f'images/{filename}'
        
        self.extracted_data['html'] = str(soup)

    def save_html(self):
        """Save the modified HTML"""
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(self.extracted_data['html'])

    def create_extraction_report(self):
        """Create an extraction report with modal interaction details"""
        report = {
            'url': self.url,
            'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'assets': {
                'html_size': len(self.extracted_data['html']),
                'css_files': len(self.extracted_data['css']),
                'js_files': len(self.extracted_data['js']),
                'images': len(self.extracted_data['images']),
                'fonts': len(self.extracted_data['fonts'])
            },
            'modals': {
                'detected_modals': len(self.extracted_data['modals'].get('modals', [])),
                'modal_triggers': len(self.extracted_data['modals'].get('triggers', [])),
                'modal_interactions': len(self.extracted_data.get('modal_interactions', []))
            },
            'modal_interaction_log': self.extracted_data.get('modal_interactions', [])
        }

        with open(os.path.join(self.output_dir, 'extraction_report.json'), 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def create_zip_archive(self):
        """Create a zip archive of the extracted website"""
        zip_filename = f"{self.output_dir}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arc_name)

        print(f"Created zip archive: {zip_filename}")
        return zip_filename

    def extract_website(self):
        """Main extraction method with enhanced modal handling"""
        try:
            print(f"Starting extraction of {self.url}...")

            # Setup the driver and load the website
            self.setup_driver()
            self.driver.get(self.url)

            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(5)

            print("Injecting JavaScript for extraction...")
            self.inject_js_for_extraction()
            
            print("Injecting enhanced modal handling...")
            self.inject_js_for_modals()

            # Wait for the extraction to complete with extended timeout
            print("Waiting for extraction and modal interactions to complete...")
            if self.wait_for_extraction_complete():
                print("Extraction completed successfully.")
            else:
                print("Extraction timed out, proceeding with available data.")

            # Get the extracted data
            self.get_extracted_data()

            # Download images from console
            print("Downloading images from console...")
            self.download_images_from_console()

            # Download assets
            print("Downloading CSS and JS assets...")
            self.download_assets()

            # Fix asset paths
            self.fix_asset_paths()

            # Save HTML
            self.save_html()

            # Create extraction report
            report = self.create_extraction_report()

            # Create a zip archive of the extracted website
            self.create_zip_archive()

            print(f"Extraction complete. Output directory: {self.output_dir}")
            print(f"Modal interactions performed: {len(self.extracted_data.get('modal_interactions', []))}")
            return True
        except Exception as e:
            print(f"Extraction failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Ultimate Website Extractor with API Integration')
    parser.add_argument('url', help='URL of the website to extract')
    parser.add_argument('--output', '-o', default='extracted_website', help='Output directory')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')

    args = parser.parse_args()

    extractor = WebsiteExtractor(
        url=args.url,
        output_dir=args.output,
        headless=args.headless
    )

    success = extractor.extract_website()

    if success:
        print("\nExtraction completed successfully!")
    else:
        print("\nExtraction failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
