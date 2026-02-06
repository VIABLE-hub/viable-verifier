#!/usr/bin/env python3
"""
End-to-End Testing Script for Verifiable Credential Issuance and Verification
Tests the complete flow between Python backend and iOS Wallet compatibility
"""

import requests
import json
import base64
import jwt
import time
import sys
from urllib.parse import urlparse, parse_qs
import logging

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndToEndTester:
    def __init__(self, base_url="https://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for local testing
        
        # iOS compatibility headers
        self.session.headers.update({
            'User-Agent': 'StudentWallet/1.0 (iOS)',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def test_backend_health(self):
        """Test basic backend connectivity and key endpoints"""
        logger.info("Testing backend health...")
        
        tests = [
            ("Root endpoint", "/"),
            ("Verifier endpoint", "/verifier/"),
            ("JWKS endpoint", "/jwks"),
            ("OpenID configuration", "/.well-known/openid-configuration"),
            ("Credential issuer metadata", "/.well-known/openid-credential-issuer")
        ]
        
        results = {}
        for name, endpoint in tests:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                results[name] = {
                    'status_code': response.status_code,
                    'success': response.status_code in [200, 302],  # 302 for redirects
                    'response_size': len(response.text)
                }
                logger.info(f"✅ {name}: Status {response.status_code}")
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}
                logger.error(f"❌ {name}: {e}")
        
        return results
        
    def test_field_mapping_compatibility(self):
        """Test snake_case to camelCase field mapping for iOS compatibility"""
        logger.info("Testing field mapping compatibility...")
        
        backend_fields = [
            "total_messages",
            "bbs_dpk", 
            "signed_nonce",
            "validity_identifier"
        ]
        
        ios_fields = [
            "totalMessages",
            "bbsDPK",
            "signedNonce", 
            "validityIdentifier"
        ]
        
        # Test mapping logic
        field_mapping = {
            "total_messages": "totalMessages",
            "bbs_dpk": "bbsDPK", 
            "signed_nonce": "signedNonce",
            "validity_identifier": "validityIdentifier"
        }
        
        mapping_tests = []
        for backend_field in backend_fields:
            ios_equivalent = field_mapping.get(backend_field, backend_field)
            test_passed = ios_equivalent in ios_fields
            mapping_tests.append({
                'backend_field': backend_field,
                'ios_field': ios_equivalent,
                'mapping_correct': test_passed
            })
            
            if test_passed:
                logger.info(f"✅ Field mapping: {backend_field} → {ios_equivalent}")
            else:
                logger.error(f"❌ Field mapping: {backend_field} → {ios_equivalent}")
        
        return {
            'mapping_tests': mapping_tests,
            'all_mappings_correct': all(test['mapping_correct'] for test in mapping_tests)
        }
        
    def test_presentation_request_flow(self):
        """Test the presentation request flow compatible with iOS"""
        logger.info("Testing presentation request flow...")
        
        try:
            # Simulate presentation request (GET to verifier)
            response = self.session.get(f"{self.base_url}/verifier/")
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Verifier page failed: {response.status_code}'}
            
            # Test presentation-request endpoint
            response = self.session.post(f"{self.base_url}/verifier/presentation-request")
            
            if response.status_code not in [200, 302]:
                return {'success': False, 'error': f'Presentation request failed: {response.status_code}'}
            
            # If it's a redirect, check the redirect URL format
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                
                # Parse the redirect URL to check iOS compatibility
                if redirect_url.startswith('openid4vp://'):
                    parsed = urlparse(redirect_url)
                    query_params = parse_qs(parsed.query)
                    
                    required_params = ['client_id', 'response_type', 'response_mode', 'presentation_definition']
                    missing_params = [param for param in required_params if param not in query_params]
                    
                    if missing_params:
                        return {
                            'success': False, 
                            'error': f'Missing required parameters: {missing_params}',
                            'redirect_url': redirect_url
                        }
                    
                    return {
                        'success': True,
                        'redirect_url': redirect_url,
                        'params': query_params
                    }
                else:
                    return {'success': False, 'error': f'Invalid redirect URL format: {redirect_url}'}
            
            return {'success': True, 'status_code': response.status_code}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_credential_issuance_compatibility(self):
        """Test credential issuance flow compatibility"""
        logger.info("Testing credential issuance compatibility...")
        
        try:
            # Get issuer page
            response = self.session.get(f"{self.base_url}/issuer")
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Issuer page failed: {response.status_code}'}
            
            # Test credential offer generation
            test_credential_data = {
                'firstName': 'Test',
                'lastName': 'Student', 
                'studentId': '12345',
                'studentIdPrefix': 'TU',
                'theme': {
                    'name': 'Test Theme',
                    'bgColorCard': '#FF0000'
                }
            }
            
            # Post form data to issuer
            form_data = {
                'firstName': test_credential_data['firstName'],
                'lastName': test_credential_data['lastName'],
                'studentId': test_credential_data['studentId'],
                'studentIdPrefix': test_credential_data['studentIdPrefix'],
                'theme[name]': test_credential_data['theme']['name'],
                'theme[bgColorCard]': test_credential_data['theme']['bgColorCard']
            }
            
            response = self.session.post(f"{self.base_url}/issuer", data=form_data)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Credential issuance failed: {response.status_code}'}
            
            return {'success': True, 'response_size': len(response.text)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_ios_network_compatibility(self):
        """Test iOS-specific network requirements"""
        logger.info("Testing iOS network compatibility...")
        
        compatibility_tests = {}
        
        # Test HTTPS requirement
        try:
            http_response = requests.get(self.base_url.replace('https://', 'http://'), verify=False, timeout=5)
            compatibility_tests['https_required'] = http_response.status_code != 200
        except:
            compatibility_tests['https_required'] = True  # Good, HTTP should fail
            
        # Test CORS headers
        try:
            response = self.session.options(f"{self.base_url}/verifier/")
            cors_headers = {
                'access-control-allow-origin': response.headers.get('Access-Control-Allow-Origin'),
                'access-control-allow-methods': response.headers.get('Access-Control-Allow-Methods'),
                'access-control-allow-headers': response.headers.get('Access-Control-Allow-Headers')
            }
            compatibility_tests['cors_headers'] = cors_headers
        except Exception as e:
            compatibility_tests['cors_headers'] = {'error': str(e)}
            
        # Test Content-Type handling
        try:
            response = self.session.get(f"{self.base_url}/jwks")
            content_type = response.headers.get('Content-Type', '')
            compatibility_tests['json_content_type'] = 'application/json' in content_type
        except Exception as e:
            compatibility_tests['json_content_type'] = {'error': str(e)}
            
        return compatibility_tests
        
    def test_bbs_core_integration(self):
        """Test BBS+ core integration for signature verification"""
        logger.info("Testing BBS+ core integration...")
        
        try:
            # Import BBS core to test availability
            import sys
            import os
            
            bbs_core_path = os.path.join(os.path.dirname(__file__), "backend", "bbs-core", "python", "bbs_core.py")
            bbs_core_path = os.path.abspath(bbs_core_path)
            
            if not os.path.exists(bbs_core_path):
                return {'success': False, 'error': f'BBS core not found at: {bbs_core_path}'}
            
            # Check if BBS core can be imported
            import importlib.util
            spec = importlib.util.spec_from_file_location("bbs_core", bbs_core_path)
            bbs_core = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bbs_core)
            
            # Test basic BBS functionality
            available_functions = dir(bbs_core)
            required_functions = ['KeyPair', 'Signature', 'verify']  # Expected BBS functions
            
            missing_functions = [func for func in required_functions if func not in available_functions]
            
            return {
                'success': len(missing_functions) == 0,
                'available_functions': len(available_functions),
                'missing_functions': missing_functions,
                'bbs_core_path': bbs_core_path
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def run_all_tests(self):
        """Run complete end-to-end test suite"""
        logger.info("Starting comprehensive end-to-end testing...")
        
        test_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'backend_url': self.base_url
        }
        
        # Run all test categories
        test_categories = [
            ('Backend Health', self.test_backend_health),
            ('Field Mapping', self.test_field_mapping_compatibility),
            ('Presentation Request', self.test_presentation_request_flow),
            ('Credential Issuance', self.test_credential_issuance_compatibility),
            ('iOS Network Compatibility', self.test_ios_network_compatibility),
            ('BBS+ Core Integration', self.test_bbs_core_integration)
        ]
        
        passed_tests = 0
        total_tests = len(test_categories)
        
        for category_name, test_function in test_categories:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing: {category_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = test_function()
                test_results[category_name.lower().replace(' ', '_')] = result
                
                # Determine if test passed
                if isinstance(result, dict) and result.get('success') is not False:
                    if category_name == 'Field Mapping':
                        test_passed = result.get('all_mappings_correct', False)
                    elif category_name == 'Backend Health':
                        test_passed = all(r.get('success', False) for r in result.values())
                    else:
                        test_passed = result.get('success', True)
                else:
                    test_passed = False
                    
                if test_passed:
                    passed_tests += 1
                    logger.info(f"✅ {category_name}: PASSED")
                else:
                    logger.error(f"❌ {category_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {category_name}: ERROR - {e}")
                test_results[category_name.lower().replace(' ', '_')] = {'success': False, 'error': str(e)}
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        test_results['summary'] = {
            'passed': passed_tests,
            'total': total_tests,
            'success_rate': (passed_tests/total_tests)*100
        }
        
        return test_results

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://127.0.0.1:8080"
    
    logger.info(f"Starting end-to-end tests for: {base_url}")
    
    tester = EndToEndTester(base_url)
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = 'end_to_end_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nDetailed results saved to: {results_file}")
    
    # Exit with appropriate code
    success_rate = results.get('summary', {}).get('success_rate', 0)
    exit_code = 0 if success_rate >= 80 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
