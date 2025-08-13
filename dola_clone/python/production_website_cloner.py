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


class ProductionWebsiteCloner:
    def __init__(
        self,
        target_url,
        output_dir="cloned_website",
        headless=True,
        delay=3000,
        depth=1,
        inject_apis=True,
    ):
        self.target_url = target_url
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.delay = delay
        self.depth = depth
        self.inject_apis = inject_apis
        self.crawled_urls = set()

        # Directory structure
        self.assets_dir = self.output_dir / "src" / "assets"
        self.components_dir = self.output_dir / "src" / "components"
        self.api_dir = self.output_dir / "src" / "api"
        self.helpers_dir = self.output_dir / "src" / "helpers"
        self.pages_dir = self.output_dir / "src" / "pages"
        self.layout_dir = self.output_dir / "src" / "layout"
        self.public_dir = self.output_dir / "public"
        self.src_dir = self.output_dir / "src"

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
            "components_detected": [],
            "apis_integrated": [],
            "modals_found": 0,
            "forms_found": 0,
            "total_size_mb": 0,
        }

        # API integration mappings from your existing projects
        self.api_base_url = os.getenv("API_BASE_URL", "https://bo.gavn138.com/api")
        self.api_mappings = {
            "login": "/login_user",
            "register": "/register_user",
            "forgot_password": "/forgot-password",
            "contact": "/contact",
            "newsletter": "/newsletter/subscribe",
            "deposit": "/account/deposit",
            "withdraw": "/account/withdraw",
            "transactions": "/account/user_transaction",
            "announcements": "/announcements",
            "notifications": "/notifications",
            "banks": "/bank/company_banks",
            "events_track": "/events/track",
            "check_phone": "/check_phone_exist",
            "user_info": "/user",
        }

    async def setup_directories(self):
        """Create React project structure"""
        directories = [
            self.output_dir,
            self.public_dir,
            self.assets_dir / "images",
            self.assets_dir / "css",
            self.assets_dir / "js",
            self.assets_dir / "fonts",
            self.assets_dir / "icons",
            self.assets_dir / "videos",
            self.components_dir / "UI",
            self.components_dir / "Forms",
            self.components_dir / "Modals",
            self.api_dir,
            self.helpers_dir / "APIs",
            self.helpers_dir / "Context",
            self.helpers_dir / "Utils",
            self.pages_dir / "Auth",
            self.pages_dir / "User",
            self.pages_dir / "FooterPages",
            self.layout_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        print(f"✅ Created React project structure in {self.output_dir}")

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
            
            // Extract fonts from CSS with better detection
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
            
            // Extract background images with element context
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
        
        window.detectUIPatterns = function() {
    let patterns = {
        modals: [],
        forms: [],
        banners: [],
        navigation: [],
        buttons: [], // Ensure this is always present
        inputs: []
    };
    
    try {
        // Detect modals with better selectors
        const modalSelectors = [
            '[class*="modal"]', '[id*="modal"]', '.popup', '.dialog',
            '[role="dialog"]', '[aria-modal="true"]', '.overlay',
            '[class*="popup"]', '[class*="dialog"]'
        ];

        modalSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(modal => {
                const style = window.getComputedStyle(modal);
                patterns.modals.push({
                    element: modal.tagName,
                    classes: modal.className,
                    id: modal.id,
                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                    zIndex: style.zIndex,
                    position: style.position
                });
            });
        });

        // Enhanced form detection
        document.querySelectorAll('form').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            const buttons = form.querySelectorAll('button, input[type="submit"]');
            
            const formData = {
                action: form.action,
                method: form.method || 'GET',
                id: form.id,
                classes: form.className,
                inputs: Array.from(inputs).map(input => input ? {
                    type: input.type,
                    name: input.name,
                    placeholder: input.placeholder,
                    required: input.required,
                    id: input.id,
                    classes: input.className
                } : {}),
                buttons: Array.from(buttons).map(btn => btn ? {
                    type: btn.type,
                    text: btn.textContent?.trim() || btn.value,
                    classes: btn.className
                } : {})
            };

            patterns.forms.push(formData);
        });

        // Detect banners and sliders
        const bannerSelectors = [
            '[class*="banner"]', '[class*="slider"]', '[class*="carousel"]',
            '[class*="hero"]', '[class*="swiper"]', '[id*="banner"]',
            '[id*="slider"]', '[id*="carousel"]'
        ];

        bannerSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(banner => {
                patterns.banners.push({
                    element: banner.tagName,
                    classes: banner.className,
                    id: banner.id,
                    images: Array.from(banner.querySelectorAll('img')).map(img => img.src)
                });
            });
        });

        // Detect navigation
        document.querySelectorAll('nav, [role="navigation"], .navbar, .menu').forEach(nav => {
            const links = nav.querySelectorAll('a');
            patterns.navigation.push({
                element: nav.tagName,
                classes: nav.className,
                id: nav.id,
                links: Array.from(links).map(link => ({
                    href: link.href,
                    text: link.textContent?.trim(),
                    classes: link.className
                }))
            });
        });

    } catch (e) {
        console.error("Error in detectUIPatterns: ", e);
    }
    
    return patterns;
};

        
        // Get internal links for crawling
        window.getInternalLinks = function() {
            const currentDomain = window.location.hostname;
            const links = new Set();
            
            document.querySelectorAll('a[href]').forEach(link => {
                try {
                    const url = new URL(link.href, window.location.href);
                    if (url.hostname === currentDomain && 
                        !url.hash && 
                        !link.href.includes('mailto:') && 
                        !link.href.includes('tel:')) {
                        links.add(url.href);
                    }
                } catch (e) {}
            });
            
            return Array.from(links);
        };
        """

        await page.evaluate(extraction_script)
        print("✅ Enhanced extraction script injected")

    async def capture_screenshot(self, page, filename="preview.png"):
        """Capture screenshot of the page"""
        try:
            screenshot_path = self.public_dir / filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"❌ Failed to capture screenshot: {str(e)}")
            return None

    async def wait_for_dynamic_content(self, page):
        """Enhanced dynamic content loading with better modal handling"""
        print("⏳ Waiting for dynamic content...")

        # Wait for initial load
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(self.delay / 1000)

        # Try to trigger modals and dynamic content
        modal_triggers = [
            'button[data-toggle="modal"]',
            'a[data-toggle="modal"]',
            ".modal-trigger",
            '[onclick*="modal"]',
            'button:has-text("Login")',
            'button:has-text("Register")',
            'button:has-text("Sign up")',
            'button:has-text("Sign in")',
            ".login-btn",
            ".register-btn",
            ".auth-btn",
            '[data-bs-toggle="modal"]',
        ]

        for selector in modal_triggers:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements[:2]:  # Limit to avoid spam
                    try:
                        # Check if element is visible
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue

                        await element.click(timeout=2000)
                        await asyncio.sleep(1)

                        # Try to close modal with multiple strategies
                        close_selectors = [
                            ".modal .close",
                            ".modal-close",
                            '[data-dismiss="modal"]',
                            ".close-btn",
                            ".btn-close",
                            '[aria-label="Close"]',
                            ".modal-backdrop",
                            '[data-bs-dismiss="modal"]',
                        ]

                        modal_closed = False
                        for close_sel in close_selectors:
                            try:
                                close_btn = await page.query_selector(close_sel)
                                if close_btn and await close_btn.is_visible():
                                    await close_btn.click(timeout=1000)
                                    modal_closed = True
                                    break
                            except:
                                continue

                        # Try ESC key if modal not closed
                        if not modal_closed:
                            await page.keyboard.press("Escape")

                        await asyncio.sleep(0.5)
                    except Exception as e:
                        continue
            except:
                continue

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
                        continue

                    url = asset["url"] if isinstance(asset, dict) else asset
                    if not url or url.startswith("data:") or url.startswith("blob:"):
                        continue

                    # Skip if already downloaded
                    if url in self.downloaded_assets:
                        continue

                    # Download using browser context
                    result = await page.evaluate(
                        f"window.downloadAssetAsBase64('{url}')"
                    )

                    if result.get("success"):
                        # Save the asset
                        await self.save_asset(
                            url,
                            result["data"],
                            asset_type,
                            result.get("contentType", ""),
                            asset,
                        )
                        self.extraction_report["assets"][
                            (
                                asset_type
                                if asset_type in self.extraction_report["assets"]
                                else "other"
                            )
                        ] += 1
                        total_size += result.get("size", 0)
                        downloaded_count += 1

                        # Progress indicator
                        if downloaded_count % 10 == 0:
                            print(
                                f"  📈 Progress: {downloaded_count}/{total_assets} assets downloaded"
                            )
                    else:
                        print(
                            f"  ⚠️ Failed to download: {url} - {result.get('error', 'Unknown error')}"
                        )

                except Exception as e:
                    print(f"❌ Error downloading {url}: {str(e)}")
                    continue

        self.extraction_report["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        print(
            f"✅ Asset extraction completed: {downloaded_count}/{total_assets} assets, {self.extraction_report['total_size_mb']} MB"
        )

    async def save_inline_style(self, style_data, index):
        """Save inline styles as separate CSS files"""
        try:
            filename = f"inline-styles-{index}.css"
            file_path = self.assets_dir / "css" / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(style_data["content"])

            relative_path = f"./assets/css/{filename}"
            self.asset_mappings[f"inline-style-{index}"] = relative_path

        except Exception as e:
            print(f"❌ Failed to save inline style: {str(e)}")

    async def save_asset(
        self, url, base64_data, asset_type, content_type, asset_metadata=None
    ):
        """Enhanced asset saving with better file naming"""
        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            filename = (
                os.path.basename(parsed_url.path)
                or f"asset_{len(self.downloaded_assets)}"
            )

            # Clean filename
            filename = re.sub(r"[^\w\-_\.]", "_", filename)

            # Determine file extension from content type if missing
            if not os.path.splitext(filename)[1]:
                if "image" in content_type:
                    if "png" in content_type:
                        ext = ".png"
                    elif "jpeg" in content_type or "jpg" in content_type:
                        ext = ".jpg"
                    elif "gif" in content_type:
                        ext = ".gif"
                    elif "svg" in content_type:
                        ext = ".svg"
                    elif "webp" in content_type:
                        ext = ".webp"
                    else:
                        ext = ".png"
                elif "css" in content_type:
                    ext = ".css"
                elif "javascript" in content_type:
                    ext = ".js"
                elif "font" in content_type:
                    if "woff2" in content_type:
                        ext = ".woff2"
                    elif "woff" in content_type:
                        ext = ".woff"
                    elif "ttf" in content_type:
                        ext = ".ttf"
                    elif "otf" in content_type:
                        ext = ".otf"
                    else:
                        ext = ".woff2"
                elif "video" in content_type:
                    ext = ".mp4"
                elif "audio" in content_type:
                    ext = ".mp3"
                else:
                    ext = ".bin"
                filename += ext

            # Determine save directory
            if asset_type in ["images", "background_images"]:
                save_dir = self.assets_dir / "images"
            elif asset_type == "stylesheets":
                save_dir = self.assets_dir / "css"
            elif asset_type == "scripts":
                save_dir = self.assets_dir / "js"
            elif asset_type == "fonts":
                save_dir = self.assets_dir / "fonts"
            elif asset_type in ["videos", "audio"]:
                save_dir = self.assets_dir / "videos"
            else:
                save_dir = self.assets_dir / "other"

            save_dir.mkdir(parents=True, exist_ok=True)

            # Handle duplicate filenames
            original_filename = filename
            counter = 1
            while (save_dir / filename).exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1

            # Remove data URL prefix
            if base64_data.startswith("data:"):
                base64_data = base64_data.split(",")[1]

            # Save file
            file_path = save_dir / filename
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_data))

            # Track the mapping
            relative_path = f"./assets/{save_dir.name}/{filename}"
            self.asset_mappings[url] = relative_path
            self.downloaded_assets[url] = str(file_path)

        except Exception as e:
            print(f"❌ Failed to save asset {url}: {str(e)}")

    async def crawl_internal_pages(self, page, base_url, current_depth=0):
        """Crawl internal pages up to specified depth"""
        if current_depth >= self.depth:
            return

        print(f"🕷️ Crawling internal pages (depth {current_depth + 1}/{self.depth})...")

        # Get internal links
        internal_links = await page.evaluate("window.getInternalLinks()")

        for link in internal_links[:5]:  # Limit to 5 pages per depth level
            if link in self.crawled_urls:
                continue

            try:
                print(f"  📄 Crawling: {link}")
                await page.goto(link, wait_until="networkidle", timeout=30000)
                self.crawled_urls.add(link)
                self.extraction_report["pages_crawled"].append(link)

                # Wait for dynamic content
                await self.wait_for_dynamic_content(page)

                # Extract assets from this page
                await self.extract_and_download_assets(page)

                # Recursively crawl if depth allows
                if current_depth + 1 < self.depth:
                    await self.crawl_internal_pages(page, base_url, current_depth + 1)

            except Exception as e:
                print(f"  ❌ Failed to crawl {link}: {str(e)}")
                continue

        async def extract_html_and_detect_patterns(self, page):
            """Extract final HTML and detect UI patterns"""
            print("📄 Extracting HTML and detecting patterns...")

            # Get the final HTML
            html_content = await page.content()

            # Initialize default patterns structure
            default_patterns = {
                "modals": [],
                "forms": [],
                "banners": [],
                "navigation": [],
                "buttons": [],
                "inputs": [],
            }

            # Detect UI patterns with error handling
            try:
                patterns = await page.evaluate("window.detectUIPatterns()")
                if not patterns or not isinstance(patterns, dict):
                    patterns = default_patterns
                else:
                    # Ensure all expected keys exist
                    for key in default_patterns:
                        if key not in patterns:
                            patterns[key] = []

            except Exception as e:
                print(f"  ⚠️ Pattern detection failed: {e}")
                patterns = default_patterns

            # Update extraction report with safe access
            self.extraction_report.update(
                {
                    "modals_found": len(patterns.get("modals", [])),
                    "forms_found": len(patterns.get("forms", [])),
                    "components_detected": [
                        f"{len(patterns.get('modals', []))} modals",
                        f"{len(patterns.get('forms', []))} forms",
                        f"{len(patterns.get('banners', []))} banners",
                        f"{len(patterns.get('navigation', []))} navigation menus",
                    ],
                }
            )

            return html_content, patterns

    def rewrite_asset_paths(self, html_content):
        """Enhanced asset path rewriting"""
        print("🔄 Rewriting asset paths...")

        soup = BeautifulSoup(html_content, "html.parser")

        # Rewrite image sources
        for img in soup.find_all("img"):
            if img.get("src") and img["src"] in self.asset_mappings:
                img["src"] = self.asset_mappings[img["src"]]
            if img.get("data-src") and img["data-src"] in self.asset_mappings:
                img["data-src"] = self.asset_mappings[img["data-src"]]

        # Rewrite CSS links
        for link in soup.find_all("link", rel="stylesheet"):
            if link.get("href") and link["href"] in self.asset_mappings:
                link["href"] = self.asset_mappings[link["href"]]

        # Rewrite script sources
        for script in soup.find_all("script"):
            if script.get("src") and script["src"] in self.asset_mappings:
                script["src"] = self.asset_mappings[script["src"]]

        # Rewrite video sources
        for video in soup.find_all(["video", "source"]):
            if video.get("src") and video["src"] in self.asset_mappings:
                video["src"] = self.asset_mappings[video["src"]]

        # Rewrite inline styles with background images
        for element in soup.find_all(style=True):
            style = element["style"]
            for original_url, local_path in self.asset_mappings.items():
                if original_url in style:
                    style = style.replace(original_url, local_path)
            element["style"] = style

        # Add inline styles as link tags
        head = soup.find("head")
        if head:
            for key, path in self.asset_mappings.items():
                if key.startswith("inline-style-"):
                    link_tag = soup.new_tag("link", rel="stylesheet", href=path)
                    head.append(link_tag)

        return str(soup)

    def integrate_apis(self, html_content, patterns):
        """Enhanced API integration with form classification"""
        if not self.inject_apis:
            return html_content

        print("🔌 Integrating APIs...")

        soup = BeautifulSoup(html_content, "html.parser")

        # Process forms based on detected patterns
        for form_pattern in patterns["forms"]:
            form_type = form_pattern.get("formType", "generic")

            # Find the corresponding form in HTML
            form_selector = None
            if form_pattern.get("id"):
                form_selector = f"form#{form_pattern['id']}"
            elif form_pattern.get("classes"):
                classes = form_pattern["classes"].split()
                if classes:
                    form_selector = f"form.{classes[0]}"

            if form_selector:
                form = soup.select_one(form_selector)
            else:
                # Find by action or method
                forms = soup.find_all("form")
                form = None
                for f in forms:
                    if f.get("action") == form_pattern.get("action") or f.get(
                        "method"
                    ) == form_pattern.get("method"):
                        form = f
                        break

            if form:
                # Integrate appropriate API
                if form_type == "login":
                    form["action"] = self.api_mappings["login"]
                    form["method"] = "POST"
                    form["data-api-type"] = "login"
                    self.extraction_report["apis_integrated"].append("login")

                elif form_type == "register":
                    form["action"] = self.api_mappings["register"]
                    form["method"] = "POST"
                    form["data-api-type"] = "register"
                    self.extraction_report["apis_integrated"].append("register")

                elif form_type == "contact":
                    form["action"] = self.api_mappings["contact"]
                    form["method"] = "POST"
                    form["data-api-type"] = "contact"
                    self.extraction_report["apis_integrated"].append("contact")

                elif form_type == "newsletter":
                    form["action"] = self.api_mappings["newsletter"]
                    form["method"] = "POST"
                    form["data-api-type"] = "newsletter"
                    self.extraction_report["apis_integrated"].append("newsletter")

        # Add event tracking to banner clicks
        for banner in patterns["banners"]:
            if banner.get("id"):
                banner_element = soup.find(id=banner["id"])
            elif banner.get("classes"):
                classes = banner["classes"].split()
                if classes:
                    banner_element = soup.find(class_=classes[0])
                else:
                    banner_element = None
            else:
                banner_element = None

            if banner_element:
                # Add click tracking
                banner_element["data-track-event"] = "banner_click"
                banner_element["data-api-endpoint"] = self.api_mappings["events_track"]

        return str(soup)

    def create_component_files(self, patterns):
        """Create React component files with enhanced functionality"""
        print("⚛️ Creating React component files...")

        # Create enhanced Login component
        login_forms = [f for f in patterns["forms"] if f.get("formType") == "login"]
        if login_forms:
            login_component = """import React, { useState, useContext } from 'react';
