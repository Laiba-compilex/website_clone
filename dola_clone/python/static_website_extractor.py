import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import zipfile
from datetime import datetime
import argparse
import re

class StaticWebsiteExtractor:
    def __init__(self, target_url):
        self.target_url = target_url
        self.output_dir = f"static_website_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def setup_driver(self):
        """Setup minimal Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(60)
            return True
        except Exception as e:
            print(f"Failed to setup Chrome driver: {e}")
            return False
    
    def get_page_html(self):
        """Get the fully rendered HTML using Selenium"""
        try:
            print(f"🌐 Loading website: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            print("⏳ Waiting for dynamic content...")
            time.sleep(5)
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Get the final HTML
            html = self.driver.page_source
            return html
            
        except Exception as e:
            print(f"Error getting HTML: {e}")
            return None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()
    
    def download_asset(self, url, asset_type="unknown"):
        """Download a single asset with error handling"""
        try:
            # Make URL absolute
            if not url.startswith('http'):
                url = urljoin(self.target_url, url)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            print(f"Failed to download {asset_type} {url}: {e}")
            return None
    
    def extract_and_download_assets(self, html):
        """Extract and download all assets from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        assets = {
            'css': {},
            'js': {},
            'images': {},
            'fonts': {}
        }
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        for asset_type in assets.keys():
            os.makedirs(os.path.join(self.output_dir, asset_type), exist_ok=True)
        
        # Extract CSS files
        print("🎨 Extracting CSS files...")
        css_links = soup.find_all('link', rel='stylesheet')
        for i, link in enumerate(css_links):
            href = link.get('href')
            if href:
                content = self.download_asset(href, 'CSS')
                if content:
                    filename = os.path.basename(urlparse(href).path) or f'style_{i}.css'
                    filepath = os.path.join(self.output_dir, 'css', filename)
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    assets['css'][filename] = href
                    # Update HTML to use local path
                    link['href'] = f'css/{filename}'
        
        # Extract inline CSS
        style_tags = soup.find_all('style')
        for i, style in enumerate(style_tags):
            if style.string:
                filename = f'inline_{i}.css'
                filepath = os.path.join(self.output_dir, 'css', filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(style.string)
                assets['css'][filename] = 'inline'
                # Replace inline style with link to external file
                new_link = soup.new_tag('link', rel='stylesheet', href=f'css/{filename}')
                style.replace_with(new_link)
        
        # Extract JavaScript files
        print("⚡ Extracting JavaScript files...")
        js_scripts = soup.find_all('script', src=True)
        for i, script in enumerate(js_scripts):
            src = script.get('src')
            if src:
                content = self.download_asset(src, 'JS')
                if content:
                    filename = os.path.basename(urlparse(src).path) or f'script_{i}.js'
                    filepath = os.path.join(self.output_dir, 'js', filename)
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    assets['js'][filename] = src
                    # Update HTML to use local path
                    script['src'] = f'js/{filename}'
        
        # Extract inline JavaScript
        inline_scripts = soup.find_all('script', src=False)
        for i, script in enumerate(inline_scripts):
            if script.string and script.string.strip():
                filename = f'inline_{i}.js'
                filepath = os.path.join(self.output_dir, 'js', filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(script.string)
                assets['js'][filename] = 'inline'
                # Replace inline script with external file reference
                script.string = ''
                script['src'] = f'js/{filename}'
        
        # Extract images
        print("🖼️ Extracting images...")
        img_tags = soup.find_all('img')
        for i, img in enumerate(img_tags):
            src = img.get('src') or img.get('data-src')
            if src and not src.startswith('data:'):
                content = self.download_asset(src, 'Image')
                if content:
                    filename = os.path.basename(urlparse(src).path) or f'image_{i}.jpg'
                    # Ensure filename has extension
                    if '.' not in filename:
                        filename += '.jpg'
                    filepath = os.path.join(self.output_dir, 'images', filename)
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    assets['images'][filename] = src
                    # Update HTML to use local path
                    img['src'] = f'images/{filename}'
        
        # Extract background images from CSS
        print("🎨 Extracting background images from CSS...")
        for css_file in os.listdir(os.path.join(self.output_dir, 'css')):
            css_path = os.path.join(self.output_dir, 'css', css_file)
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                # Find background image URLs
                bg_urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css_content)
                
                for bg_url in bg_urls:
                    if not bg_url.startswith('data:') and any(ext in bg_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                        content = self.download_asset(bg_url, 'Background Image')
                        if content:
                            filename = os.path.basename(urlparse(bg_url).path)
                            if filename and '.' in filename:
                                filepath = os.path.join(self.output_dir, 'images', filename)
                                with open(filepath, 'wb') as f:
                                    f.write(content)
                                assets['images'][filename] = bg_url
                                # Update CSS to use local path
                                css_content = css_content.replace(bg_url, f'../images/{filename}')
                
                # Save updated CSS
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(css_content)
                    
            except Exception as e:
                print(f"Error processing CSS file {css_file}: {e}")
        
        # Extract fonts
        print("🔤 Extracting fonts...")
        font_links = soup.find_all('link', href=True)
        for link in font_links:
            href = link.get('href')
            if href and any(ext in href.lower() for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']):
                content = self.download_asset(href, 'Font')
                if content:
                    filename = os.path.basename(urlparse(href).path)
                    if filename:
                        filepath = os.path.join(self.output_dir, 'fonts', filename)
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        assets['fonts'][filename] = href
                        # Update HTML to use local path
                        link['href'] = f'fonts/{filename}'
        
        return soup, assets
    
    def save_html(self, soup):
        """Save the updated HTML"""
        # Clean up the HTML
        html_content = str(soup)
        
        # Add responsive meta tags if not present
        if 'viewport' not in html_content:
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            html_content = html_content.replace('<head>', f'<head>\n    {viewport_meta}')
        
        html_path = os.path.join(self.output_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_report(self, assets):
        """Create extraction report"""
        report = {
            'extraction_time': datetime.now().isoformat(),
            'target_url': self.target_url,
            'output_directory': self.output_dir,
            'summary': {
                'css_files': len(assets['css']),
                'js_files': len(assets['js']),
                'images': len(assets['images']),
                'fonts': len(assets['fonts'])
            },
            'assets': assets,
            'instructions': {
                'usage': 'Open index.html in a web browser to view the website',
                'structure': {
                    'index.html': 'Main HTML file',
                    'css/': 'Stylesheets directory',
                    'js/': 'JavaScript files directory',
                    'images/': 'Images directory',
                    'fonts/': 'Fonts directory'
                }
            }
        }
        
        report_path = os.path.join(self.output_dir, 'extraction_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def create_zip(self):
        """Create zip archive"""
        zip_filename = f"{self.output_dir}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arcname)
        return zip_filename
    
    def extract(self):
        """Main extraction method"""
        print("🚀 Starting static website extraction...")
        
        # Setup driver
        if not self.setup_driver():
            return False
        
        try:
            # Get HTML
            html = self.get_page_html()
            if not html:
                print("❌ Failed to get HTML")
                return False
            
            # Extract and download assets
            soup, assets = self.extract_and_download_assets(html)
            
            # Save updated HTML
            self.save_html(soup)
            
            # Create report
            self.create_report(assets)
            
            # Create zip
            zip_file = self.create_zip()
            
            print(f"\n🎉 Extraction completed successfully!")
            print(f"📁 Output directory: {self.output_dir}")
            print(f"📦 Zip archive: {zip_file}")
            print(f"📊 Summary:")
            print(f"   - CSS files: {len(assets['css'])}")
            print(f"   - JS files: {len(assets['js'])}")
            print(f"   - Images: {len(assets['images'])}")
            print(f"   - Fonts: {len(assets['fonts'])}")
            print(f"\n📖 Usage: Open {self.output_dir}/index.html in your browser")
            
            return True
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Static Website Extractor')
    parser.add_argument('url', help='Target website URL')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 STATIC WEBSITE EXTRACTOR")
    print("="*60)
    print(f"Target URL: {args.url}")
    print("Features:")
    print("- Selenium for dynamic content")
    print("- Complete asset extraction (CSS, JS, Images, Fonts)")
    print("- Automatic path fixing")
    print("- Standalone HTML/CSS/JS output")
    print("- No React dependencies")
    print("="*60)
    
    extractor = StaticWebsiteExtractor(args.url)
    success = extractor.extract()
    
    if success:
        print("\n✅ Website extraction completed successfully!")
        print("📁 You now have a complete static website with:")
        print("   - index.html (main file)")
        print("   - css/ (stylesheets)")
        print("   - js/ (JavaScript files)")
        print("   - images/ (all images)")
        print("   - fonts/ (font files)")
    else:
        print("\n❌ Website extraction failed")

if __name__ == "__main__":
    print("Static Website Extractor")
    print("Required: pip install requests beautifulsoup4 selenium")
    print("Make sure Chrome browser is installed")
    print()
    
    main()