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

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
from PIL import Image
import io

class EnhancedWebsiteCloner:
    def __init__(self, target_url, output_dir="cloned_website", headless=True, delay=3000):
        self.target_url = target_url
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.delay = delay
        self.assets_dir = self.output_dir / "assets"
        self.components_dir = self.output_dir / "components"
        self.api_dir = self.output_dir / "api"
        self.helpers_dir = self.output_dir / "helpers"
        self.pages_dir = self.output_dir / "pages"
        self.layout_dir = self.output_dir / "layout"
        
        # Asset tracking
        self.downloaded_assets = {}
        self.asset_mappings = {}
        self.extraction_report = {
            "url": target_url,
            "timestamp": datetime.now().isoformat(),
            "assets": {"images": 0, "css": 0, "js": 0, "fonts": 0, "other": 0},
            "components_detected": [],
            "apis_integrated": [],
            "modals_found": 0,
            "forms_found": 0
        }
        
        # API integration mappings based on your existing projects
        self.api_mappings = {
            "login": "/api/login_user",
            "register": "/api/register_user",
            "forgot_password": "/api/forgot-password",
            "contact": "/api/contact",
            "newsletter": "/api/newsletter/subscribe",
            "deposit": "/api/account/deposit",
            "withdraw": "/api/account/withdraw",
            "transactions": "/api/account/user_transaction",
            "announcements": "/api/announcements",
            "notifications": "/api/notifications",
            "banks": "/api/bank/company_banks",
            "events_track": "/api/events/track"
        }

    async def setup_directories(self):
        """Create the project structure matching your frontend architecture"""
        directories = [
            self.output_dir,
            self.assets_dir / "images",
            self.assets_dir / "css",
            self.assets_dir / "js",
            self.assets_dir / "fonts",
            self.assets_dir / "icons",
            self.components_dir,
            self.api_dir,
            self.helpers_dir / "APIs",
            self.helpers_dir / "Context",
            self.pages_dir / "login",
            self.pages_dir / "register",
            self.pages_dir / "User",
            self.pages_dir / "FooterPages",
            self.layout_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Created project structure in {self.output_dir}")

    async def inject_asset_extraction_script(self, page):
        """Inject comprehensive asset extraction script into browser context"""
        extraction_script = """
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
                if (img.src) assets.images.push({
                    url: img.src,
                    alt: img.alt || '',
                    element: 'img'
                });
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
                    type: script.type || 'text/javascript'
                });
            });
            
            // Extract fonts from CSS
            Array.from(document.styleSheets).forEach(sheet => {
                try {
                    Array.from(sheet.cssRules || sheet.rules).forEach(rule => {
                        if (rule.style && rule.style.fontFamily) {
                            const fontMatch = rule.cssText.match(/url\(['"]?([^'"\)]+)['"]?\)/g);
                            if (fontMatch) {
                                fontMatch.forEach(match => {
                                    const url = match.match(/url\(['"]?([^'"\)]+)['"]?\)/)[1];
                                    assets.fonts.push({url: new URL(url, window.location.href).href});
                                });
                            }
                        }
                    });
                } catch (e) {}
            });
            
            // Extract background images
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.backgroundImage && style.backgroundImage !== 'none') {
                    const matches = style.backgroundImage.match(/url\(['"]?([^'"\)]+)['"]?\)/g);
                    if (matches) {
                        matches.forEach(match => {
                            const url = match.match(/url\(['"]?([^'"\)]+)['"]?\)/)[1];
                            assets.background_images.push({
                                url: new URL(url, window.location.href).href,
                                element: el.tagName.toLowerCase()
                            });
                        });
                    }
                }
            });
            
            // Extract videos
            document.querySelectorAll('video, source').forEach(video => {
                if (video.src) assets.videos.push({url: video.src});
            });
            
            return assets;
        };
        
        // Function to download assets as base64 (bypass CORS)
        window.downloadAssetAsBase64 = async function(url) {
            try {
                const response = await fetch(url);
                const blob = await response.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve({
                        success: true,
                        data: reader.result,
                        contentType: blob.type,
                        size: blob.size
                    });
                    reader.readAsDataURL(blob);
                });
            } catch (error) {
                return {success: false, error: error.message};
            }
        };
        
        // Detect UI patterns
        window.detectUIPatterns = function() {
            const patterns = {
                modals: [],
                forms: [],
                banners: [],
                navigation: []
            };
            
            // Detect modals
            document.querySelectorAll('[class*="modal"], [id*="modal"], .popup, .dialog').forEach(modal => {
                patterns.modals.push({
                    element: modal.tagName,
                    classes: modal.className,
                    id: modal.id,
                    visible: window.getComputedStyle(modal).display !== 'none'
                });
            });
            
            // Detect forms
            document.querySelectorAll('form').forEach(form => {
                const inputs = form.querySelectorAll('input, textarea, select');
                patterns.forms.push({
                    action: form.action,
                    method: form.method,
                    inputs: Array.from(inputs).map(input => ({
                        type: input.type,
                        name: input.name,
                        placeholder: input.placeholder
                    }))
                });
            });
            
            // Detect banners/sliders
            document.querySelectorAll('[class*="banner"], [class*="slider"], [class*="carousel"]').forEach(banner => {
                patterns.banners.push({
                    element: banner.tagName,
                    classes: banner.className,
                    id: banner.id
                });
            });
            
            return patterns;
        };
        """
        
        await page.evaluate(extraction_script)
        print("✅ Asset extraction script injected")

    async def wait_for_dynamic_content(self, page):
        """Wait for dynamic content to load including modals and lazy-loaded elements"""
        print("⏳ Waiting for dynamic content...")
        
        # Wait for initial load
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(self.delay / 1000)
        
        # Try to trigger modals and dynamic content
        modal_triggers = [
            'button[data-toggle="modal"]',
            'a[data-toggle="modal"]',
            '.modal-trigger',
            '[onclick*="modal"]',
            'button:has-text("Login")',
            'button:has-text("Register")',
            'button:has-text("Sign up")',
            '.login-btn',
            '.register-btn'
        ]
        
        for selector in modal_triggers:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements[:3]:  # Limit to first 3 to avoid spam
                    try:
                        await element.click(timeout=1000)
                        await asyncio.sleep(0.5)
                        # Try to close modal
                        close_selectors = ['.modal .close', '.modal-close', '[data-dismiss="modal"]', '.close-btn']
                        for close_sel in close_selectors:
                            try:
                                close_btn = await page.query_selector(close_sel)
                                if close_btn:
                                    await close_btn.click(timeout=500)
                                    break
                            except:
                                continue
                        await asyncio.sleep(0.5)
                    except:
                        continue
            except:
                continue
        
        # Scroll to trigger lazy loading
        await page.evaluate("""
            window.scrollTo(0, document.body.scrollHeight / 4);
        """)
        await asyncio.sleep(1)
        
        await page.evaluate("""
            window.scrollTo(0, document.body.scrollHeight / 2);
        """)
        await asyncio.sleep(1)
        
        await page.evaluate("""
            window.scrollTo(0, document.body.scrollHeight);
        """)
        await asyncio.sleep(1)
        
        await page.evaluate("window.scrollTo(0, 0);")
        await asyncio.sleep(1)
        
        print("✅ Dynamic content loading completed")

    async def extract_and_download_assets(self, page):
        """Extract all assets and download them using browser context"""
        print("🔍 Extracting assets...")
        
        # Get all assets
        assets = await page.evaluate("window.extractAllAssets()")
        
        # Download each asset type
        for asset_type, asset_list in assets.items():
            if not asset_list:
                continue
                
            print(f"📥 Downloading {len(asset_list)} {asset_type}...")
            
            for i, asset in enumerate(asset_list):
                try:
                    url = asset['url'] if isinstance(asset, dict) else asset
                    if not url or url.startswith('data:'):
                        continue
                    
                    # Download using browser context to bypass CORS
                    result = await page.evaluate(f"window.downloadAssetAsBase64('{url}')")
                    
                    if result.get('success'):
                        # Save the asset
                        await self.save_asset(url, result['data'], asset_type, result.get('contentType', ''))
                        self.extraction_report['assets'][asset_type if asset_type in self.extraction_report['assets'] else 'other'] += 1
                    
                except Exception as e:
                    print(f"❌ Failed to download {url}: {str(e)}")
                    continue
        
        print("✅ Asset extraction completed")

    async def save_asset(self, url, base64_data, asset_type, content_type):
        """Save asset from base64 data"""
        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or f"asset_{len(self.downloaded_assets)}"
            
            # Determine file extension
            if not os.path.splitext(filename)[1]:
                if 'image' in content_type:
                    ext = '.png' if 'png' in content_type else '.jpg'
                elif 'css' in content_type:
                    ext = '.css'
                elif 'javascript' in content_type:
                    ext = '.js'
                elif 'font' in content_type:
                    ext = '.woff2' if 'woff2' in content_type else '.woff'
                else:
                    ext = '.bin'
                filename += ext
            
            # Determine save directory
            if asset_type in ['images', 'background_images']:
                save_dir = self.assets_dir / "images"
            elif asset_type == 'stylesheets':
                save_dir = self.assets_dir / "css"
            elif asset_type == 'scripts':
                save_dir = self.assets_dir / "js"
            elif asset_type == 'fonts':
                save_dir = self.assets_dir / "fonts"
            else:
                save_dir = self.assets_dir / "other"
            
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Remove data URL prefix
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            # Save file
            file_path = save_dir / filename
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(base64_data))
            
            # Track the mapping
            relative_path = f"./assets/{save_dir.name}/{filename}"
            self.asset_mappings[url] = relative_path
            self.downloaded_assets[url] = str(file_path)
            
        except Exception as e:
            print(f"❌ Failed to save asset {url}: {str(e)}")

    async def extract_html_and_detect_patterns(self, page):
        """Extract final HTML and detect UI patterns"""
        print("📄 Extracting HTML and detecting patterns...")
        
        # Get the final HTML
        html_content = await page.evaluate("document.documentElement.outerHTML")
        
        # Detect UI patterns
        patterns = await page.evaluate("window.detectUIPatterns()")
        
        # Update extraction report
        self.extraction_report['modals_found'] = len(patterns['modals'])
        self.extraction_report['forms_found'] = len(patterns['forms'])
        self.extraction_report['components_detected'] = [
            f"{len(patterns['modals'])} modals",
            f"{len(patterns['forms'])} forms",
            f"{len(patterns['banners'])} banners"
        ]
        
        return html_content, patterns

    def rewrite_asset_paths(self, html_content):
        """Rewrite all asset paths to point to local files"""
        print("🔄 Rewriting asset paths...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Rewrite image sources
        for img in soup.find_all('img'):
            if img.get('src') and img['src'] in self.asset_mappings:
                img['src'] = self.asset_mappings[img['src']]
        
        # Rewrite CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href') and link['href'] in self.asset_mappings:
                link['href'] = self.asset_mappings[link['href']]
        
        # Rewrite script sources
        for script in soup.find_all('script'):
            if script.get('src') and script['src'] in self.asset_mappings:
                script['src'] = self.asset_mappings[script['src']]
        
        # Rewrite inline styles with background images
        for element in soup.find_all(style=True):
            style = element['style']
            for original_url, local_path in self.asset_mappings.items():
                if original_url in style:
                    style = style.replace(original_url, local_path)
            element['style'] = style
        
        return str(soup)

    def integrate_apis(self, html_content, patterns):
        """Integrate your project APIs into forms and components"""
        print("🔌 Integrating APIs...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Process forms
        for form in soup.find_all('form'):
            form_inputs = [inp.get('name', '').lower() for inp in form.find_all('input')]
            
            # Detect form type and integrate appropriate API
            if any(field in form_inputs for field in ['email', 'username', 'phone']) and 'password' in form_inputs:
                if any(field in form_inputs for field in ['confirm', 'repeat']):
                    # Registration form
                    form['action'] = self.api_mappings['register']
                    form['method'] = 'POST'
                    self.extraction_report['apis_integrated'].append('register')
                else:
                    # Login form
                    form['action'] = self.api_mappings['login']
                    form['method'] = 'POST'
                    self.extraction_report['apis_integrated'].append('login')
            
            elif any(field in form_inputs for field in ['message', 'subject', 'contact']):
                # Contact form
                form['action'] = self.api_mappings['contact']
                form['method'] = 'POST'
                self.extraction_report['apis_integrated'].append('contact')
            
            elif any(field in form_inputs for field in ['newsletter', 'subscribe']):
                # Newsletter form
                form['action'] = self.api_mappings['newsletter']
                form['method'] = 'POST'
                self.extraction_report['apis_integrated'].append('newsletter')
        
        return str(soup)

    def create_component_files(self, patterns):
        """Create React component files based on detected patterns"""
        print("⚛️ Creating component files...")
        
        # Create Login component
        if any('login' in str(pattern).lower() for pattern in patterns['forms']):
            login_component = '''
import React, { useState, useContext } from 'react';
import { APILoginUser } from '../helpers/APIs/UserAPIs';
import UserContext from '../helpers/Context/user-context';
import styles from './Login.module.css';

const Login = () => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { setUser } = useContext(UserContext);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            const token = await APILoginUser(phone, password);
            if (token) {
                localStorage.setItem('auth_token', token);
                setUser({ token, phone });
            }
        } catch (error) {
            console.error('Login failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleLogin} className={styles.loginForm}>
            <input
                type="tel"
                placeholder="Phone Number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
            </button>
        </form>
    );
};

export default Login;
'''
            
            with open(self.components_dir / 'Login.js', 'w', encoding='utf-8') as f:
                f.write(login_component)
        
        # Create Register component
        if any('register' in str(pattern).lower() or 'signup' in str(pattern).lower() for pattern in patterns['forms']):
            register_component = '''
import React, { useState } from 'react';
import { APIRegisterUser, APICheckIfPhoneExists } from '../helpers/APIs/UserAPIs';
import styles from './Register.module.css';

const Register = () => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e) => {
        e.preventDefault();
        
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        setLoading(true);
        
        try {
            const phoneExists = await APICheckIfPhoneExists(phone);
            if (phoneExists) {
                alert('Phone number already exists');
                return;
            }
            
            const token = await APIRegisterUser(phone, password, null, null, null);
            if (token) {
                alert('Registration successful!');
            }
        } catch (error) {
            console.error('Registration failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleRegister} className={styles.registerForm}>
            <input
                type="tel"
                placeholder="Phone Number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
            />
            <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Registering...' : 'Register'}
            </button>
        </form>
    );
};

export default Register;
'''
            
            with open(self.components_dir / 'Register.js', 'w', encoding='utf-8') as f:
                f.write(register_component)

    def create_api_files(self):
        """Create API helper files based on your existing structure"""
        print("🌐 Creating API files...")
        
        # Create BaseUrl.js
        base_url_content = '''
import axios from "axios";

const getAxiosInstance = async () => {
  const BaseUrl = axios.create({
    baseURL: "https://bo.gavn138.com/api",
    timeout: 10000,
  });
  
  return BaseUrl;
};

export default getAxiosInstance;
'''
        
        with open(self.helpers_dir / 'APIs' / 'BaseUrl.js', 'w', encoding='utf-8') as f:
            f.write(base_url_content)
        
        # Create UserAPIs.js
        user_apis_content = '''
import getAxiosInstance from "./BaseUrl";

// Login API
export const APILoginUser = async (phone, password) => {
  const BaseUrl = await getAxiosInstance();
  
  try {
    const res = await BaseUrl.post("/login_user", { phone, password });
    if (res.data && res.data.status && res.data.token) {
      return res.data.token;
    }
  } catch (e) {
    throw new Error("Login failed");
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
    throw new Error("Registration failed");
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
    return null;
  }
};
'''
        
        with open(self.helpers_dir / 'APIs' / 'UserAPIs.js', 'w', encoding='utf-8') as f:
            f.write(user_apis_content)

    def create_project_files(self, html_content):
        """Create additional project files"""
        print("📁 Creating project files...")
        
        # Save the main HTML file
        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create package.json
        package_json = {
            "name": "cloned-website",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0",
                "axios": "^1.3.0",
                "@mui/material": "^5.11.0",
                "react-icons": "^4.7.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
        
        with open(self.output_dir / 'package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
        
        # Create README.md
        readme_content = f'''
# Cloned Website Project

This project was automatically generated by the Enhanced Website Cloner.

## Source
- **Original URL**: {self.target_url}
- **Cloned on**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Project Structure
- `/assets` - All downloaded assets (images, CSS, JS, fonts)
- `/components` - React components
- `/helpers/APIs` - API integration files
- `/pages` - Page components
- `/layout` - Layout components

## Installation
```bash
npm install
npm start
```

## Features
- ✅ Complete asset extraction and local storage
- ✅ API integration with existing backend
- ✅ React component structure
- ✅ Responsive design preservation
- ✅ Modal and form functionality

## Extraction Report
{json.dumps(self.extraction_report, indent=2)}
'''
        
        with open(self.output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def create_extraction_report(self):
        """Create detailed extraction report"""
        report_path = self.output_dir / 'extraction_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_report, f, indent=2)
        
        print(f"📊 Extraction report saved to {report_path}")

    def create_zip_archive(self):
        """Create a zip archive of the cloned website"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir.parent / f"cloned_website_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)
        
        print(f"📦 Created zip archive: {zip_path}")
        return zip_path

    async def clone_website(self):
        """Main method to clone the website"""
        print(f"🚀 Starting website cloning: {self.target_url}")
        
        # Setup project structure
        await self.setup_directories()
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to target URL
                print(f"🌐 Loading {self.target_url}...")
                await page.goto(self.target_url, wait_until='networkidle')
                
                # Inject asset extraction scripts
                await self.inject_asset_extraction_script(page)
                
                # Wait for dynamic content
                await self.wait_for_dynamic_content(page)
                
                # Extract and download assets
                await self.extract_and_download_assets(page)
                
                # Extract HTML and detect patterns
                html_content, patterns = await self.extract_html_and_detect_patterns(page)
                
                # Rewrite asset paths
                html_content = self.rewrite_asset_paths(html_content)
                
                # Integrate APIs
                html_content = self.integrate_apis(html_content, patterns)
                
                # Create component files
                self.create_component_files(patterns)
                
                # Create API files
                self.create_api_files()
                
                # Create project files
                self.create_project_files(html_content)
                
                # Create extraction report
                self.create_extraction_report()
                
                # Create zip archive
                zip_path = self.create_zip_archive()
                
                print(f"\n✅ Website cloning completed successfully!")
                print(f"📁 Output directory: {self.output_dir}")
                print(f"📦 Zip archive: {zip_path}")
                print(f"📊 Total assets downloaded: {sum(self.extraction_report['assets'].values())}")
                print(f"🔌 APIs integrated: {len(self.extraction_report['apis_integrated'])}")
                
            except Exception as e:
                print(f"❌ Error during cloning: {str(e)}")
                raise
            
            finally:
                await browser.close()

def main():
    parser = argparse.ArgumentParser(description='Enhanced Website Cloner')
    parser.add_argument('--url', required=True, help='Target website URL')
    parser.add_argument('--output', default='cloned_website', help='Output directory')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--delay', type=int, default=3000, help='Delay for dynamic content (ms)')
    parser.add_argument('--inject-apis', action='store_true', default=True, help='Inject API integrations')
    
    args = parser.parse_args()
    
    # Create cloner instance
    cloner = EnhancedWebsiteCloner(
        target_url=args.url,
        output_dir=args.output,
        headless=args.headless,
        delay=args.delay
    )
    
    # Run the cloning process
    asyncio.run(cloner.clone_website())

if __name__ == "__main__":
    main()