import { APILoginUser } from '../helpers/APIs/UserAPIs';
import UserContext from '../helpers/Context/user-context';
import styles from './Login.module.css';
import { GoogleReCaptcha } from 'react-google-recaptcha-v3';

const Login = ({ onClose, onSwitchToRegister }) => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const { setUser } = useContext(UserContext);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            const token = await APILoginUser(phone, password);
            if (token) {
                localStorage.setItem('auth_token', token);
                setUser({ token, phone });
                onClose && onClose();
            } else {
                setError('Invalid credentials');
            }
        } catch (error) {
            setError('Login failed. Please try again.');
            console.error('Login failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.loginContainer}>
            <form onSubmit={handleLogin} className={styles.loginForm}>
                <h2>Login</h2>
                {error && <div className={styles.error}>{error}</div>}
                
                <div className={styles.inputGroup}>
                    <input
                        type="tel"
                        placeholder="Phone Number"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        required
                        className={styles.input}
                    />
                </div>
                
                <div className={styles.inputGroup}>
                    <input
                        type={showPassword ? "text" : "password"}
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className={styles.input}
                    />
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className={styles.togglePassword}
                    >
                        {showPassword ? '👁️' : '👁️‍🗨️'}
                    </button>
                </div>
                
                <button 
                    type="submit" 
                    disabled={loading}
                    className={styles.submitButton}
                >
                    {loading ? 'Logging in...' : 'Login'}
                </button>
                
                <div className={styles.links}>
                    <button 
                        type="button" 
                        onClick={onSwitchToRegister}
                        className={styles.linkButton}
                    >
                        Don't have an account? Register
                    </button>
                </div>
            </form>
        </div>
    );
};

