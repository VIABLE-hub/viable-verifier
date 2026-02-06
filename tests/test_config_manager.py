"""
Perfect Tenant Configuration Manager Tests
Tests the centralized per-tenant configuration management with caching
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
import sys
sys.path.append('backend/src')

from src.tenants.config_manager import TenantConfigManager


class TestTenantConfigManager:
    """Test the core TenantConfigManager class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config_manager = TenantConfigManager()
        self.config_manager._config_cache = {}
        self.config_manager._settings_cache = {}
        self.config_manager._static_config_cache = {}
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.Path')
    def test_load_static_config_success(self, mock_path, mock_tenant_id):
        """Test successful loading of static configuration"""
        mock_tenant_id.return_value = 'tub'
        
        # Mock file existence and content
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path.return_value = mock_config_file
        
        static_config = {
            "id": "tub",
            "name": "Technische Universität Berlin",
            "color": "#c41230",
            "logo_path": "logos/tub_logo.png",
            "domain_patterns": ["tub.", "tu-berlin."]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(static_config))):
            result = self.config_manager.load_static_config('tub')
        
        assert result['id'] == 'tub'
        assert result['name'] == 'Technische Universität Berlin'
        assert result['color'] == '#c41230'
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.Path')
    def test_load_static_config_file_not_found(self, mock_path, mock_tenant_id):
        """Test handling when static config file doesn't exist"""
        mock_tenant_id.return_value = 'nonexistent'
        
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        mock_path.return_value = mock_config_file
        
        result = self.config_manager.load_static_config('nonexistent')
        
        # Should return default configuration
        assert result['id'] == 'nonexistent'
        assert result['name'] == 'Unknown Tenant'
        assert result['color'] == '#666666'
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.TenantSettings')
    @patch('src.tenants.config_manager.db')
    def test_load_dynamic_settings_success(self, mock_db, mock_tenant_settings, mock_tenant_id):
        """Test successful loading of dynamic settings"""
        mock_tenant_id.return_value = 'fub'
        
        # Mock database query
        mock_settings = MagicMock()
        mock_settings.network_config = {
            'use_ngrok': False,
            'ngrok_url': '',
            'connection_mode': 'local',
            'default_port': 8080
        }
        mock_settings.branding_config = {
            'custom_css': '',
            'footer_text': 'FU Berlin'
        }
        mock_settings.credential_config = {
            'default_validity_days': 365,
            'enable_revocation': True
        }
        
        mock_tenant_settings.query.filter_by.return_value.first.return_value = mock_settings
        
        result = self.config_manager.load_dynamic_settings('fub')
        
        assert result['network_config']['use_ngrok'] == False
        assert result['network_config']['connection_mode'] == 'local'
        assert result['branding_config']['footer_text'] == 'FU Berlin'
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.TenantSettings')
    def test_load_dynamic_settings_not_found(self, mock_tenant_settings, mock_tenant_id):
        """Test handling when tenant settings don't exist in database"""
        mock_tenant_id.return_value = 'new_tenant'
        
        mock_tenant_settings.query.filter_by.return_value.first.return_value = None
        
        result = self.config_manager.load_dynamic_settings('new_tenant')
        
        # Should return default settings
        assert result['network_config']['use_ngrok'] == False
        assert result['network_config']['default_port'] == 8080
        assert result['branding_config'] == {}
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    def test_get_complete_tenant_config(self, mock_tenant_id):
        """Test getting complete tenant configuration"""
        mock_tenant_id.return_value = 'tub'
        
        # Mock static config loading
        with patch.object(self.config_manager, 'load_static_config') as mock_static:
            mock_static.return_value = {
                'id': 'tub',
                'name': 'Technische Universität Berlin',
                'color': '#c41230'
            }
            
            # Mock dynamic settings loading
            with patch.object(self.config_manager, 'load_dynamic_settings') as mock_dynamic:
                mock_dynamic.return_value = {
                    'network_config': {
                        'use_ngrok': True,
                        'ngrok_url': 'https://tub-123.ngrok.io'
                    },
                    'branding_config': {},
                    'credential_config': {}
                }
                
                result = self.config_manager.get_complete_tenant_config('tub')
        
        assert result['id'] == 'tub'
        assert result['name'] == 'Technische Universität Berlin'
        assert result['network_config']['use_ngrok'] == True
        assert 'effective_urls' in result  # Should have computed URLs
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    def test_caching_behavior(self, mock_tenant_id):
        """Test that configurations are properly cached"""
        mock_tenant_id.return_value = 'tub'
        
        with patch.object(self.config_manager, 'load_static_config') as mock_static:
            with patch.object(self.config_manager, 'load_dynamic_settings') as mock_dynamic:
                mock_static.return_value = {'id': 'tub'}
                mock_dynamic.return_value = {'network_config': {}}
                
                # First call should load from sources
                result1 = self.config_manager.get_complete_tenant_config('tub')
                
                # Second call should use cache
                result2 = self.config_manager.get_complete_tenant_config('tub')
                
                # Should only call load functions once
                mock_static.assert_called_once()
                mock_dynamic.assert_called_once()
                
                assert result1 == result2
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    def test_cache_invalidation(self, mock_tenant_id):
        """Test cache invalidation functionality"""
        mock_tenant_id.return_value = 'fub'
        
        # Pre-populate cache
        self.config_manager._config_cache['fub'] = {'cached': True}
        
        # Invalidate cache
        self.config_manager.invalidate_cache('fub')
        
        # Cache should be cleared
        assert 'fub' not in self.config_manager._config_cache
    
    def test_compute_effective_urls_ngrok(self):
        """Test URL computation with NGROK enabled"""
        config = {
            'network_config': {
                'use_ngrok': True,
                'ngrok_url': 'https://tub-123.ngrok.io',
                'default_port': 8080
            }
        }
        
        result = self.config_manager.compute_effective_urls(config)
        
        assert result['server_url'] == 'https://tub-123.ngrok.io'
        assert result['issuer_url'] == 'https://tub-123.ngrok.io/issuer'
        assert result['verifier_url'] == 'https://tub-123.ngrok.io/verifier'
        assert result['vcstatus_url'] == 'https://tub-123.ngrok.io/vcstatus'
    
    def test_compute_effective_urls_local(self):
        """Test URL computation with local configuration"""
        config = {
            'network_config': {
                'use_ngrok': False,
                'default_ip': '192.168.1.100',
                'default_port': 8080,
                'use_https': True
            }
        }
        
        result = self.config_manager.compute_effective_urls(config)
        
        assert result['server_url'] == 'https://192.168.1.100:8080'
        assert result['issuer_url'] == 'https://192.168.1.100:8080/issuer'
        assert result['verifier_url'] == 'https://192.168.1.100:8080/verifier'
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.TenantSettings')
    @patch('src.tenants.config_manager.db')
    def test_update_network_config_success(self, mock_db, mock_tenant_settings, mock_tenant_id):
        """Test successful network configuration update"""
        mock_tenant_id.return_value = 'tub'
        
        # Mock existing settings
        mock_settings = MagicMock()
        mock_settings.network_config = {}
        mock_tenant_settings.query.filter_by.return_value.first.return_value = mock_settings
        
        network_config = {
            'use_ngrok': True,
            'ngrok_url': 'https://tub-456.ngrok.io',
            'connection_mode': 'ngrok',
            'default_port': 8080
        }
        
        result = self.config_manager.update_network_config('tub', network_config)
        
        # Should update settings and commit
        mock_db.session.commit.assert_called_once()
        assert result['network_config']['use_ngrok'] == True
        assert result['network_config']['ngrok_url'] == 'https://tub-456.ngrok.io'
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    @patch('src.tenants.config_manager.TenantSettings')
    @patch('src.tenants.config_manager.db')
    def test_update_network_config_create_new(self, mock_db, mock_tenant_settings, mock_tenant_id):
        """Test network configuration update when tenant settings don't exist"""
        mock_tenant_id.return_value = 'new_tenant'
        
        # Mock no existing settings
        mock_tenant_settings.query.filter_by.return_value.first.return_value = None
        mock_tenant_settings.return_value = MagicMock()
        
        network_config = {
            'use_ngrok': False,
            'connection_mode': 'local',
            'default_port': 8080
        }
        
        result = self.config_manager.update_network_config('new_tenant', network_config)
        
        # Should create new settings and add to session
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
        assert result['network_config']['use_ngrok'] == False


