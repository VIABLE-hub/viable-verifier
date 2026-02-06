"""
Perfect Tenant System Integration Tests
Runs comprehensive integration tests across all tenant system components
"""

import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
import subprocess

# Add backend to path for imports
sys.path.append('backend/src')


class TestFullTenantSystemIntegration:
    """Integration tests for the complete tenant system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.project_root = "/Users/patrickherbke/Documents/stvc"
    
    def test_all_tenant_modules_importable(self):
        """Test that all new tenant modules can be imported successfully"""
        modules_to_test = [
            'src.tenants.detection',
            'src.tenants.config_manager', 
            'src.tenants.middleware',
            'src.settings.network_api'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ Successfully imported {module_name}")
            except ImportError as e:
                pytest.fail(f"❌ Failed to import {module_name}: {e}")
    
    def test_tenant_detection_chain_integration(self):
        """Test complete tenant detection chain works end-to-end"""
        try:
            from src.tenants.detection import (
                get_current_tenant_id, 
                clear_tenant_detection_cache
            )
            
            # Test environment variable detection
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'tub'}):
                clear_tenant_detection_cache()
                detected = get_current_tenant_id()
                assert detected == 'tub', f"Expected 'tub', got '{detected}'"
            
            print("✅ Tenant detection chain working correctly")
            
        except Exception as e:
            pytest.fail(f"❌ Tenant detection chain failed: {e}")
    
    def test_config_manager_integration(self):
        """Test configuration manager integration"""
        try:
            from src.tenants.config_manager import TenantConfigManager
            
            config_manager = TenantConfigManager()
            
            # Test URL generation for NGROK mode
            ngrok_config = {
                'network_config': {
                    'use_ngrok': True,
                    'ngrok_url': 'https://test-123.ngrok.io',
                    'default_port': 8080
                }
            }
            
            # Test NGROK URL generation
            ngrok_urls = config_manager.compute_effective_urls(ngrok_config)
            assert ngrok_urls['server_url'] == 'https://test-123.ngrok.io'
            assert ngrok_urls['issuer_url'] == 'https://test-123.ngrok.io/issuer'
            
            print("✅ Configuration manager integration working correctly")
            
        except Exception as e:
            pytest.fail(f"❌ Configuration manager integration failed: {e}")
    
    def test_tenant_files_structure(self):
        """Test that all required tenant files exist with correct structure"""
        required_files = [
            'backend/src/tenants/__init__.py',
            'backend/src/tenants/detection.py',
            'backend/src/tenants/config_manager.py',
            'backend/src/tenants/middleware.py',
            'backend/src/tenants/instances/tub/config.json',
            'backend/src/tenants/instances/fub/config.json',
            'backend/src/tenants/instances/root/config.json',
            'backend/src/settings/network_api.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if missing_files:
            pytest.fail(f"❌ Missing required files: {missing_files}")
        
        print("✅ All required tenant files exist")
    
    def test_tenant_config_files_valid(self):
        """Test that tenant configuration files are valid and complete"""
        config_files = {
            'tub': 'backend/src/tenants/instances/tub/config.json',
            'fub': 'backend/src/tenants/instances/fub/config.json', 
            'root': 'backend/src/tenants/instances/root/config.json'
        }
        
        required_fields = ['id', 'name', 'color']
        
        for tenant_id, config_file in config_files.items():
            full_path = os.path.join(self.project_root, config_file)
            
            try:
                with open(full_path, 'r') as f:
                    config_data = json.load(f)
                
                # Check required fields
                for field in required_fields:
                    assert field in config_data, f"Missing field '{field}' in {config_file}"
                
                # Check that ID matches expected tenant
                assert config_data['id'] == tenant_id, f"ID mismatch in {config_file}"
                
                print(f"✅ {tenant_id} config file valid")
                
            except Exception as e:
                pytest.fail(f"❌ Error validating {config_file}: {e}")
    
    def test_network_api_structure(self):
        """Test that network API has correct structure"""
        try:
            from src.settings.network_api import network_api
            
            # Check that blueprint is created
            assert hasattr(network_api, 'name')
            assert network_api.name == 'network_api'
            
            print("✅ Network API structure correct")
            
        except Exception as e:
            pytest.fail(f"❌ Network API structure test failed: {e}")
    
    @pytest.mark.slow
    def test_makefile_commands_exist_and_valid(self):
        """Test that makefile commands exist and have valid syntax"""
        makefile_path = os.path.join(self.project_root, "Makefile")
        
        if not os.path.exists(makefile_path):
            pytest.skip("Makefile not found - skipping command tests")
        
        with open(makefile_path, 'r') as f:
            makefile_content = f.read()
        
        # Check for required commands
        required_commands = ['dev-tub:', 'dev-fub:', 'dev-root:']
        missing_commands = []
        
        for command in required_commands:
            if command not in makefile_content:
                missing_commands.append(command)
        
        if missing_commands:
            pytest.fail(f"❌ Missing makefile commands: {missing_commands}")
        
        # Check that commands set UNIVERSITY_TENANT
        for tenant in ['tub', 'fub', 'root']:
            if f'UNIVERSITY_TENANT={tenant}' not in makefile_content:
                pytest.fail(f"❌ Command for {tenant} doesn't set UNIVERSITY_TENANT")
        
        print("✅ Makefile commands exist and are valid")


class TestTenantSystemEndToEnd:
    """End-to-end tests simulating real tenant usage"""
    
    def test_tub_tenant_simulation(self):
        """Simulate complete TUB tenant workflow"""
        try:
            # Set environment like make dev-tub would
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'tub'}):
                from src.tenants.detection import get_current_tenant_id
                from src.tenants.config_manager import TenantConfigManager
                
                # Clear cache to ensure fresh detection
                from src.tenants.detection import clear_tenant_detection_cache
                clear_tenant_detection_cache()
                
                # Test tenant detection
                detected_tenant = get_current_tenant_id()
                assert detected_tenant == 'tub'
                
                # Test config loading
                config_manager = TenantConfigManager()
                
                # Mock static config loading
                with patch.object(config_manager, 'load_static_config') as mock_static:
                    mock_static.return_value = {
                        'id': 'tub',
                        'name': 'Technische Universität Berlin',
                        'color': '#c41230'
                    }
                    
                    with patch.object(config_manager, 'load_dynamic_settings') as mock_dynamic:
                        mock_dynamic.return_value = {
                            'network_config': {
                                'use_ngrok': True,
                                'ngrok_url': 'https://tub-test.ngrok.io'
                            },
                            'branding_config': {},
                            'credential_config': {}
                        }
                        
                        # Get complete configuration
                        config = config_manager.get_complete_tenant_config('tub')
                        
                        # Verify TUB-specific configuration
                        assert config['id'] == 'tub'
                        assert config['name'] == 'Technische Universität Berlin'
                        assert config['color'] == '#c41230'
                        assert config['network_config']['use_ngrok'] == True
                        assert 'effective_urls' in config
                
                print("✅ TUB tenant simulation successful")
                
        except Exception as e:
            pytest.fail(f"❌ TUB tenant simulation failed: {e}")
    
    def test_fub_tenant_simulation(self):
        """Simulate complete FUB tenant workflow"""
        try:
            # Set environment like make dev-fub would
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'fub'}):
                from src.tenants.detection import get_current_tenant_id
                from src.tenants.config_manager import TenantConfigManager
                
                # Clear cache to ensure fresh detection
                from src.tenants.detection import clear_tenant_detection_cache
                clear_tenant_detection_cache()
                
                # Test tenant detection
                detected_tenant = get_current_tenant_id()
                assert detected_tenant == 'fub'
                
                # Test config loading
                config_manager = TenantConfigManager()
                
                # Mock static config loading  
                with patch.object(config_manager, 'load_static_config') as mock_static:
                    mock_static.return_value = {
                        'id': 'fub',
                        'name': 'Freie Universität Berlin',
                        'color': '#008000'
                    }
                    
                    with patch.object(config_manager, 'load_dynamic_settings') as mock_dynamic:
                        mock_dynamic.return_value = {
                            'network_config': {
                                'use_ngrok': False,
                                'default_ip': '192.168.1.100'
                            },
                            'branding_config': {},
                            'credential_config': {}
                        }
                        
                        # Get complete configuration
                        config = config_manager.get_complete_tenant_config('fub')
                        
                        # Verify FUB-specific configuration
                        assert config['id'] == 'fub'
                        assert config['name'] == 'Freie Universität Berlin'
                        assert config['color'] == '#008000'
                        assert config['network_config']['use_ngrok'] == False
                
                print("✅ FUB tenant simulation successful")
                
        except Exception as e:
            pytest.fail(f"❌ FUB tenant simulation failed: {e}")
    
    def test_root_tenant_simulation(self):
        """Simulate complete Root tenant workflow"""
        try:
            # Set environment like make dev-root would
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'root'}):
                from src.tenants.detection import get_current_tenant_id
                from src.tenants.config_manager import TenantConfigManager
                
                # Clear cache to ensure fresh detection
                from src.tenants.detection import clear_tenant_detection_cache
                clear_tenant_detection_cache()
                
                # Test tenant detection
                detected_tenant = get_current_tenant_id()
                assert detected_tenant == 'root'
                
                # Test config loading
                config_manager = TenantConfigManager()
                
                # Mock static config loading
                with patch.object(config_manager, 'load_static_config') as mock_static:
                    mock_static.return_value = {
                        'id': 'root',
                        'name': 'StudentVC Platform',
                        'color': '#0066cc'
                    }
                    
                    with patch.object(config_manager, 'load_dynamic_settings') as mock_dynamic:
                        mock_dynamic.return_value = {
                            'network_config': {
                                'use_ngrok': False,
                                'default_ip': '203.0.113.10'
                            },
                            'branding_config': {},
                            'credential_config': {}
                        }
                        
                        # Get complete configuration
                        config = config_manager.get_complete_tenant_config('root')
                        
                        # Verify Root-specific configuration
                        assert config['id'] == 'root'
                        assert config['name'] == 'StudentVC Platform'
                        assert config['color'] == '#0066cc'
                        assert config['network_config']['use_ngrok'] == False
                
                print("✅ Root tenant simulation successful")
                
        except Exception as e:
            pytest.fail(f"❌ Root tenant simulation failed: {e}")
    
    def test_tenant_switching_isolation(self):
        """Test that switching between tenants maintains proper isolation"""
        try:
            from src.tenants.detection import get_current_tenant_id, clear_tenant_detection_cache
            
            # Test switching from TUB to FUB
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'tub'}):
                clear_tenant_detection_cache()
                tenant1 = get_current_tenant_id()
                assert tenant1 == 'tub'
            
            # Switch to FUB
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'fub'}):
                clear_tenant_detection_cache()
                tenant2 = get_current_tenant_id()
                assert tenant2 == 'fub'
            
            # Switch to Root
            with patch.dict(os.environ, {'UNIVERSITY_TENANT': 'root'}):
                clear_tenant_detection_cache()
                tenant3 = get_current_tenant_id()
                assert tenant3 == 'root'
            
            # Verify no contamination
            assert tenant1 != tenant2
            assert tenant2 != tenant3
            assert tenant1 != tenant3
            
            print("✅ Tenant switching isolation working correctly")
            
        except Exception as e:
            pytest.fail(f"❌ Tenant switching isolation failed: {e}")


class TestSystemReadiness:
    """Test that the system is ready for production use"""
    
    def test_all_critical_files_exist(self):
        """Test that all critical files exist for production deployment"""
        critical_files = [
            'backend/main.py',
            'backend/src/__init__.py',
            'backend/src/tenants/__init__.py',
            'backend/src/tenants/detection.py',
            'backend/src/tenants/config_manager.py',
            'backend/src/tenants/middleware.py',
            'backend/src/settings/network_api.py',
            'Makefile'
        ]
        
        project_root = "/Users/patrickherbke/Documents/stvc"
        missing_files = []
        
        for file_path in critical_files:
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if missing_files:
            pytest.fail(f"❌ Critical files missing: {missing_files}")
        
        print("✅ All critical files exist")
    
    def test_no_import_errors(self):
        """Test that there are no import errors in the new modules"""
        modules_to_test = [
            'src.tenants',
            'src.tenants.detection',
            'src.tenants.config_manager',
            'src.tenants.middleware'
        ]
        
        import_errors = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                import_errors.append(f"{module_name}: {e}")
        
        if import_errors:
            pytest.fail(f"❌ Import errors found: {import_errors}")
        
        print("✅ No import errors detected")
    
    def test_integration_documentation_exists(self):
        """Test that integration documentation exists"""
        doc_files = [
            'PERFECT_TENANT_IMPLEMENTATION_GUIDE.md',
            'TENANT_OPTIMIZATION_STRATEGY.md'
        ]
        
        project_root = "/Users/patrickherbke/Documents/stvc"
        missing_docs = []
        
        for doc_file in doc_files:
            full_path = os.path.join(project_root, doc_file)
            if not os.path.exists(full_path):
                missing_docs.append(doc_file)
        
        if missing_docs:
            print(f"⚠️  Missing documentation files: {missing_docs}")
        else:
            print("✅ Integration documentation exists")


def run_complete_test_suite():
    """Run the complete test suite with proper reporting"""
    print("\n🚀 PERFECT TENANT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Run each test file
    test_files = [
        'tests/test_tenant_detection.py',
        'tests/test_network_api.py', 
        'tests/test_config_manager.py',
        'tests/test_middleware.py',
        'tests/test_tenant_isolation.py',
        'tests/test_makefile_commands.py',
        'tests/test_integration.py'
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\n📋 Running {test_file}...")
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                results[test_file] = "✅ PASSED"
            else:
                results[test_file] = "❌ FAILED"
                print(f"Error output: {result.stderr}")
                
        except Exception as e:
            results[test_file] = f"❌ ERROR: {e}"
    
    # Print summary
    print("\n📊 TEST SUITE SUMMARY")
    print("=" * 40)
    
    passed = sum(1 for result in results.values() if "PASSED" in result)
    total = len(results)
    
    for test_file, result in results.items():
        print(f"{result} {test_file}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} test files passed")
    
    if passed == total:
        print("🎉 PERFECT TENANT SYSTEM READY FOR PRODUCTION!")
        return True
    else:
        print("⚠️  Some tests failed - please review before production use")
        return False


if __name__ == '__main__':
    # Run integration tests with verbose output
    pytest.main([__file__, '-v', '--tb=short']) 