export default Login;"""

            with open(
                self.components_dir / "Forms" / "Login.js", "w", encoding="utf-8"
            ) as f:
                f.write(login_component)

            # Create Login CSS module
            login_css = """.loginContainer {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loginForm {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.loginForm h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #333;
}

.inputGroup {
  position: relative;
  margin-bottom: 1rem;
}

.input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.input:focus {
  outline: none;
  border-color: #007bff;
}

.togglePassword {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
}

.submitButton {
  width: 100%;
  padding: 0.75rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.submitButton:hover {
  background: #0056b3;
}

.submitButton:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.links {
  text-align: center;
  margin-top: 1rem;
}

.linkButton {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
}"""

            with open(
                self.components_dir / "Forms" / "Login.module.css",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(login_css)

        # Create enhanced Register component
        register_forms = [
            f for f in patterns["forms"] if f.get("formType") == "register"
        ]
        if register_forms:
            register_component = """import React, { useState } from 'react';
import { APIRegisterUser, APICheckIfPhoneExists } from '../helpers/APIs/UserAPIs';
import styles from './Register.module.css';

const Register = ({ onClose, onSwitchToLogin }) => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        
        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }
        
        setLoading(true);
        
        try {
            const phoneExists = await APICheckIfPhoneExists(phone);
            if (phoneExists) {
                setError('Phone number already exists');
                return;
            }
            
            const token = await APIRegisterUser(phone, password, null, null, null);
            if (token) {
                setSuccess(true);
                setTimeout(() => {
                    onSwitchToLogin && onSwitchToLogin();
                }, 2000);
            } else {
                setError('Registration failed');
            }
        } catch (error) {
            setError('Registration failed. Please try again.');
            console.error('Registration failed:', error);
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className={styles.successContainer}>
                <h2>Registration Successful!</h2>
                <p>Please login with your credentials.</p>
            </div>
        );
    }

    return (
        <div className={styles.registerContainer}>
            <form onSubmit={handleRegister} className={styles.registerForm}>
                <h2>Register</h2>
                {error && <div className={styles.error}>{error}</div>}
                
                <div className={styles.inputGroup}>
                    <input
                        type="tel"
                        placeholder="Phone Number"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        required
                        className={styles.input}
                    />
                </div>
                
                <div className={styles.inputGroup}>
                    <input
                        type={showPassword ? "text" : "password"}
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className={styles.input}
                    />
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className={styles.togglePassword}
                    >
                        {showPassword ? '👁️' : '👁️‍🗨️'}
                    </button>
                </div>
                
                <div className={styles.inputGroup}>
                    <input
                        type={showPassword ? "text" : "password"}
                        placeholder="Confirm Password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className={styles.input}
                    />
                </div>
                
                <button 
                    type="submit" 
                    disabled={loading}
                    className={styles.submitButton}
                >
                    {loading ? 'Registering...' : 'Register'}
                </button>
                
                <div className={styles.links}>
                    <button 
                        type="button" 
                        onClick={onSwitchToLogin}
                        className={styles.linkButton}
                    >
                        Already have an account? Login
                    </button>
                </div>
            </form>
        </div>
    );
};