class TestTenantConfigManagerUrlGeneration:
    """Test URL generation functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config_manager = TenantConfigManager()
    
    def test_url_generation_ngrok_without_protocol(self):
        """Test URL generation when NGROK URL lacks protocol"""
        config = {
            'network_config': {
                'use_ngrok': True,
                'ngrok_url': 'abc123.ngrok.io',  # Missing https://
                'default_port': 8080
            }
        }
        
        result = self.config_manager.compute_effective_urls(config)
        
        # Should add https:// automatically
        assert result['server_url'] == 'https://abc123.ngrok.io'
        assert result['issuer_url'] == 'https://abc123.ngrok.io/issuer'
    
    def test_url_generation_custom_ports(self):
        """Test URL generation with custom ports"""
        config = {
            'network_config': {
                'use_ngrok': False,
                'default_ip': '127.0.0.1',
                'default_port': 9000,
                'use_https': False
            }
        }
        
        result = self.config_manager.compute_effective_urls(config)
        
        assert result['server_url'] == 'http://127.0.0.1:9000'
        assert result['issuer_url'] == 'http://127.0.0.1:9000/issuer'
    
    def test_url_generation_fallback_values(self):
        """Test URL generation with missing configuration values"""
        config = {
            'network_config': {
                'use_ngrok': False
                # Missing default_ip, default_port, use_https
            }
        }
        
        result = self.config_manager.compute_effective_urls(config)
        
        # Should use default values
        assert 'localhost' in result['server_url'] or '127.0.0.1' in result['server_url']
        assert ':8080' in result['server_url']


class TestTenantConfigManagerErrorHandling:
    """Test error handling in configuration manager"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config_manager = TenantConfigManager()
    
    @patch('src.tenants.config_manager.Path')
    def test_load_static_config_json_error(self, mock_path):
        """Test handling of malformed JSON in static config"""
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_path.return_value = mock_config_file
        
        # Mock file with invalid JSON
        with patch('builtins.open', mock_open(read_data='invalid json {')):
            result = self.config_manager.load_static_config('tub')
        
        # Should return default configuration on JSON error
        assert result['id'] == 'tub'
        assert result['name'] == 'Unknown Tenant'
    
    @patch('src.tenants.config_manager.TenantSettings')
    def test_load_dynamic_settings_database_error(self, mock_tenant_settings):
        """Test handling of database errors"""
        mock_tenant_settings.query.filter_by.side_effect = Exception('Database connection failed')
        
        result = self.config_manager.load_dynamic_settings('tub')
        
        # Should return default settings on database error
        assert result['network_config']['use_ngrok'] == False
        assert result['branding_config'] == {}
    
    @patch('src.tenants.config_manager.TenantSettings')
    @patch('src.tenants.config_manager.db')
    def test_update_network_config_database_error(self, mock_db, mock_tenant_settings):
        """Test handling of database errors during update"""
        mock_settings = MagicMock()
        mock_tenant_settings.query.filter_by.return_value.first.return_value = mock_settings
        
        # Mock database commit error
        mock_db.session.commit.side_effect = Exception('Database write failed')
        
        with pytest.raises(Exception, match='Database write failed'):
            self.config_manager.update_network_config('tub', {'use_ngrok': True})


