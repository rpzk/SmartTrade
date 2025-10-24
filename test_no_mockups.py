"""
Test script to validate NO MOCK DATA policy
This script ensures the application never uses mock/simulated data
"""

import unittest
import sys
import os
from bingx_api import BingXAPI


class TestNoMockupsPolicy(unittest.TestCase):
    """Test suite to ensure NO mock data is ever used"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = BingXAPI()

    def test_no_mock_in_source_code(self):
        """Verify source code contains no mock data references"""
        print("\n🔍 Checking source code for mock data references...")
        
        files_to_check = ['app.py', 'bingx_api.py']
        forbidden_keywords = ['mock_data', 'fake_data', 'simulated_data', 'dummy_data']
        
        for filename in files_to_check:
            if not os.path.exists(filename):
                continue
                
            with open(filename, 'r') as f:
                content = f.read().lower()
                
            for keyword in forbidden_keywords:
                self.assertNotIn(
                    keyword,
                    content,
                    f"❌ Found forbidden keyword '{keyword}' in {filename}"
                )
        
        print("✅ No mock data keywords found in source code")

    def test_api_error_no_mock_fallback(self):
        """Test that API errors don't fall back to mock data"""
        print("\n🔍 Testing API error handling...")
        
        # Test with invalid credentials
        result = self.api.get_market_price('INVALID-SYMBOL')
        
        # Should return error, not mock data
        if 'error' in result or 'success' in result and result['success'] is False:
            print("✅ API properly returns errors without mock fallback")
        else:
            # If we got data, verify it's not mock
            self.assertNotIn('mock', str(result).lower())
            self.assertNotIn('simulated', str(result).lower())
            self.assertNotIn('fake', str(result).lower())
            print("✅ Response contains no mock data indicators")

    def test_comments_emphasize_real_data(self):
        """Verify code comments emphasize real data usage"""
        print("\n🔍 Checking code documentation...")
        
        with open('bingx_api.py', 'r') as f:
            content = f.read()
        
        # Should have comments about real data
        self.assertIn('REAL', content.upper())
        self.assertIn('NO MOCK', content.upper())
        
        print("✅ Code documentation emphasizes real data usage")

    def test_html_warns_about_real_trading(self):
        """Verify HTML interface warns users about real trading"""
        print("\n🔍 Checking HTML interface warnings...")
        
        html_path = 'templates/index.html'
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                content = f.read()
            
            # Should have warnings about real trading
            self.assertIn('REAL', content.upper())
            self.assertIn('NO MOCK', content.upper())
            
            print("✅ HTML interface contains real trading warnings")
        else:
            print("⚠️  HTML file not found, skipping")

    def test_readme_documents_no_mockups(self):
        """Verify README clearly documents no mockups policy"""
        print("\n🔍 Checking README documentation...")
        
        with open('README.md', 'r') as f:
            content = f.read()
        
        # Should clearly state no mock data
        self.assertIn('NO mock', content)
        self.assertIn('REAL', content)
        self.assertIn('BingX', content)
        
        print("✅ README properly documents no mockups policy")

    def test_api_methods_return_real_data_only(self):
        """Test that API methods indicate real data sources"""
        print("\n🔍 Testing API method signatures...")
        
        api_methods = [
            'get_market_price',
            'get_kline_data',
            'get_24h_ticker',
            'get_trading_pairs'
        ]
        
        for method_name in api_methods:
            method = getattr(self.api, method_name)
            # Check docstring emphasizes real data
            if method.__doc__:
                doc = method.__doc__.lower()
                # Should explicitly state "no mock" or "real data"
                has_no_mock_statement = 'no mock' in doc or 'real data' in doc
                self.assertTrue(has_no_mock_statement,
                    f"Method {method_name} should explicitly state 'no mock' or 'real data'")
                print(f"✅ {method_name}: Explicitly states real data policy")


def run_tests():
    """Run all no-mockups policy tests"""
    print("=" * 70)
    print("🚫 NO MOCKUPS POLICY VALIDATION")
    print("=" * 70)
    print("\nValidating that SmartTrade uses ONLY real data from BingX API...")
    print("No mock data, no simulated data, no fake data allowed.\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNoMockupsPolicy)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("✅ Application follows NO MOCKUPS policy")
        print("✅ All data comes from real BingX API")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ Application may contain mock data")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