export default Register;"""

            with open(
                self.components_dir / "Forms" / "Register.js", "w", encoding="utf-8"
            ) as f:
                f.write(register_component)

            # Create Register CSS (similar to Login)
            with open(
                self.components_dir / "Forms" / "Register.module.css",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(
                    login_css.replace("login", "register").replace("Login", "Register")
                )

    def create_api_files(self):
        """Create comprehensive API helper files"""
        print("🌐 Creating API files...")

        # Create enhanced BaseUrl.js with environment support
        base_url_content = f"""import axios from "axios";

const getAxiosInstance = async () => {{
  const BaseUrl = axios.create({{
    baseURL: process.env.REACT_APP_API_BASE_URL || "{self.api_base_url}",
    timeout: 15000,
    headers: {{
      'Content-Type': 'application/json',
    }}
  }});
  
  // Request interceptor
  BaseUrl.interceptors.request.use(
    (config) => {{
      const token = localStorage.getItem('auth_token');
      if (token) {{
        config.headers.Authorization = `Bearer ${{token}}`;
      }}
      return config;
    }},
    (error) => {{
      return Promise.reject(error);
    }}
  );
  
  // Response interceptor
  BaseUrl.interceptors.response.use(
    (response) => response,
    (error) => {{
      if (error.response?.status === 401) {{
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }}
      return Promise.reject(error);
    }}
  );
  
  return BaseUrl;
}};