class TestTenantConfigManagerIntegration:
    """Integration tests for configuration manager"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config_manager = TenantConfigManager()
    
    @patch('src.tenants.config_manager.get_current_tenant_id')
    def test_full_configuration_lifecycle(self, mock_tenant_id):
        """Test complete configuration lifecycle"""
        mock_tenant_id.return_value = 'tub'
        
        # Mock static config
        with patch.object(self.config_manager, 'load_static_config') as mock_static:
            mock_static.return_value = {
                'id': 'tub',
                'name': 'Technische Universität Berlin',
                'color': '#c41230'
            }
            
            # Mock dynamic settings
            with patch.object(self.config_manager, 'load_dynamic_settings') as mock_dynamic:
                mock_dynamic.return_value = {
                    'network_config': {
                        'use_ngrok': False,
                        'default_ip': '192.168.1.100',
                        'default_port': 8080
                    },
                    'branding_config': {},
                    'credential_config': {}
                }
                
                # Get initial configuration
                config = self.config_manager.get_complete_tenant_config('tub')
                assert config['network_config']['use_ngrok'] == False
                
                # Update network configuration
                with patch.object(self.config_manager, 'update_network_config') as mock_update:
                    mock_update.return_value = {
                        'network_config': {
                            'use_ngrok': True,
                            'ngrok_url': 'https://tub-123.ngrok.io'
                        },
                        'urls': {
                            'server_url': 'https://tub-123.ngrok.io'
                        }
                    }
                    
                    # Simulate network config update
                    new_config = {
                        'use_ngrok': True,
                        'ngrok_url': 'https://tub-123.ngrok.io'
                    }
                    
                    result = self.config_manager.update_network_config('tub', new_config)
                    assert result['network_config']['use_ngrok'] == True
    
    def test_multi_tenant_isolation(self):
        """Test that different tenants have isolated configurations"""
        # Mock different configurations for different tenants
        with patch.object(self.config_manager, 'load_static_config') as mock_static:
            with patch.object(self.config_manager, 'load_dynamic_settings') as mock_dynamic:
                
                def static_config_side_effect(tenant_id):
                    configs = {
                        'tub': {'id': 'tub', 'name': 'TU Berlin', 'color': '#c41230'},
                        'fub': {'id': 'fub', 'name': 'FU Berlin', 'color': '#008000'}
                    }
                    return configs.get(tenant_id, {'id': tenant_id})
                
                def dynamic_settings_side_effect(tenant_id):
                    settings = {
                        'tub': {
                            'network_config': {'use_ngrok': True, 'ngrok_url': 'https://tub.ngrok.io'},
                            'branding_config': {},
                            'credential_config': {}
                        },
                        'fub': {
                            'network_config': {'use_ngrok': False, 'default_ip': '192.168.1.100'},
                            'branding_config': {},
                            'credential_config': {}
                        }
                    }
                    return settings.get(tenant_id, {'network_config': {}, 'branding_config': {}, 'credential_config': {}})
                
                mock_static.side_effect = static_config_side_effect
                mock_dynamic.side_effect = dynamic_settings_side_effect
                
                # Get configurations for different tenants
                tub_config = self.config_manager.get_complete_tenant_config('tub')
                fub_config = self.config_manager.get_complete_tenant_config('fub')
                
                # Verify isolation
                assert tub_config['name'] == 'TU Berlin'
                assert fub_config['name'] == 'FU Berlin'
                assert tub_config['network_config']['use_ngrok'] == True
                assert fub_config['network_config']['use_ngrok'] == False


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short']) 