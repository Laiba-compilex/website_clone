import asyncio
import os
import json
import re
import base64
import argparse
import shutil
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
import zipfile
from dotenv import load_dotenv

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
from PIL import Image
import io

# Load environment variables
load_dotenv()

class MergedStaticCloner:
    def __init__(
        self,
        target_url,
        output_dir="static_website",
        headless=True,
        delay=3000,
        depth=1,
    ):
        self.target_url = target_url
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.delay = delay
        self.depth = depth
        self.crawled_urls = set()

        # Directory structure for static website
        self.css_dir = self.output_dir / "css"
        self.js_dir = self.output_dir / "js"
        self.images_dir = self.output_dir / "images"
        self.fonts_dir = self.output_dir / "fonts"
        self.videos_dir = self.output_dir / "videos"

        # Asset tracking
        self.downloaded_assets = {}
        self.asset_mappings = {}
        
        # Content collectors for merging
        self.merged_css_content = []
        self.merged_js_content = []
        
        self.extraction_report = {
            "url": target_url,
            "timestamp": datetime.now().isoformat(),
            "pages_crawled": [],
            "assets": {
                "images": 0,
                "css": 0,
                "js": 0,
                "fonts": 0,
                "videos": 0,
                "other": 0,
            },
            "total_size_mb": 0,
        }

    async def setup_directories(self):
        """Create static website directory structure"""
        directories = [
            self.output_dir,
            self.css_dir,
            self.js_dir,
            self.images_dir,
            self.fonts_dir,
            self.videos_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        print(f"✅ Created static website structure in {self.output_dir}")

    async def inject_enhanced_extraction_script(self, page):
        """Inject comprehensive asset extraction script"""
        extraction_script = r"""
        window.extractAllAssets = function() {
            const assets = {
                images: [],
                stylesheets: [],
                scripts: [],
                fonts: [],
                videos: [],
                other: [],
                inline_styles: [],
                background_images: []
            };
            
            // Extract images
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.startsWith('data:')) {
                    assets.images.push({
                        url: img.src,
                        alt: img.alt || '',
                        width: img.naturalWidth || img.width,
                        height: img.naturalHeight || img.height,
                        element: 'img',
                        classes: img.className,
                        loading: img.loading || 'eager'
                    });
                }
            });
            
            // Extract stylesheets
            document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                assets.stylesheets.push({
                    url: link.href,
                    media: link.media || 'all'
                });
            });
            
            // Extract scripts
            document.querySelectorAll('script[src]').forEach(script => {
                assets.scripts.push({
                    url: script.src,
                    type: script.type || 'text/javascript',
                    async: script.async,
                    defer: script.defer
                });
            });
            
            // Extract inline styles
            document.querySelectorAll('style').forEach(style => {
                if (style.textContent.trim()) {
                    assets.inline_styles.push({
                        content: style.textContent,
                        media: style.media || 'all'
                    });
                }
            });
            
            // Extract fonts from CSS
            const extractFontsFromCSS = (cssText, baseUrl) => {
                const fontRegex = /url\s*\(\s*['"]?([^'"\)]+\.(woff2?|ttf|otf|eot))['"]?\s*\)/gi;
                let match;
                while ((match = fontRegex.exec(cssText)) !== null) {
                    try {
                        const fontUrl = new URL(match[1], baseUrl).href;
                        assets.fonts.push({url: fontUrl, format: match[2]});
                    } catch (e) {}
                }
            };
            
            // Process stylesheets for fonts
            Array.from(document.styleSheets).forEach(sheet => {
                try {
                    Array.from(sheet.cssRules || sheet.rules).forEach(rule => {
                        if (rule.cssText) {
                            extractFontsFromCSS(rule.cssText, sheet.href || window.location.href);
                        }
                    });
                } catch (e) {}
            });
            
            // Extract background images
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.backgroundImage && style.backgroundImage !== 'none') {
                    const matches = style.backgroundImage.match(/url\s*\(\s*['"]?([^'"\)]+)['"]?\s*\)/g);
                    if (matches) {
                        matches.forEach(match => {
                            const urlMatch = match.match(/url\s*\(\s*['"]?([^'"\)]+)['"]?\s*\)/);
                            if (urlMatch) {
                                try {
                                    const url = new URL(urlMatch[1], window.location.href).href;
                                    assets.background_images.push({
                                        url: url,
                                        element: el.tagName.toLowerCase(),
                                        classes: el.className,
                                        id: el.id
                                    });
                                } catch (e) {}
                            }
                        });
                    }
                }
            });
            
            // Extract videos and audio
            document.querySelectorAll('video, audio, source').forEach(media => {
                if (media.src) {
                    assets.videos.push({
                        url: media.src,
                        type: media.type || '',
                        element: media.tagName.toLowerCase()
                    });
                }
            });
            
            // Remove duplicates
            Object.keys(assets).forEach(key => {
                if (Array.isArray(assets[key])) {
                    const seen = new Set();
                    assets[key] = assets[key].filter(item => {
                        const url = item.url || item.content;
                        if (seen.has(url)) return false;
                        seen.add(url);
                        return true;
                    });
                }
            });
            
            return assets;
        };
        
        window.downloadAssetAsBase64 = async function(url, retries = 3) {
            for (let i = 0; i < retries; i++) {
                try {
                    const response = await fetch(url, {
                        mode: 'cors',
                        credentials: 'omit'
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const blob = await response.blob();
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve({
                            success: true,
                            data: reader.result,
                            contentType: blob.type,
                            size: blob.size,
                            url: url
                        });
                        reader.onerror = () => resolve({
                            success: false,
                            error: 'FileReader error',
                            url: url
                        });
                        reader.readAsDataURL(blob);
                    });
                } catch (error) {
                    if (i === retries - 1) {
                        return {success: false, error: error.message, url: url};
                    }
                    await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
                }
            }
        };
        """

        await page.evaluate(extraction_script)
        print("✅ Enhanced extraction script injected")

    async def wait_for_dynamic_content(self, page):
        """Wait for dynamic content to load"""
        print("⏳ Waiting for dynamic content...")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(self.delay / 1000)
        
        # Scroll to trigger lazy loading
        scroll_positions = [0.25, 0.5, 0.75, 1.0]
        for position in scroll_positions:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {position});")
            await asyncio.sleep(1)
        
        await page.evaluate("window.scrollTo(0, 0);")
        await asyncio.sleep(1)
        await page.wait_for_load_state("networkidle", timeout=10000)
        print("✅ Dynamic content loading completed")

    async def extract_and_download_assets(self, page):
        """Extract and download assets, merging CSS and JS"""
        print("🔍 Extracting assets...")
        assets = await page.evaluate("window.extractAllAssets()")

        # --- Start of edit ---
        if 'scripts' in assets and assets['scripts']:
            print(f"   ℹ️  Found {len(assets['scripts'])} script tags to process.")
        else:
            print("   ⚠️  Warning: No script tags found on the page.")
        # --- End of edit ---

        total_assets = sum(len(asset_list) for asset_list in assets.values() if isinstance(asset_list, list))
        downloaded_count = 0
        
        print(f"📊 Found {total_assets} assets to download")
        
        # Process each asset type
        for asset_type, asset_list in assets.items():
            if not asset_list or not isinstance(asset_list, list):
                continue
                
            print(f"📥 Processing {len(asset_list)} {asset_type}...")
            
            for asset in asset_list:
                try:
                    if asset_type == "inline_styles":
                        # Add inline styles to merged CSS
                        self.merged_css_content.append(f"/* Inline Style */\n{asset['content']}\n")
                        self.extraction_report["assets"]["css"] += 1
                        continue
                    
                    if not asset.get('url'):
                        continue
                    
                    # Download asset - FIXED: Use proper function call syntax
                    result = await page.evaluate("""
                        (url) => window.downloadAssetAsBase64(url)
                    """, asset['url'])
                    
                    if result['success']:
                        await self.save_asset_merged(result, asset_type, asset)
                        downloaded_count += 1
                        
                        if downloaded_count % 10 == 0:
                            print(f"   📥 Downloaded {downloaded_count}/{total_assets} assets")
                    else:
                        # --- Start of edit ---
                        print(f"   ❌ Failed to download {asset['url']}: {result.get('error', 'Unknown error')}")
                        if asset_type == 'scripts':
                            print(f"   └── Script download failed. This may cause issues with website functionality.")
                        # --- End of edit ---
                        
                except Exception as e:
                    print(f"   ❌ Error processing {asset.get('url', 'unknown')}: {str(e)}")
                    continue
        
        # Save merged files
        await self.save_merged_files()
        
        print(f"✅ Asset extraction completed: {downloaded_count}/{total_assets} downloaded")
        return assets

    async def save_asset_merged(self, result, asset_type, asset_metadata):
        """Save asset with merging logic for CSS and JS"""
        try:
            # Decode base64 data
            base64_data = result['data'].split(',')[1]
            file_data = base64.b64decode(base64_data)
            
            # Determine file type and handle merging
            if asset_type in ['stylesheets'] or 'css' in result.get('contentType', '').lower():
                # Add CSS content to merged collection
                css_content = file_data.decode('utf-8', errors='ignore')
                self.merged_css_content.append(f"/* {result['url']} */\n{css_content}\n")
                self.extraction_report["assets"]["css"] += 1
                
            elif asset_type in ['scripts'] or 'javascript' in result.get('contentType', '').lower():
                # Add JS content to merged collection
                js_content = file_data.decode('utf-8', errors='ignore')
                self.merged_js_content.append(f"/* {result['url']} */\n{js_content}\n")
                self.extraction_report["assets"]["js"] += 1
                
            else:
                # Save other assets normally
                await self.save_individual_asset(result, asset_type, file_data)
                
        except Exception as e:
            print(f"   ❌ Error saving asset {result['url']}: {str(e)}")

    async def save_individual_asset(self, result, asset_type, file_data):
        """Save individual non-CSS/JS assets"""
        try:
            # Determine file extension and directory
            parsed_url = urlparse(result['url'])
            filename = os.path.basename(parsed_url.path) or 'asset'
            
            # Clean filename
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            
            # Determine save directory
            if any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']):
                save_dir = self.images_dir
                self.extraction_report["assets"]["images"] += 1
            elif any(ext in filename.lower() for ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']):
                save_dir = self.fonts_dir
                self.extraction_report["assets"]["fonts"] += 1
            elif any(ext in filename.lower() for ext in ['.mp4', '.webm', '.ogg', '.avi']):
                save_dir = self.videos_dir
                self.extraction_report["assets"]["videos"] += 1
            else:
                save_dir = self.output_dir
                self.extraction_report["assets"]["other"] += 1
            
            # Handle duplicates
            counter = 1
            original_filename = filename
            while (save_dir / filename).exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1
            
            # Save file
            file_path = save_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Track asset mapping
            self.asset_mappings[result['url']] = str(file_path.relative_to(self.output_dir))
            
        except Exception as e:
            print(f"   ❌ Error saving individual asset: {str(e)}")

    async def save_merged_files(self):
        """Save merged CSS and JS files"""
        try:
            # Save merged CSS
            if self.merged_css_content:
                css_path = self.css_dir / "index.css"
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.merged_css_content))
                print(f"✅ Merged CSS saved: {css_path}")
            
            # Save merged JS
            if self.merged_js_content:
                js_path = self.js_dir / "index.js"
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.merged_js_content))
                print(f"✅ Merged JS saved: {js_path}")
            # --- Start of edit ---
            else:
                print("   ⚠️  Warning: No JavaScript content was collected to merge. The 'js/index.js' file will not be created.")
            # --- End of edit ---
                
        except Exception as e:
            print(f"❌ Error saving merged files: {str(e)}")

    def rewrite_asset_paths(self, html_content):
        """Rewrite asset paths to use merged files and local assets"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Replace all CSS links with single merged CSS
        for link in soup.find_all('link', rel='stylesheet'):
            link.decompose()
        
        # Replace all script tags with single merged JS
        for script in soup.find_all('script', src=True):
            script.decompose()
        
        # Add merged CSS link
        if self.merged_css_content:
            head = soup.find('head')
            if head:
                css_link = soup.new_tag('link', rel='stylesheet', href='css/index.css')
                head.append(css_link)
        
        # Add merged JS script
        if self.merged_js_content:
            body = soup.find('body')
            if body:
                js_script = soup.new_tag('script', src='js/index.js')
                body.append(js_script)
        
        # Update image paths
        for img in soup.find_all('img', src=True):
            original_src = img['src']
            if original_src in self.asset_mappings:
                img['src'] = self.asset_mappings[original_src]
        
        # Update background images in style attributes
        for element in soup.find_all(style=True):
            style = element['style']
            for original_url, local_path in self.asset_mappings.items():
                if original_url in style:
                    style = style.replace(original_url, local_path)
            element['style'] = style
        
        return str(soup)

    async def capture_screenshot(self, page, filename="preview.png"):
        """Capture screenshot of the page"""
        try:
            screenshot_path = self.output_dir / filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"❌ Failed to capture screenshot: {str(e)}")
            return None

    def create_extraction_report(self):
        """Create extraction report"""
        report_path = self.output_dir / "extraction_report.json"
        
        # Calculate total size
        total_size = 0
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        self.extraction_report["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Extraction report saved: {report_path}")
        return report_path

    def create_zip_archive(self):
        """Create zip archive of extracted website"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"merged_website_{timestamp}.zip"
        zip_path = self.output_dir.parent / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)
        
        print(f"📦 Archive created: {zip_path}")
        return zip_path

    async def clone_website(self):
        """Main cloning process"""
        print(f"🚀 Starting website cloning: {self.target_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            try:
                await self.setup_directories()
                
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Navigate to target URL
                print(f"🌐 Loading page: {self.target_url}")
                await page.goto(self.target_url, wait_until="networkidle", timeout=60000)
                
                # Inject extraction scripts
                await self.inject_enhanced_extraction_script(page)
                
                # Wait for dynamic content
                await self.wait_for_dynamic_content(page)
                
                # Capture screenshot
                await self.capture_screenshot(page)
                
                # Extract and download assets
                await self.extract_and_download_assets(page)
                
                # Get final HTML
                html_content = await page.content()
                
                # Rewrite asset paths
                updated_html = self.rewrite_asset_paths(html_content)
                
                # Save main HTML file
                html_path = self.output_dir / "index.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(updated_html)
                
                print(f"💾 Main HTML saved: {html_path}")
                
                # Create reports and archive
                report_path = self.create_extraction_report()
                zip_path = self.create_zip_archive()
                
                print(f"\n✅ Website cloning completed successfully!")
                print(f"   • Output directory: {self.output_dir}")
                print(f"   • Pages crawled: {len(self.extraction_report['pages_crawled'])}")
                print(f"   • Total assets: {sum(self.extraction_report['assets'].values())}")
                print(f"   • Project size: {self.extraction_report['total_size_mb']} MB")
                print(f"   • Merged CSS: {'✅' if self.merged_css_content else '❌'}")
                print(f"   • Merged JS: {'✅' if self.merged_js_content else '❌'}")
                
                return {
                    "success": True,
                    "output_dir": str(self.output_dir),
                    "zip_path": str(zip_path),
                    "report_path": str(report_path),
                    "stats": self.extraction_report,
                }
                
            except Exception as e:
                print(f"❌ Error during cloning: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "output_dir": str(self.output_dir),
                }
                
            finally:
                await browser.close()

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Merged Static Website Cloner - Clone websites with merged CSS and JS files"
    )
    
    parser.add_argument("--url", required=True, help="Target website URL to clone")
    parser.add_argument("--output", default="merged_website", help="Output directory name")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--delay", type=int, default=3000, help="Delay for dynamic content loading")
    
    args = parser.parse_args()
    
    if not args.url.startswith(("http://", "https://")):
        print("❌ Error: URL must start with http:// or https://")
        return 1
    
    # Create output directory
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"⚠️  Directory '{output_path}' already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("❌ Operation cancelled")
            return 1
        shutil.rmtree(output_path)
    
    # Create cloner instance
    cloner = MergedStaticCloner(
        target_url=args.url,
        output_dir=args.output,
        headless=args.headless,
        delay=args.delay,
    )
    
    # Run the cloning process
    try:
        result = asyncio.run(cloner.clone_website())
        
        if result["success"]:
            print(f"\n🚀 Next steps:")
            print(f"   1. Open {result['output_dir']}/index.html in your browser")
            print(f"   2. All CSS is merged into css/index.css")
            print(f"   3. All JS is merged into js/index.js")
            return 0
        else:
            print(f"\n❌ Cloning failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())