export default getAxiosInstance;"""

        with open(self.helpers_dir / "APIs" / "BaseUrl.js", "w", encoding="utf-8") as f:
            f.write(base_url_content)

        # Create comprehensive UserAPIs.js
        user_apis_content = """import getAxiosInstance from "./BaseUrl";

// Login API
export const APILoginUser = async (phone, password) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/login_user", { phone, password });
    if (res.data && res.data.status && res.data.token) {
      return res.data.token;
    }
  } catch (e) {
    console.error("Login API Error:", e);
    throw new Error(e.response?.data?.message || "Login failed");
  }
  return null;
};

// Register API
export const APIRegisterUser = async (phone, password, agentId, token, webGlResult) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/register_user", { 
      phone, 
      password, 
      agent_id: agentId,
      fp_data: webGlResult 
    });
    
    if (res.data && res.data.status && res.data.token) {
      return res.data.token;
    }
  } catch (e) {
    console.error("Register API Error:", e);
    throw new Error(e.response?.data?.message || "Registration failed");
  }
  return null;
};

// Check if phone exists
export const APICheckIfPhoneExists = async (phone) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/check_phone_exist", { phone });
    return res.data && res.data.status;
  } catch (e) {
    console.error("Check Phone API Error:", e);
    return false;
  }
};

