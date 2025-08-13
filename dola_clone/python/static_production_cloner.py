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

class StaticProductionCloner:
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

        # Static directory structure
        self.css_dir = self.output_dir / "css"
        self.js_dir = self.output_dir / "js"
        self.images_dir = self.output_dir / "images"
        self.fonts_dir = self.output_dir / "fonts"
        self.videos_dir = self.output_dir / "videos"

        # Asset tracking
        self.downloaded_assets = {}
        self.asset_mappings = {}
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
            "modals_found": 0,
            "forms_found": 0,
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
        """Inject comprehensive asset extraction and UI detection script"""
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
            
            // Extract images with better metadata
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
                    media: link.media || 'all',
                    integrity: link.integrity || '',
                    crossorigin: link.crossOrigin || ''
                });
            });
            
            // Extract scripts
            document.querySelectorAll('script[src]').forEach(script => {
                assets.scripts.push({
                    url: script.src,
                    type: script.type || 'text/javascript',
                    async: script.async,
                    defer: script.defer,
                    integrity: script.integrity || ''
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
                const fontRegex = /url\s*\(\s*['"]*([^'"\)]+\.(woff2?|ttf|otf|eot))['"]*\s*\)/gi;
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
            
            // Process inline styles for fonts
            assets.inline_styles.forEach(style => {
                extractFontsFromCSS(style.content, window.location.href);
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
        
        // Enhanced asset download with retry logic
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

    async def wait_for_dynamic_content(self, page):
        """Enhanced dynamic content loading"""
        print("⏳ Waiting for dynamic content...")

        # Wait for initial load
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(self.delay / 1000)

        # Enhanced scrolling for lazy loading
        scroll_positions = [0.25, 0.5, 0.75, 1.0]
        for position in scroll_positions:
            await page.evaluate(
                f"""
                window.scrollTo(0, document.body.scrollHeight * {position});
            """
            )
            await asyncio.sleep(1)

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0);")
        await asyncio.sleep(1)

        # Wait for any final network requests
        await page.wait_for_load_state("networkidle", timeout=10000)

        print("✅ Dynamic content loading completed")

    async def extract_and_download_assets(self, page):
        """Enhanced asset extraction with progress tracking"""
        print("🔍 Extracting assets...")

        # Get all assets
        assets = await page.evaluate("window.extractAllAssets()")

        total_assets = sum(
            len(asset_list)
            for asset_list in assets.values()
            if isinstance(asset_list, list)
        )
        downloaded_count = 0
        total_size = 0

        print(f"📊 Found {total_assets} assets to download")

        # Download each asset type
        for asset_type, asset_list in assets.items():
            if not asset_list or not isinstance(asset_list, list):
                continue

            print(f"📥 Downloading {len(asset_list)} {asset_type}...")

            for i, asset in enumerate(asset_list):
                try:
                    if asset_type == "inline_styles":
                        # Handle inline styles separately
                        await self.save_inline_style(asset, i)
                        downloaded_count += 1
                        continue

                    # Download asset
                    result = await page.evaluate(
                        "window.downloadAssetAsBase64(arguments[0])", asset["url"]
                    )

                    if result["success"]:
                        # Save asset
                        saved_path = await self.save_asset(
                            asset["url"],
                            result["data"],
                            asset_type,
                            result["contentType"],
                            asset,
                        )

                        if saved_path:
                            total_size += result["size"]
                            downloaded_count += 1
                            self.extraction_report["assets"][
                                self.get_asset_category(asset_type)
                            ] += 1

                            # Progress indicator
                            progress = (downloaded_count / total_assets) * 100
                            print(
                                f"  📦 {downloaded_count}/{total_assets} ({progress:.1f}%) - {os.path.basename(saved_path)}"
                            )
                    else:
                        print(f"  ❌ Failed: {asset['url']} - {result['error']}")

                except Exception as e:
                    print(f"  ❌ Error downloading {asset.get('url', 'unknown')}: {str(e)}")
                    continue

        self.extraction_report["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        print(f"✅ Downloaded {downloaded_count} assets ({self.extraction_report['total_size_mb']} MB)")

        return assets

    async def save_inline_style(self, style_data, index):
        """Save inline CSS to file"""
        try:
            filename = f"inline_style_{index}.css"
            file_path = self.css_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(style_data["content"])
            
            self.asset_mappings[f"inline_style_{index}"] = f"css/{filename}"
            return file_path
        except Exception as e:
            print(f"❌ Failed to save inline style {index}: {str(e)}")
            return None

    async def save_asset(
        self, url, base64_data, asset_type, content_type, asset_metadata=None
    ):
        """Save asset to appropriate directory"""
        try:
            # Determine file extension and directory
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            
            # Get file extension from URL or content type
            if "." in original_filename:
                file_ext = os.path.splitext(original_filename)[1]
            else:
                file_ext = self.get_extension_from_content_type(content_type)
                original_filename = f"asset_{hash(url) % 10000}{file_ext}"

            # Determine target directory
            if asset_type in ["stylesheets", "inline_styles"]:
                target_dir = self.css_dir
                category = "css"
            elif asset_type in ["scripts"]:
                target_dir = self.js_dir
                category = "js"
            elif asset_type in ["images", "background_images"]:
                target_dir = self.images_dir
                category = "images"
            elif asset_type in ["fonts"]:
                target_dir = self.fonts_dir
                category = "fonts"
            elif asset_type in ["videos"]:
                target_dir = self.videos_dir
                category = "videos"
            else:
                target_dir = self.output_dir
                category = "other"

            # Create unique filename if exists
            file_path = target_dir / original_filename
            counter = 1
            while file_path.exists():
                name, ext = os.path.splitext(original_filename)
                file_path = target_dir / f"{name}_{counter}{ext}"
                counter += 1

            # Decode and save file
            if base64_data.startswith("data:"):
                # Remove data URL prefix
                base64_content = base64_data.split(",", 1)[1]
                file_content = base64.b64decode(base64_content)
            else:
                file_content = base64.b64decode(base64_data)

            with open(file_path, "wb") as f:
                f.write(file_content)

            # Store mapping for HTML rewriting
            relative_path = f"{category}/{file_path.name}"
            self.asset_mappings[url] = relative_path
            self.downloaded_assets[url] = {
                "local_path": str(file_path),
                "relative_path": relative_path,
                "size": len(file_content),
                "content_type": content_type,
            }

            return file_path

        except Exception as e:
            print(f"❌ Failed to save asset {url}: {str(e)}")
            return None

    def get_extension_from_content_type(self, content_type):
        """Get file extension from content type"""
        content_type_map = {
            "text/css": ".css",
            "text/javascript": ".js",
            "application/javascript": ".js",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
            "font/woff": ".woff",
            "font/woff2": ".woff2",
            "font/ttf": ".ttf",
            "font/otf": ".otf",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
        }
        return content_type_map.get(content_type, ".bin")

    def get_asset_category(self, asset_type):
        """Map asset type to report category"""
        category_map = {
            "stylesheets": "css",
            "inline_styles": "css",
            "scripts": "js",
            "images": "images",
            "background_images": "images",
            "fonts": "fonts",
            "videos": "videos",
        }
        return category_map.get(asset_type, "other")

    def rewrite_asset_paths(self, html_content):
        """Rewrite asset paths in HTML to use local files"""
        print("🔄 Rewriting asset paths...")
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Update CSS links
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href and href in self.asset_mappings:
                link["href"] = self.asset_mappings[href]
        
        # Update script sources
        for script in soup.find_all("script", src=True):
            src = script.get("src")
            if src and src in self.asset_mappings:
                script["src"] = self.asset_mappings[src]
        
        # Update image sources
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src in self.asset_mappings:
                img["src"] = self.asset_mappings[src]
        
        # Replace inline styles with external CSS files
        inline_style_count = 0
        for style in soup.find_all("style"):
            if style.string and style.string.strip():
                # Replace with link to external CSS
                new_link = soup.new_tag("link", rel="stylesheet", href=f"css/inline_style_{inline_style_count}.css")
                style.replace_with(new_link)
                inline_style_count += 1
        
        # Update CSS content for background images
        for css_file in self.css_dir.glob("*.css"):
            try:
                with open(css_file, "r", encoding="utf-8") as f:
                    css_content = f.read()
                
                # Replace background image URLs
                for original_url, local_path in self.asset_mappings.items():
                    if original_url in css_content:
                        # Calculate relative path from CSS to images
                        if local_path.startswith("images/"):
                            relative_path = f"../{local_path}"
                            css_content = css_content.replace(original_url, relative_path)
                
                with open(css_file, "w", encoding="utf-8") as f:
                    f.write(css_content)
            except Exception as e:
                print(f"❌ Error updating CSS file {css_file}: {str(e)}")
        
        return str(soup)

    def create_extraction_report(self):
        """Create detailed extraction report"""
        report_path = self.output_dir / "extraction_report.json"
        
        self.extraction_report.update({
            "extraction_completed": datetime.now().isoformat(),
            "output_directory": str(self.output_dir),
            "total_files": len(self.downloaded_assets),
            "file_structure": {
                "index.html": "Main HTML file",
                "css/": "Stylesheets directory",
                "js/": "JavaScript files directory", 
                "images/": "Images directory",
                "fonts/": "Fonts directory",
                "videos/": "Videos directory (if any)"
            },
            "usage_instructions": {
                "how_to_use": "Open index.html in any web browser",
                "requirements": "No server required - works offline",
                "compatibility": "Works in all modern browsers"
            }
        })
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.extraction_report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Extraction report saved: {report_path}")

    def create_zip_archive(self):
        """Create zip archive of the static website"""
        zip_filename = f"{self.output_dir.name}.zip"
        zip_path = self.output_dir.parent / zip_filename
        
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)
        
        print(f"📦 Zip archive created: {zip_path}")
        return zip_path

    async def clone_website(self):
        """Main cloning process"""
        print(f"🚀 Starting static website cloning: {self.target_url}")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ],
            )
            
            try:
                # Setup directories
                await self.setup_directories()
                
                # Create browser context
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                
                page = await context.new_page()
                
                # Navigate to target URL
                print(f"🌐 Loading: {self.target_url}")
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
                index_path = self.output_dir / "index.html"
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(updated_html)
                
                print(f"💾 Main HTML saved: {index_path}")
                
                # Create extraction report
                self.create_extraction_report()
                
                # Create zip archive
                zip_path = self.create_zip_archive()
                
                print(f"\n🎉 Static website cloning completed successfully!")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📦 Zip archive: {zip_path}")
                print(f"📊 Summary:")
                print(f"   - CSS files: {self.extraction_report['assets']['css']}")
                print(f"   - JS files: {self.extraction_report['assets']['js']}")
                print(f"   - Images: {self.extraction_report['assets']['images']}")
                print(f"   - Fonts: {self.extraction_report['assets']['fonts']}")
                print(f"   - Total size: {self.extraction_report['total_size_mb']} MB")
                print(f"\n📖 Usage: Open {self.output_dir}/index.html in your browser")
                
                return True
                
            except Exception as e:
                print(f"❌ Cloning failed: {str(e)}")
                return False
            finally:
                await browser.close()

def main():
    parser = argparse.ArgumentParser(description="Static Production Website Cloner")
    parser.add_argument("url", help="Target website URL")
    parser.add_argument(
        "--output", "-o", 
        default=f"static_website_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Output directory name"
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        default=True,
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--delay", 
        type=int, 
        default=3000,
        help="Delay in milliseconds for dynamic content loading"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 STATIC PRODUCTION WEBSITE CLONER")
    print("=" * 80)
    print(f"Target URL: {args.url}")
    print(f"Output Directory: {args.output}")
    print("Features:")
    print("- Playwright for dynamic content extraction")
    print("- Complete asset downloading (CSS, JS, Images, Fonts)")
    print("- Automatic path rewriting for offline usage")
    print("- Static HTML/CSS/JS output (no React dependencies)")
    print("- Production-ready asset optimization")
    print("=" * 80)
    
    cloner = StaticProductionCloner(
        target_url=args.url,
        output_dir=args.output,
        headless=args.headless,
        delay=args.delay
    )
    
    try:
        success = asyncio.run(cloner.clone_website())
        if success:
            print("\n✅ Static website cloning completed successfully!")
            print("📁 You now have a complete static website with:")
            print("   - index.html (main file)")
            print("   - css/ (all stylesheets)")
            print("   - js/ (all JavaScript files)")
            print("   - images/ (all images)")
            print("   - fonts/ (all font files)")
            print("   - extraction_report.json (detailed report)")
            print("   - preview.png (screenshot)")
        else:
            print("\n❌ Static website cloning failed")
    except KeyboardInterrupt:
        print("\n⚠️ Cloning interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()