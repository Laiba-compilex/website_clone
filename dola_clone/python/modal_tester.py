import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import logging

from playwright.async_api import async_playwright, Page, Browser, ElementHandle
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('modal_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ModalTestResult:
    """Data class to store modal test results"""
    modal_id: str
    modal_selector: str
    trigger_selector: str
    trigger_text: str
    modal_type: str
    tests_passed: int
    tests_failed: int
    test_details: Dict[str, Any]
    errors: List[str]
    accessibility_score: float
    screenshot_path: Optional[str] = None

@dataclass
class TestReport:
    """Data class for the complete test report"""
    url: str
    timestamp: str
    total_modals: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    accessibility_issues: int
    modal_results: List[ModalTestResult]
    summary: Dict[str, Any]

class ModalTester:
    """Comprehensive modal testing automation class"""
    
    def __init__(self, base_url: str, output_dir: str = "modal_test_results", headless: bool = True):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.output_dir.mkdir(exist_ok=True)
        
        # Modal detection selectors
        self.modal_selectors = [
            '[role="dialog"]',
            '.modal',
            '.popup',
            '.dialog',
            '.overlay',
            '[aria-modal="true"]',
            '.lightbox',
            '.modal-dialog',
            '.popup-dialog',
            '[data-modal]',
            '[id*="modal"]',
            '[class*="modal"]',
            '[class*="popup"]',
            '[class*="dialog"]'
        ]
        
        # Modal trigger selectors
        self.trigger_selectors = [
            '[data-toggle="modal"]',
            '[data-bs-toggle="modal"]',
            '[data-target*="modal"]',
            '[data-bs-target*="modal"]',
            '.modal-trigger',
            '.popup-trigger',
            '.open-modal',
            'button[onclick*="modal"]',
            'a[href*="#modal"]',
            '[aria-haspopup="dialog"]',
            'button:has-text("Login")',
            'button:has-text("Register")',
            'button:has-text("Sign up")',
            'button:has-text("Sign in")',
            'button:has-text("Contact")',
            'button:has-text("Subscribe")',
            'a:has-text("Login")',
            'a:has-text("Register")'
        ]
        
        # Close button selectors
        self.close_selectors = [
            '.close',
            '.btn-close',
            '.modal-close',
            '[data-dismiss="modal"]',
            '[data-bs-dismiss="modal"]',
            '[aria-label="Close"]',
            '.close-btn',
            '.popup-close',
            '.dialog-close',
            'button:has-text("Close")',
            'button:has-text("Cancel")',
            'button:has-text("×")',
            '[title="Close"]'
        ]
        
        self.test_results: List[ModalTestResult] = []
        
    async def inject_modal_detection_script(self, page: Page):
        """Inject JavaScript for enhanced modal detection"""
        detection_script = """
        window.modalTester = {
            detectModals: function() {
                const modals = [];
                const modalSelectors = [
                    '[role="dialog"]', '.modal', '.popup', '.dialog', '.overlay',
                    '[aria-modal="true"]', '.lightbox', '.modal-dialog', '.popup-dialog',
                    '[data-modal]', '[id*="modal"]', '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]'
                ];
                
                modalSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(modal => {
                        if (!modals.find(m => m.element === modal)) {
                            const computedStyle = window.getComputedStyle(modal);
                            modals.push({
                                element: modal,
                                selector: selector,
                                id: modal.id || `modal_${modals.length}`,
                                classes: modal.className,
                                visible: computedStyle.display !== 'none' && computedStyle.visibility !== 'hidden',
                                zIndex: computedStyle.zIndex,
                                position: computedStyle.position,
                                hasCloseButton: this.hasCloseButton(modal),
                                hasForm: modal.querySelector('form') !== null,
                                hasImages: modal.querySelector('img') !== null,
                                ariaAttributes: this.getAriaAttributes(modal)
                            });
                        }
                    });
                });
                
                return modals;
            },
            
            hasCloseButton: function(modal) {
                const closeSelectors = [
                    '.close', '.btn-close', '.modal-close', '[data-dismiss="modal"]',
                    '[data-bs-dismiss="modal"]', '[aria-label="Close"]', '.close-btn'
                ];
                return closeSelectors.some(selector => modal.querySelector(selector) !== null);
            },
            
            getAriaAttributes: function(element) {
                const ariaAttrs = {};
                Array.from(element.attributes).forEach(attr => {
                    if (attr.name.startsWith('aria-')) {
                        ariaAttrs[attr.name] = attr.value;
                    }
                });
                return ariaAttrs;
            },
            
            detectTriggers: function() {
                const triggers = [];
                const triggerSelectors = [
                    '[data-toggle="modal"]', '[data-bs-toggle="modal"]', '[data-target*="modal"]',
                    '[data-bs-target*="modal"]', '.modal-trigger', '.popup-trigger', '.open-modal',
                    'button[onclick*="modal"]', 'a[href*="#modal"]', '[aria-haspopup="dialog"]'
                ];
                
                triggerSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(trigger => {
                        triggers.push({
                            element: trigger,
                            selector: selector,
                            text: trigger.textContent?.trim() || trigger.value || trigger.title,
                            target: trigger.getAttribute('data-target') || trigger.getAttribute('data-bs-target') || trigger.getAttribute('href'),
                            tagName: trigger.tagName.toLowerCase(),
                            type: trigger.type || 'unknown'
                        });
                    });
                });
                
                return triggers;
            },
            
            isModalVisible: function(modal) {
                const style = window.getComputedStyle(modal);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
            },
            
            waitForModalAnimation: function(modal, timeout = 3000) {
                return new Promise((resolve) => {
                    const startTime = Date.now();
                    const checkAnimation = () => {
                        if (Date.now() - startTime > timeout) {
                            resolve(false);
                            return;
                        }
                        
                        const style = window.getComputedStyle(modal);
                        if (style.transition === 'none' && style.animation === 'none') {
                            resolve(true);
                        } else {
                            setTimeout(checkAnimation, 100);
                        }
                    };
                    checkAnimation();
                });
            }
        };
        """
        
        await page.evaluate(detection_script)
        logger.info("Modal detection script injected successfully")
    
    async def detect_modals_and_triggers(self, page: Page) -> tuple:
        """Detect all modals and their triggers on the page"""
        try:
            # Get modals using injected script
            modals = await page.evaluate("window.modalTester.detectModals()")
            triggers = await page.evaluate("window.modalTester.detectTriggers()")
            
            # Also detect using Playwright selectors as backup
            playwright_modals = []
            for selector in self.modal_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        modal_info = {
                            'selector': selector,
                            'id': await element.get_attribute('id') or f'modal_{len(playwright_modals)}',
                            'classes': await element.get_attribute('class') or '',
                            'visible': await element.is_visible()
                        }
                        playwright_modals.append(modal_info)
                except Exception as e:
                    logger.warning(f"Error detecting modals with selector {selector}: {e}")
            
            playwright_triggers = []
            for selector in self.trigger_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            trigger_info = {
                                'selector': selector,
                                'text': (await element.text_content() or '').strip(),
                                'target': await element.get_attribute('data-target') or await element.get_attribute('href'),
                                'tagName': await element.evaluate('el => el.tagName.toLowerCase()')
                            }
                            playwright_triggers.append(trigger_info)
                except Exception as e:
                    logger.warning(f"Error detecting triggers with selector {selector}: {e}")
            
            logger.info(f"Detected {len(modals)} modals via script, {len(playwright_modals)} via Playwright")
            logger.info(f"Detected {len(triggers)} triggers via script, {len(playwright_triggers)} via Playwright")
            
            return modals + playwright_modals, triggers + playwright_triggers
            
        except Exception as e:
            logger.error(f"Error in modal detection: {e}")
            return [], []
    
    async def test_modal_opening(self, page: Page, trigger_info: dict) -> dict:
        """Test if a modal opens when its trigger is clicked"""
        test_result = {
            'trigger_clicked': False,
            'modal_opened': False,
            'animation_completed': False,
            'error': None
        }
        
        try:
            # Find and click the trigger
            trigger = await page.query_selector(trigger_info['selector'])
            if not trigger:
                test_result['error'] = f"Trigger not found: {trigger_info['selector']}"
                return test_result
            
            # Check if trigger is visible and clickable
            if not await trigger.is_visible():
                test_result['error'] = "Trigger is not visible"
                return test_result
            
            # Scroll trigger into view
            await trigger.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            
            # Click the trigger
            await trigger.click()
            test_result['trigger_clicked'] = True
            
            # Wait for modal to appear
            await page.wait_for_timeout(1000)
            
            # Check if any modal became visible
            for selector in self.modal_selectors:
                try:
                    modal = await page.query_selector(selector)
                    if modal and await modal.is_visible():
                        test_result['modal_opened'] = True
                        
                        # Wait for animation to complete
                        await page.wait_for_timeout(1000)
                        test_result['animation_completed'] = True
                        break
                except:
                    continue
            
            if not test_result['modal_opened']:
                test_result['error'] = "Modal did not open after trigger click"
            
        except Exception as e:
            test_result['error'] = f"Error testing modal opening: {str(e)}"
            logger.error(f"Modal opening test failed: {e}")
        
        return test_result
    
    async def test_modal_closing(self, page: Page, modal_selector: str) -> dict:
        """Test various ways to close a modal"""
        test_result = {
            'close_button': False,
            'escape_key': False,
            'outside_click': False,
            'errors': []
        }
        
        try:
            modal = await page.query_selector(modal_selector)
            if not modal or not await modal.is_visible():
                test_result['errors'].append("Modal not found or not visible")
                return test_result
            
            # Test 1: Close button
            for close_selector in self.close_selectors:
                try:
                    close_btn = await modal.query_selector(close_selector)
                    if close_btn and await close_btn.is_visible():
                        await close_btn.click()
                        await page.wait_for_timeout(1000)
                        
                        if not await modal.is_visible():
                            test_result['close_button'] = True
                            break
                        else:
                            # Re-open modal for next test
                            await self.reopen_modal_for_testing(page)
                except Exception as e:
                    test_result['errors'].append(f"Close button test error: {str(e)}")
            
            # Test 2: Escape key
            try:
                # Ensure modal is open
                if await modal.is_visible():
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(1000)
                    
                    if not await modal.is_visible():
                        test_result['escape_key'] = True
                    else:
                        await self.reopen_modal_for_testing(page)
            except Exception as e:
                test_result['errors'].append(f"Escape key test error: {str(e)}")
            
            # Test 3: Outside click (if modal supports it)
            try:
                if await modal.is_visible():
                    # Click outside the modal content
                    modal_rect = await modal.bounding_box()
                    if modal_rect:
                        # Click at the edge of the modal (outside content)
                        await page.mouse.click(modal_rect['x'] + 10, modal_rect['y'] + 10)
                        await page.wait_for_timeout(1000)
                        
                        if not await modal.is_visible():
                            test_result['outside_click'] = True
            except Exception as e:
                test_result['errors'].append(f"Outside click test error: {str(e)}")
        
        except Exception as e:
            test_result['errors'].append(f"General modal closing test error: {str(e)}")
        
        return test_result
    
    async def reopen_modal_for_testing(self, page: Page):
        """Helper method to reopen modal for subsequent tests"""
        try:
            # Try to find and click a trigger to reopen the modal
            for selector in self.trigger_selectors:
                trigger = await page.query_selector(selector)
                if trigger and await trigger.is_visible():
                    await trigger.click()
                    await page.wait_for_timeout(1000)
                    break
        except:
            pass
    
    async def test_modal_accessibility(self, page: Page, modal_selector: str) -> dict:
        """Test modal accessibility features"""
        accessibility_result = {
            'focus_trapped': False,
            'keyboard_navigation': False,
            'aria_attributes': False,
            'screen_reader_support': False,
            'score': 0.0,
            'issues': []
        }
        
        try:
            modal = await page.query_selector(modal_selector)
            if not modal:
                accessibility_result['issues'].append("Modal not found")
                return accessibility_result
            
            # Check ARIA attributes
            aria_attrs = await page.evaluate("""
                (modal) => {
                    const attrs = {};
                    Array.from(modal.attributes).forEach(attr => {
                        if (attr.name.startsWith('aria-')) {
                            attrs[attr.name] = attr.value;
                        }
                    });
                    return attrs;
                }
            """, modal)
            
            required_aria = ['aria-labelledby', 'aria-describedby', 'aria-modal']
            aria_score = sum(1 for attr in required_aria if attr in aria_attrs) / len(required_aria)
            
            if aria_score > 0.5:
                accessibility_result['aria_attributes'] = True
            else:
                accessibility_result['issues'].append("Missing important ARIA attributes")
            
            # Test keyboard navigation
            try:
                await modal.focus()
                await page.keyboard.press('Tab')
                focused_element = await page.evaluate('document.activeElement.tagName')
                if focused_element:
                    accessibility_result['keyboard_navigation'] = True
            except Exception as e:
                accessibility_result['issues'].append(f"Keyboard navigation test failed: {str(e)}")
            
            # Test focus trapping (simplified)
            try:
                focusable_elements = await modal.query_selector_all(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                )
                if len(focusable_elements) > 0:
                    accessibility_result['focus_trapped'] = True
            except Exception as e:
                accessibility_result['issues'].append(f"Focus trapping test failed: {str(e)}")
            
            # Calculate accessibility score
            passed_tests = sum([
                accessibility_result['aria_attributes'],
                accessibility_result['keyboard_navigation'],
                accessibility_result['focus_trapped']
            ])
            accessibility_result['score'] = passed_tests / 3.0
            
        except Exception as e:
            accessibility_result['issues'].append(f"Accessibility test error: {str(e)}")
        
        return accessibility_result
    
    async def test_dynamic_content(self, page: Page, modal_selector: str) -> dict:
        """Test if modal handles dynamic content loading"""
        dynamic_test = {
            'has_dynamic_content': False,
            'content_loaded': False,
            'loading_time': 0,
            'errors': []
        }
        
        try:
            modal = await page.query_selector(modal_selector)
            if not modal:
                dynamic_test['errors'].append("Modal not found")
                return dynamic_test
            
            # Check for loading indicators
            loading_selectors = ['.loading', '.spinner', '.loader', '[data-loading]']
            has_loader = False
            
            for selector in loading_selectors:
                loader = await modal.query_selector(selector)
                if loader:
                    has_loader = True
                    dynamic_test['has_dynamic_content'] = True
                    break
            
            # Check for AJAX/fetch requests
            start_time = time.time()
            
            # Wait for potential dynamic content
            await page.wait_for_timeout(3000)
            
            # Check if content has loaded (no more loading indicators)
            if has_loader:
                content_loaded = True
                for selector in loading_selectors:
                    loader = await modal.query_selector(selector)
                    if loader and await loader.is_visible():
                        content_loaded = False
                        break
                
                dynamic_test['content_loaded'] = content_loaded
                dynamic_test['loading_time'] = time.time() - start_time
            
        except Exception as e:
            dynamic_test['errors'].append(f"Dynamic content test error: {str(e)}")
        
        return dynamic_test
    
    def classify_modal_type(self, modal_info: dict, trigger_info: dict) -> str:
        """Classify the type of modal based on content and trigger"""
        trigger_text = trigger_info.get('text', '').lower()
        modal_classes = modal_info.get('classes', '').lower()
        
        # Form modals
        if any(keyword in trigger_text for keyword in ['login', 'register', 'sign up', 'sign in', 'contact']):
            return 'form'
        
        # Confirmation modals
        if any(keyword in trigger_text for keyword in ['delete', 'confirm', 'remove', 'sure']):
            return 'confirmation'
        
        # Information modals
        if any(keyword in trigger_text for keyword in ['info', 'about', 'help', 'details']):
            return 'information'
        
        # Image modals
        if any(keyword in modal_classes for keyword in ['lightbox', 'gallery', 'image']):
            return 'image'
        
        return 'generic'
    
    async def capture_modal_screenshot(self, page: Page, modal_selector: str, modal_id: str) -> Optional[str]:
        """Capture screenshot of the modal"""
        try:
            modal = await page.query_selector(modal_selector)
            if modal and await modal.is_visible():
                screenshot_path = self.output_dir / f"modal_{modal_id}_{int(time.time())}.png"
                await modal.screenshot(path=str(screenshot_path))
                return str(screenshot_path)
        except Exception as e:
            logger.warning(f"Failed to capture screenshot for modal {modal_id}: {e}")
        return None
    
    async def test_single_modal(self, page: Page, modal_info: dict, trigger_info: dict) -> ModalTestResult:
        """Test a single modal comprehensively"""
        modal_id = modal_info.get('id', f"modal_{int(time.time())}")
        modal_selector = modal_info.get('selector', '')
        trigger_selector = trigger_info.get('selector', '')
        trigger_text = trigger_info.get('text', '')
        
        logger.info(f"Testing modal: {modal_id} with trigger: {trigger_text}")
        
        test_details = {}
        errors = []
        tests_passed = 0
        tests_failed = 0
        
        try:
            # Test modal opening
            opening_result = await self.test_modal_opening(page, trigger_info)
            test_details['opening'] = opening_result
            
            if opening_result['modal_opened']:
                tests_passed += 1
                
                # Capture screenshot
                screenshot_path = await self.capture_modal_screenshot(page, modal_selector, modal_id)
                
                # Test modal closing
                closing_result = await self.test_modal_closing(page, modal_selector)
                test_details['closing'] = closing_result
                
                if any(closing_result.values()):
                    tests_passed += 1
                else:
                    tests_failed += 1
                    errors.extend(closing_result.get('errors', []))
                
                # Test accessibility
                accessibility_result = await self.test_modal_accessibility(page, modal_selector)
                test_details['accessibility'] = accessibility_result
                
                if accessibility_result['score'] > 0.5:
                    tests_passed += 1
                else:
                    tests_failed += 1
                    errors.extend(accessibility_result.get('issues', []))
                
                # Test dynamic content
                dynamic_result = await self.test_dynamic_content(page, modal_selector)
                test_details['dynamic_content'] = dynamic_result
                
                if not dynamic_result.get('errors'):
                    tests_passed += 1
                else:
                    tests_failed += 1
                    errors.extend(dynamic_result.get('errors', []))
                
            else:
                tests_failed += 1
                errors.append(opening_result.get('error', 'Modal failed to open'))
                accessibility_result = {'score': 0.0}
                screenshot_path = None
            
            # Classify modal type
            modal_type = self.classify_modal_type(modal_info, trigger_info)
            
            return ModalTestResult(
                modal_id=modal_id,
                modal_selector=modal_selector,
                trigger_selector=trigger_selector,
                trigger_text=trigger_text,
                modal_type=modal_type,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                test_details=test_details,
                errors=errors,
                accessibility_score=accessibility_result.get('score', 0.0),
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            logger.error(f"Error testing modal {modal_id}: {e}")
            return ModalTestResult(
                modal_id=modal_id,
                modal_selector=modal_selector,
                trigger_selector=trigger_selector,
                trigger_text=trigger_text,
                modal_type='unknown',
                tests_passed=0,
                tests_failed=1,
                test_details={},
                errors=[f"Test execution error: {str(e)}"],
                accessibility_score=0.0
            )
    
    async def test_responsive_modals(self, page: Page, viewport_sizes: List[tuple]):
        """Test modals across different viewport sizes"""
        responsive_results = {}
        
        for width, height in viewport_sizes:
            logger.info(f"Testing modals at viewport {width}x{height}")
            await page.set_viewport_size({"width": width, "height": height})
            await page.wait_for_timeout(1000)
            
            # Re-detect modals and triggers for this viewport
            modals, triggers = await self.detect_modals_and_triggers(page)
            
            viewport_results = []
            for i, (modal, trigger) in enumerate(zip(modals, triggers)):
                if i < len(triggers):  # Ensure we have a corresponding trigger
                    result = await self.test_single_modal(page, modal, trigger)
                    viewport_results.append(result)
            
            responsive_results[f"{width}x{height}"] = viewport_results
        
        return responsive_results
    
    async def generate_report(self, responsive_results: dict = None) -> TestReport:
        """Generate comprehensive test report"""
        total_tests = sum(result.tests_passed + result.tests_failed for result in self.test_results)
        passed_tests = sum(result.tests_passed for result in self.test_results)
        failed_tests = sum(result.tests_failed for result in self.test_results)
        accessibility_issues = sum(1 for result in self.test_results if result.accessibility_score < 0.7)
        
        summary = {
            'modal_types': {},
            'common_issues': [],
            'accessibility_summary': {
                'average_score': sum(result.accessibility_score for result in self.test_results) / len(self.test_results) if self.test_results else 0,
                'modals_with_issues': accessibility_issues
            },
            'responsive_summary': responsive_results or {}
        }
        
        # Count modal types
        for result in self.test_results:
            modal_type = result.modal_type
            if modal_type not in summary['modal_types']:
                summary['modal_types'][modal_type] = 0
            summary['modal_types'][modal_type] += 1
        
        # Identify common issues
        all_errors = []
        for result in self.test_results:
            all_errors.extend(result.errors)
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        summary['common_issues'] = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return TestReport(
            url=self.base_url,
            timestamp=datetime.now().isoformat(),
            total_modals=len(self.test_results),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            accessibility_issues=accessibility_issues,
            modal_results=self.test_results,
            summary=summary
        )
    
    def save_report(self, report: TestReport, format_type: str = 'json'):
        """Save test report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            report_path = self.output_dir / f"modal_test_report_{timestamp}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        elif format_type == 'html':
            report_path = self.output_dir / f"modal_test_report_{timestamp}.html"
            html_content = self.generate_html_report(report)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        logger.info(f"Report saved: {report_path}")
        return report_path
    
    def generate_html_report(self, report: TestReport) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Modal Test Report - {report.url}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat-box {{ background: #e9ecef; padding: 15px; border-radius: 5px; flex: 1; }}
                .modal-result {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .passed {{ border-left: 5px solid #28a745; }}
                .failed {{ border-left: 5px solid #dc3545; }}
                .warning {{ border-left: 5px solid #ffc107; }}
                .error {{ color: #dc3545; }}
                .success {{ color: #28a745; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Modal Test Report</h1>
                <p><strong>URL:</strong> {report.url}</p>
                <p><strong>Test Date:</strong> {report.timestamp}</p>
            </div>
            
            <div class="summary">
                <div class="stat-box">
                    <h3>Total Modals</h3>
                    <h2>{report.total_modals}</h2>
                </div>
                <div class="stat-box">
                    <h3>Tests Passed</h3>
                    <h2 class="success">{report.passed_tests}</h2>
                </div>
                <div class="stat-box">
                    <h3>Tests Failed</h3>
                    <h2 class="error">{report.failed_tests}</h2>
                </div>
                <div class="stat-box">
                    <h3>Accessibility Issues</h3>
                    <h2 class="{'error' if report.accessibility_issues > 0 else 'success'}">{report.accessibility_issues}</h2>
                </div>
            </div>
            
            <h2>Modal Test Results</h2>
        """
        
        for result in report.modal_results:
            status_class = 'passed' if result.tests_failed == 0 else 'failed'
            html += f"""
            <div class="modal-result {status_class}">
                <h3>Modal: {result.modal_id}</h3>
                <p><strong>Type:</strong> {result.modal_type}</p>
                <p><strong>Trigger:</strong> {result.trigger_text}</p>
                <p><strong>Tests Passed:</strong> {result.tests_passed} | <strong>Failed:</strong> {result.tests_failed}</p>
                <p><strong>Accessibility Score:</strong> {result.accessibility_score:.2f}</p>
                
                {f'<p><strong>Screenshot:</strong> <a href="{result.screenshot_path}">View</a></p>' if result.screenshot_path else ''}
                
                {f'<div class="error"><strong>Errors:</strong><ul>{"".join(f"<li>{error}</li>" for error in result.errors)}</ul></div>' if result.errors else ''}
            </div>
            """
        
        html += """
            </body>
        </html>
        """
        
        return html
    
    async def run_tests(self, test_responsive: bool = True, viewport_sizes: List[tuple] = None):
        """Run comprehensive modal tests"""
        if viewport_sizes is None:
            viewport_sizes = [(1920, 1080), (1366, 768), (768, 1024), (375, 667)]
        
        logger.info(f"Starting modal tests for {self.base_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            try:
                page = await browser.new_page()
                await page.goto(self.base_url, wait_until="networkidle")
                
                # Inject modal detection script
                await self.inject_modal_detection_script(page)
                
                # Wait for page to fully load
                await page.wait_for_timeout(3000)
                
                # Detect modals and triggers
                modals, triggers = await self.detect_modals_and_triggers(page)
                
                if not modals or not triggers:
                    logger.warning("No modals or triggers detected on the page")
                    return await self.generate_report()
                
                logger.info(f"Found {len(modals)} modals and {len(triggers)} triggers")
                
                # Test each modal
                for i, modal in enumerate(modals):
                    if i < len(triggers):  # Ensure we have a corresponding trigger
                        trigger = triggers[i]
                        result = await self.test_single_modal(page, modal, trigger)
                        self.test_results.append(result)
                        
                        # Wait between tests
                        await page.wait_for_timeout(1000)
                
                # Test responsive behavior if requested
                responsive_results = None
                if test_responsive:
                    responsive_results = await self.test_responsive_modals(page, viewport_sizes)
                
                # Generate and save report
                report = await self.generate_report(responsive_results)
                
                # Save reports in both formats
                json_path = self.save_report(report, 'json')
                html_path = self.save_report(report, 'html')
                
                logger.info(f"Modal testing completed. Reports saved:")
                logger.info(f"JSON: {json_path}")
                logger.info(f"HTML: {html_path}")
                
                return report
                
            except Exception as e:
                logger.error(f"Error during modal testing: {e}")
                raise
            
            finally:
                await browser.close()

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Automated Modal Testing Tool")
    parser.add_argument("--url", required=True, help="Target website URL")
    parser.add_argument("--output", default="modal_test_results", help="Output directory")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--no-responsive", action="store_true", help="Skip responsive testing")
    parser.add_argument("--viewport-sizes", nargs="*", help="Custom viewport sizes (format: WIDTHxHEIGHT)")
    
    args = parser.parse_args()
    
    # Parse viewport sizes
    viewport_sizes = [(1920, 1080), (1366, 768), (768, 1024), (375, 667)]
    if args.viewport_sizes:
        viewport_sizes = []
        for size in args.viewport_sizes:
            try:
                width, height = map(int, size.split('x'))
                viewport_sizes.append((width, height))
            except ValueError:
                logger.warning(f"Invalid viewport size format: {size}. Using default sizes.")
                viewport_sizes = [(1920, 1080), (1366, 768), (768, 1024), (375, 667)]
                break
    
    # Create tester instance
    tester = ModalTester(
        base_url=args.url,
        output_dir=args.output,
        headless=args.headless
    )
    
    # Run tests
    try:
        report = asyncio.run(tester.run_tests(
            test_responsive=not args.no_responsive,
            viewport_sizes=viewport_sizes
        ))
        
        print(f"\n✅ Modal testing completed!")
        print(f"📊 Results: {report.passed_tests} passed, {report.failed_tests} failed")
        print(f"🔍 Accessibility issues: {report.accessibility_issues}")
        print(f"📁 Reports saved in: {args.output}")
        
        return 0 if report.failed_tests == 0 else 1
        
    except Exception as e:
        logger.error(f"Modal testing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())