// Get user info
export const APIUser = async (token) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.get("/user", {
      headers: { Authorization: `Bearer ${token}` }
    });
    return res.data;
  } catch (e) {
    console.error("User API Error:", e);
    return null;
  }
};

// Forgot password
export const APIForgotPassword = async (phone) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/forgot-password", { phone });
    return res.data;
  } catch (e) {
    console.error("Forgot Password API Error:", e);
    throw new Error(e.response?.data?.message || "Failed to send reset code");
  }
};

// Contact form submission
export const APIContactForm = async (name, email, subject, message) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/contact", { name, email, subject, message });
    return res.data;
  } catch (e) {
    console.error("Contact API Error:", e);
    throw new Error(e.response?.data?.message || "Failed to send message");
  }
};

// Newsletter subscription
export const APINewsletterSubscribe = async (email) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/newsletter/subscribe", { email });
    return res.data;
  } catch (e) {
    console.error("Newsletter API Error:", e);
    throw new Error(e.response?.data?.message || "Failed to subscribe");
  }
};

// Event tracking
export const APITrackEvent = async (eventType, eventData) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/events/track", { 
      event_type: eventType,
      event_data: eventData,
      timestamp: new Date().toISOString()
    });
    return res.data;
  } catch (e) {
    console.error("Event Tracking API Error:", e);
    // Don't throw error for tracking as it's not critical
    return null;
  }
};"""

        with open(
            self.helpers_dir / "APIs" / "UserAPIs.js", "w", encoding="utf-8"
        ) as f:
            f.write(user_apis_content)

        # Create UserContext
        user_context_content = """import React, { createContext, useState, useEffect } from 'react';
import { APIUser } from '../APIs/UserAPIs';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeUser = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const userData = await APIUser(token);
          if (userData) {
            setUser({ ...userData, token });
          } else {
            localStorage.removeItem('auth_token');
          }
        } catch (error) {
          console.error('Failed to initialize user:', error);
          localStorage.removeItem('auth_token');
        }
      }
      setLoading(false);
    };

    initializeUser();
  }, []);

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  const value = {
    user,
    setUser,
    loading,
    logout,
    isAuthenticated: !!user
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

export default UserContext;"""

        with open(
            self.helpers_dir / "Context" / "user-context.js", "w", encoding="utf-8"
        ) as f:
            f.write(user_context_content)

    def create_project_files(self, html_content):
        """Create comprehensive project files"""
        print("📁 Creating project files...")

        # Create a minimal index.html for React
        index_html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloned Website</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>"""
        with open(self.public_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(index_html_template)

        # Extract body content from the provided html_content
        body_match = re.search(r'<body.*?>(.*)</body>', html_content, re.DOTALL)
        body_content = body_match.group(1) if body_match else ''
        # Escape backticks and curly braces for inclusion in JS template literal
        body_content_escaped = body_content.replace('`', '\\`').replace('{', '{{').replace('}', '}}')

        # Create enhanced package.json
        package_json = {
            "name": "cloned-website",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0",
                "react-scripts": "5.0.1",
                "axios": "^1.3.0",
                "@mui/material": "^5.11.0",
                "@emotion/react": "^11.10.0",
                "@emotion/styled": "^11.10.0",
                "react-icons": "^4.7.0",
                "react-google-recaptcha-v3": "^1.10.0",
                "date-fns": "^2.29.0",
                "web-vitals": "^3.1.0",
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject",
                "analyze": "npm run build && npx bundle-analyzer build/static/js/*.js",
            },
            "eslintConfig": {"extends": ["react-app", "react-app/jest"]},
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version",
                ],
            },
            "proxy": self.api_base_url,
        }

        with open(self.output_dir / "package.json", "w", encoding="utf-8") as f:
            json.dump(package_json, f, indent=2)

        # Create .env file
        env_content = f"""# API Configuration
REACT_APP_API_BASE_URL={self.api_base_url}

# Google reCAPTCHA (if needed)
# REACT_APP_RECAPTCHA_SITE_KEY=your_site_key_here

# Other environment variables
REACT_APP_VERSION={package_json["version"]}
REACT_APP_BUILD_DATE={datetime.now().isoformat()}
"""

        with open(self.output_dir / ".env", "w", encoding="utf-8") as f:
            f.write(env_content)

        # Create .gitignore
        gitignore_content = """# Dependencies
node_modules/
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build

# Environment variables
.env.local
.env.# ... existing code ...
.env.development
.env.test
.env.production

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Storybook build outputs
.out
.storybook-out

# Temporary folders
tmp/
temp/

# Editor directories and files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""

        with open(self.output_dir / ".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

        # Create src/App.js with the cloned HTML body
        app_js_content = f"""import React from 'react';

function App() {{
  const clonedHtml = `{body_content_escaped}`;
  return (
    <div dangerouslySetInnerHTML={{{{ __html: clonedHtml }}}} />
  );
}}

export default App;
"""
        with open(self.src_dir / "App.js", "w", encoding="utf-8") as f:
            f.write(app_js_content)

        # Create src/index.js
        index_js_content = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        with open(self.src_dir / "index.js", "w", encoding="utf-8") as f:
            f.write(index_js_content)

        print("✅ Project files created successfully")

    def create_extraction_report(self):
        """Create detailed extraction report with analytics"""
        # Calculate total size
        total_size = 0
        for file_path in self.output_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        self.extraction_report["total_size_mb"] = round(total_size / (1024 * 1024), 2)

        # Add performance metrics
        self.extraction_report["performance"] = {
            "total_assets": sum(self.extraction_report["assets"].values()),
            "largest_asset_type": max(
                self.extraction_report["assets"],
                key=self.extraction_report["assets"].get,
            ),
            "pages_crawled_count": len(self.extraction_report["pages_crawled"]),
            "apis_integrated_count": len(self.extraction_report["apis_integrated"]),
        }

        report_path = self.output_dir / "extraction_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.extraction_report, f, indent=2)

        print(f"📊 Extraction report saved: {report_path}")
        return report_path

    def create_zip_archive(self):
        """Create production-ready zip archive"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir.parent / f"production_website_{timestamp}.zip"

        with zipfile.ZipFile(
            zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zipf:
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)

        print(f"📦 Production archive created: {zip_path}")
        return zip_path

    async def crawl_multiple_pages(self, page, start_url, max_depth=1):
        """Crawl multiple pages if depth > 1"""
        if max_depth <= 1:
            return [start_url]

        urls_to_crawl = [start_url]
        crawled_urls = set()

        for depth in range(max_depth):
            current_level_urls = []

            for url in urls_to_crawl:
                if url in crawled_urls:
                    continue

                try:
                    print(f"🔍 Crawling: {url} (depth {depth + 1})")
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await self.inject_enhanced_extraction_script(page)

                    # Get internal links
                    internal_links = await page.evaluate("window.getInternalLinks()")
                    current_level_urls.extend(
                        internal_links[:5]
                    )  # Limit to 5 links per page

                    crawled_urls.add(url)
                    self.extraction_report["pages_crawled"].append(
                        {
                            "url": url,
                            "depth": depth + 1,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    print(f"❌ Failed to crawl {url}: {str(e)}")
                    continue

            urls_to_crawl = list(set(current_level_urls) - crawled_urls)

            if not urls_to_crawl:
                break

        return list(crawled_urls)

    async def clone_website(self):
        """Main cloning process with enhanced features"""
        print(f"🚀 Starting production website cloning: {self.target_url}")
        print(f"📁 Output directory: {self.output_dir}")
        print(
            f"🔧 Configuration: headless={self.headless}, delay={self.delay}ms, depth={self.depth}"
        )

        # Setup project structure
        await self.setup_directories()

        async with async_playwright() as p:
            # Launch browser with production settings
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--disable-gpu",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )

            page = await context.new_page()

            try:
                # Navigate to target URL
                print(f"🌐 Loading {self.target_url}...")
                await page.goto(
                    self.target_url, wait_until="networkidle", timeout=60000
                )

                # Inject enhanced extraction scripts
                await self.inject_enhanced_extraction_script(page)

                # Capture initial screenshot
                await self.capture_screenshot(page, "preview.png")

                # Wait for dynamic content
                await self.wait_for_dynamic_content(page)

                # Crawl multiple pages if depth > 1
                crawled_urls = await self.crawl_multiple_pages(
                    page, self.target_url, self.depth
                )

                # Extract and download assets from all pages
                all_assets = {}
                all_patterns = {
                    "modals": [],
                    "forms": [],
                    "banners": [],
                    "navigation": [],
                }

                for url in crawled_urls:
                    try:
                        if url != self.target_url:
                            await page.goto(
                                url, wait_until="networkidle", timeout=30000
                            )
                            await self.inject_enhanced_extraction_script(page)

                        # Extract assets and patterns
                        assets = await self.extract_and_download_assets(page)
                        patterns = await page.evaluate("window.detectUIPatterns()")

                        # Merge assets and patterns
                        for asset_type, asset_list in assets.items():
                            if asset_type not in all_assets:
                                all_assets[asset_type] = []
                            all_assets[asset_type].extend(asset_list)

                        for pattern_type, pattern_list in (patterns or {}).items():
                            all_patterns[pattern_type].extend(pattern_list)

                    except Exception as e:
                        print(f"❌ Failed to process {url}: {str(e)}")
                        continue

                # Return to main page for final HTML extraction
                await page.goto(self.target_url, wait_until="networkidle")
                await self.inject_enhanced_extraction_script(page)

                # Extract final HTML and detect patterns
                # Extract HTML content and patterns
                html_content = await page.content()

                # Get UI patterns through injected script
                main_patterns = await page.evaluate("detectUIPatterns()")
                # Merge main patterns
                for pattern_type, pattern_list in (main_patterns or {}).items():
                    if pattern_type not in all_patterns:
                        all_patterns[pattern_type] = []
                    all_patterns[pattern_type].extend(pattern_list)

                # Remove duplicates from patterns
                for pattern_type in all_patterns:
                    seen = set()
                    unique_patterns = []
                    for pattern in all_patterns[pattern_type]:
                        pattern_str = json.dumps(pattern, sort_keys=True)
                        if pattern_str not in seen:
                            seen.add(pattern_str)
                            unique_patterns.append(pattern)
                    all_patterns[pattern_type] = unique_patterns

                # Update extraction report
                self.extraction_report["modals_found"] = len(all_patterns["modals"])
                self.extraction_report["forms_found"] = len(all_patterns["forms"])
                self.extraction_report["components_detected"] = [
                    f"{len(all_patterns['modals'])} modals",
                    f"{len(all_patterns['forms'])} forms",
                    f"{len(all_patterns['banners'])} banners",
                    f"{len(all_patterns['navigation'])} navigation components",
                ]

                # Rewrite asset paths
                html_content = self.rewrite_asset_paths(html_content)

                # Integrate APIs if enabled
                if self.inject_apis:
                    html_content = self.integrate_apis(html_content, all_patterns)

                # Create component files
                self.create_component_files(all_patterns)

                # Create API files
                self.create_api_files()

                # Create project files
                self.create_project_files(html_content)

                # Create extraction report
                report_path = self.create_extraction_report()

                # Create zip archive
                zip_path = self.create_zip_archive()

                # Final success message
                print(f"\n🎉 Production website cloning completed successfully!")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📦 Archive: {zip_path}")
                print(f"📊 Report: {report_path}")
                print(f"\n📈 Statistics:")
                print(
                    f"   • Pages crawled: {len(self.extraction_report['pages_crawled'])}"
                )
                print(
                    f"   • Total assets: {sum(self.extraction_report['assets'].values())}"
                )
                print(
                    f"   • Project size: {self.extraction_report['total_size_mb']} MB"
                )
                print(
                    f"   • APIs integrated: {len(self.extraction_report['apis_integrated'])}"
                )
                print(
                    f"   • Components detected: {len(self.extraction_report['components_detected'])}"
                )

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
    """CLI entry point with enhanced argument parsing"""
    parser = argparse.ArgumentParser(
        description="Production Website Cloner - Clone websites into production-ready React projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python production_website_cloner.py --url https://example.com
  python production_website_cloner.py --url https://example.com --output my_project --depth 2
  python production_website_cloner.py --url https://example.com --headless --no-apis
        """,
    )

    # Required arguments
    parser.add_argument("--url", required=True, help="Target website URL to clone")

    # Optional arguments
    parser.add_argument(
        "--output",
        default="cloned_website",
        help="Output directory name (default: cloned_website)",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=3000,
        help="Delay for dynamic content loading in milliseconds (default: 3000)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Crawling depth - number of page levels to crawl (default: 1)",
    )
    parser.add_argument(
        "--no-apis", action="store_true", help="Disable API integration"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(("http://", "https://")):
        print("❌ Error: URL must start with http:// or https://")
        return 1

    # Create output directory path
    output_path = Path(args.output)
    if output_path.exists():
        response = input(
            f"⚠️  Directory '{output_path}' already exists. Overwrite? (y/N): "
        )
        if response.lower() != "y":
            print("❌ Operation cancelled")
            return 1
        shutil.rmtree(output_path)

    # Create cloner instance
    cloner = ProductionWebsiteCloner(
        target_url=args.url,
        output_dir=args.output,
        headless=args.headless,
        delay=args.delay,
        depth=args.depth,
        inject_apis=not args.no_apis,
    )

    # Run the cloning process
    try:
        result = asyncio.run(cloner.clone_website())

        if result["success"]:
            print(f"\n✅ Cloning completed successfully!")
            print(f"\n🚀 Next steps:")
            print(f"   1. cd {result['output_dir']}")
            print(f"   2. npm install")
            print(f"   3. npm start")
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
