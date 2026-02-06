/**
 * StudentVC Settings Component
 * Vanilla JS implementation replacing Alpine.js
 */

document.addEventListener('DOMContentLoaded', function() {
  // State management
  const state = {
    // Navigation
    activeTab: 'dashboard',
    
    // Theme
    darkMode: localStorage.getItem('darkMode') === 'true' || false,
    
    // Data state
    systemData: null,
    databaseData: null,
    networkData: null,
    healthData: {
      issuer: null,
      verifier: null,
      websocket: null,
      sse: null,
      database: null,
      ssl: null
    },
    
    // NGROK state
    unifiedNgrokDomain: '',
    unifiedDefaultIp: '',
    unifiedDefaultPort: '8080',
    
    // Database state
    databaseStatus: null,
    backupList: [],
    selectedBackupId: null,
    
    // Loading states
    dashboardRefreshing: false,
    systemRefreshing: false,
    databaseLoading: false,
    backupListLoading: false,
    backupCreating: false,
    backupRestoring: false,
    importLoading: false,
    exportLoading: false,
    networkRefreshing: false,
    networkConfigUpdating: false,
    networkTestRunning: false,
    
    // Network configuration
    systemNetworkData: null,
    networkConfigurationResult: null,
    networkTestResults: null,
    
    // Timestamps
    lastUpdated: new Date().toLocaleString()
  };
  
  // DOM Elements cache
  const elements = {
    tabButtons: {},
    tabContents: {},
    loaders: {},
    forms: {},
    statusIndicators: {}
  };
  
  /**
   * Initialize the component
   */
  function init() {
    // Initialize dark mode
    document.documentElement.classList.toggle('dark', state.darkMode);
    
    // Cache DOM elements
    cacheElements();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    console.log('Settings component initialized');
  }
  
  /**
   * Cache commonly used DOM elements
   */
  function cacheElements() {
    // Tab buttons
    document.querySelectorAll('[data-tab]').forEach(button => {
      elements.tabButtons[button.dataset.tab] = button;
    });
    
    // Tab contents
    document.querySelectorAll('[data-tab-content]').forEach(content => {
      elements.tabContents[content.dataset.tabContent] = content;
    });
    
    // Loading indicators
    document.querySelectorAll('[data-loader]').forEach(loader => {
      elements.loaders[loader.dataset.loader] = loader;
    });
    
    // Forms
    document.querySelectorAll('form').forEach(form => {
      if (form.id) {
        elements.forms[form.id] = form;
      }
    });
    
    // Status indicators
    document.querySelectorAll('[data-status]').forEach(indicator => {
      elements.statusIndicators[indicator.dataset.status] = indicator;
    });
  }
  
  /**
   * Set up all event listeners
   */
  function setupEventListeners() {
    // Tab navigation
    Object.keys(elements.tabButtons).forEach(tabId => {
      elements.tabButtons[tabId].addEventListener('click', () => switchToTab(tabId));
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
      darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
    // Manual refresh button
    const refreshButton = document.getElementById('manual-refresh-button');
    if (refreshButton) {
      refreshButton.addEventListener('click', manualRefresh);
    }
    
    // Network form events
    const ngrokToggle = document.getElementById('use-ngrok-toggle');
    if (ngrokToggle) {
      ngrokToggle.addEventListener('change', () => {
        state.networkData.use_ngrok = ngrokToggle.checked;
        updateNetworkSettings();
      });
    }
    
    // Database backup/restore events
    const createBackupButton = document.getElementById('create-backup-button');
    if (createBackupButton) {
      createBackupButton.addEventListener('click', createDatabaseBackup);
    }
    
    const exportButton = document.getElementById('export-database-button');
    if (exportButton) {
      exportButton.addEventListener('click', exportDatabaseSQL);
    }
    
    const importForm = document.getElementById('import-database-form');
    if (importForm) {
      importForm.addEventListener('submit', (e) => {
        e.preventDefault();
        importDatabaseSQL();
      });
    }
  }
  
  /**
   * Load initial data based on active tab
   */
  function loadInitialData() {
    // Set default tab if none active
    if (!state.activeTab) {
      switchToTab('dashboard');
    } else {
      updateActiveTabUI();
    }
    
    // Load dashboard data
    if (state.activeTab === 'dashboard') {
      fetchDashboardData();
    }
    
    // Update timestamp
    updateLastUpdated();
  }
  
  /**
   * Switch to a different tab
   */
  function switchToTab(tabId) {
    // Update state
    state.activeTab = tabId;
    
    // Update UI
    updateActiveTabUI();
    
    // Load data based on tab
    if (tabId === 'dashboard' && !state.dashboardRefreshing) {
      fetchDashboardData();
    } else if (tabId === 'system' && !state.systemRefreshing) {
      fetchSystemData();
    } else if (tabId === 'database' && !state.databaseLoading) {
      loadDatabaseStatus();
      loadBackupList();
    } else if (tabId === 'network' && !state.networkRefreshing) {
      fetchNetworkData();
    } else if (tabId === 'api') {
      // API documentation tab - no data loading needed
    }
  }
  
  /**
   * Update the UI to reflect the active tab
   */
  function updateActiveTabUI() {
    // Update tab buttons
    Object.keys(elements.tabButtons).forEach(tabId => {
      const button = elements.tabButtons[tabId];
      if (tabId === state.activeTab) {
        button.classList.add('text-berlin-blue', 'border-berlin-blue', 'border-b-2');
        button.classList.remove('text-gray-500', 'dark:text-gray-400', 'hover:text-gray-700', 'dark:hover:text-gray-300');
      } else {
        button.classList.remove('text-berlin-blue', 'border-berlin-blue', 'border-b-2');
        button.classList.add('text-gray-500', 'dark:text-gray-400', 'hover:text-gray-700', 'dark:hover:text-gray-300');
      }
    });
    
    // Show active tab content, hide others
    Object.keys(elements.tabContents).forEach(tabId => {
      const content = elements.tabContents[tabId];
      if (tabId === state.activeTab) {
        content.classList.remove('hidden');
      } else {
        content.classList.add('hidden');
      }
    });
  }
  
  /**
   * Toggle dark mode
   */
  function toggleDarkMode() {
    state.darkMode = !state.darkMode;
    localStorage.setItem('darkMode', state.darkMode);
    document.documentElement.classList.toggle('dark', state.darkMode);
  }
  
  /**
   * Update the last updated timestamp
   */
  function updateLastUpdated() {
    state.lastUpdated = new Date().toLocaleString();
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
      lastUpdatedElement.textContent = state.lastUpdated;
    }
  }
  
  /**
   * Format bytes to human-readable format
   */
  function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }
  
  /**
   * Format uptime seconds to human-readable format
   */
  function formatUptime(seconds) {
    if (!seconds) return '0s';
    
    const days = Math.floor(seconds / 86400);
    seconds %= 86400;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    seconds %= 60;
    
    let result = '';
    if (days > 0) result += `${days}d `;
    if (hours > 0 || days > 0) result += `${hours}h `;
    if (minutes > 0 || hours > 0 || days > 0) result += `${minutes}m `;
    result += `${Math.floor(seconds)}s`;
    
    return result;
  }
  
  /**
   * Format timestamp to human-readable format
   */
  function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (e) {
      return timestamp.toString();
    }
  }
  
  /**
   * Show notification
   */
  function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) return;
    
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 flex items-center p-4 rounded-lg shadow-lg transform transition-transform duration-300 z-50';
    
    switch (type) {
      case 'success':
        notification.classList.add('bg-green-500', 'text-white');
        break;
      case 'error':
        notification.classList.add('bg-red-500', 'text-white');
        break;
      case 'warning':
        notification.classList.add('bg-yellow-500', 'text-white');
        break;
      default:
        notification.classList.add('bg-blue-500', 'text-white');
    }
    
    notification.innerHTML = `
      <div class="mr-3">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          ${type === 'success' ? 
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' : 
            type === 'error' ? 
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>' :
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'}
        </svg>
      </div>
      <div>${message}</div>
      <button class="ml-auto text-white focus:outline-none">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;
    
    notificationContainer.appendChild(notification);
    
    const closeButton = notification.querySelector('button');
    closeButton.addEventListener('click', () => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    });
    
    setTimeout(() => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }
  
  /**
   * Helper functions for network status visualization
   */
  function getStatusBgClass(status) {
    if (!status) return 'bg-gray-100 dark:bg-gray-800';
    
    switch (status) {
      case 'healthy':
        return 'bg-green-50 dark:bg-green-900/20';
      case 'degraded':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'critical':
        return 'bg-red-50 dark:bg-red-900/20';
      default:
        return 'bg-gray-100 dark:bg-gray-800';
    }
  }
  
  function getStatusDotClass(status) {
    if (!status) return 'bg-gray-400';
    
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  }
  
  function getStatusText(status) {
    if (!status) return 'Unknown';
    
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'critical':
        return 'Critical';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  }
  
  /**
   * API Functions
   */
  
  // Dashboard data
  async function fetchDashboardData() {
    state.dashboardRefreshing = true;
    updateLoadingUI('dashboard', true);
    
    try {
      // Fetch health data
      const healthResponse = await fetch('/settings/api/health');
      if (healthResponse.ok) {
        state.healthData = await healthResponse.json();
      }
      
      // Fetch system data
      const systemResponse = await fetch('/settings/api/system');
      if (systemResponse.ok) {
        state.systemData = await systemResponse.json();
      }
      
      // Update UI with new data
      updateDashboardUI();
      
      // Update timestamp
      updateLastUpdated();
    } catch (error) {
      console.error('Dashboard data fetch failed:', error);
      showNotification('Failed to load dashboard data', 'error');
    } finally {
      state.dashboardRefreshing = false;
      updateLoadingUI('dashboard', false);
    }
  }
  
  // System data
  async function fetchSystemData() {
    state.systemRefreshing = true;
    updateLoadingUI('system', true);
    
    try {
      const response = await fetch('/settings/api/system/health');
      if (response.ok) {
        state.systemData = await response.json();
        updateSystemUI();
      }
    } catch (error) {
      console.error('System data fetch failed:', error);
      showNotification('Failed to load system data', 'error');
    } finally {
      state.systemRefreshing = false;
      updateLoadingUI('system', false);
    }
  }
  
  // Network data
  async function fetchNetworkData() {
    state.networkRefreshing = true;
    updateLoadingUI('network', true);
    
    try {
      // Fetch network system data
      const response = await fetch('/settings/api/system/network');
      if (response.ok) {
        state.systemNetworkData = await response.json();
        updateNetworkUI();
      }
    } catch (error) {
      console.error('Network data fetch failed:', error);
      showNotification('Failed to load network data', 'error');
    } finally {
      state.networkRefreshing = false;
      updateLoadingUI('network', false);
    }
  }
  
  // Database functions
  async function loadDatabaseStatus() {
    state.databaseLoading = true;
    updateLoadingUI('database', true);
    
    try {
      console.log('Loading database status...');
      const response = await fetch('/settings/api/database/status');
      if (response.ok) {
        state.databaseStatus = await response.json();
        console.log('Database status loaded:', state.databaseStatus);
        updateDatabaseStatusUI();
      } else {
        throw new Error(`HTTP ${response.status}: Failed to fetch database status`);
      }
    } catch (error) {
      console.error('Database status load failed:', error);
      showNotification('Failed to load database status', 'error');
    } finally {
      state.databaseLoading = false;
      updateLoadingUI('database', false);
    }
  }
  
  async function loadBackupList() {
    state.backupListLoading = true;
    
    try {
      console.log('Loading backup list...');
      const response = await fetch('/settings/api/database/backup/list');
      if (response.ok) {
        state.backupList = await response.json();
        console.log('Backup list loaded:', state.backupList);
        updateBackupListUI();
      } else {
        throw new Error(`HTTP ${response.status}: Failed to fetch backup list`);
      }
    } catch (error) {
      console.error('Backup list load failed:', error);
    } finally {
      state.backupListLoading = false;
    }
  }
  
  async function createDatabaseBackup() {
    state.backupCreating = true;
    updateButtonState('create-backup-button', true);
    
    try {
      console.log('Creating database backup...');
      const response = await fetch('/settings/api/database/backup/create', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('Database backup created');
        showNotification('Database backup created successfully', 'success');
        await loadBackupList();
      } else {
        throw new Error(`HTTP ${response.status}: Failed to create database backup`);
      }
    } catch (error) {
      console.error('Database backup creation failed:', error);
      showNotification('Failed to create database backup', 'error');
    } finally {
      state.backupCreating = false;
      updateButtonState('create-backup-button', false);
    }
  }
  
  async function exportDatabaseSQL() {
    state.exportLoading = true;
    updateButtonState('export-database-button', true);
    
    try {
      console.log('Exporting database as SQL...');
      window.location.href = '/settings/api/database/export/sql';
      setTimeout(() => {
        state.exportLoading = false;
        updateButtonState('export-database-button', false);
      }, 2000);
    } catch (error) {
      console.error('Database export failed:', error);
      showNotification('Failed to export database', 'error');
      state.exportLoading = false;
      updateButtonState('export-database-button', false);
    }
  }
  
  async function importDatabaseSQL() {
    const importFileInput = document.getElementById('database-import-file');
    if (!importFileInput?.files?.length) {
      showNotification('Please select a file to import', 'error');
      return;
    }
    
    state.importLoading = true;
    updateButtonState('import-database-button', true);
    
    try {
      const formData = new FormData();
      formData.append('file', importFileInput.files[0]);
      
      console.log('Importing database from SQL...');
      const response = await fetch('/settings/api/database/import/sql', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        console.log('Database import successful');
        showNotification('Database imported successfully', 'success');
        await loadDatabaseStatus();
        importFileInput.value = '';
      } else {
        throw new Error(`HTTP ${response.status}: Failed to import database`);
      }
    } catch (error) {
      console.error('Database import failed:', error);
      showNotification('Failed to import database: ' + error.message, 'error');
    } finally {
      state.importLoading = false;
      updateButtonState('import-database-button', false);
    }
  }
  
  // Network functions
  async function updateNetworkSettings() {
    state.networkConfigUpdating = true;
    updateButtonState('save-network-config-button', true);
    
    try {
      const response = await fetch('/settings/api/network', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_ngrok: state.systemNetworkData.unified_config.use_ngrok,
          ngrok_domain: state.unifiedNgrokDomain,
          default_ip: state.unifiedDefaultIp,
          default_port: state.unifiedDefaultPort
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        state.networkConfigurationResult = {
          success: true,
          message: 'Network configuration saved successfully'
        };
        showNotification('Network configuration saved', 'success');
      } else {
        throw new Error(`HTTP ${response.status}: Failed to save network configuration`);
      }
    } catch (error) {
      console.error('Failed to save network configuration:', error);
      state.networkConfigurationResult = {
        success: false,
        message: 'Failed to save network configuration'
      };
      showNotification('Failed to save network configuration', 'error');
    } finally {
      state.networkConfigUpdating = false;
      updateButtonState('save-network-config-button', false);
      displayNetworkConfigResult();
    }
  }
  
  async function runNetworkDiagnostics() {
    state.networkTestRunning = true;
    updateButtonState('test-network-button', true);
    
    try {
      const response = await fetch('/settings/api/system/network/test');
      if (response.ok) {
        state.networkTestResults = await response.json();
        displayNetworkDiagnostics();
      } else {
        throw new Error(`HTTP ${response.status}: Failed to run network diagnostics`);
      }
    } catch (error) {
      console.error('Network diagnostics failed:', error);
      showNotification('Failed to run network diagnostics', 'error');
    } finally {
      state.networkTestRunning = false;
      updateButtonState('test-network-button', false);
    }
  }
  
  /**
   * UI Update Functions
   */
  function updateLoadingUI(section, isLoading) {
    const loader = elements.loaders[section];
    if (loader) {
      if (isLoading) {
        loader.classList.remove('hidden');
      } else {
        loader.classList.add('hidden');
      }
    }
  }
  
  function updateButtonState(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.disabled = isLoading;
      
      const loadingSpinner = button.querySelector('.loading-spinner');
      const buttonText = button.querySelector('.button-text');
      
      if (loadingSpinner) {
        if (isLoading) {
          loadingSpinner.classList.remove('hidden');
        } else {
          loadingSpinner.classList.add('hidden');
        }
      }
      
      if (buttonText) {
        if (isLoading && buttonText.dataset.loadingText) {
          buttonText.textContent = buttonText.dataset.loadingText;
        } else if (!isLoading && buttonText.dataset.defaultText) {
          buttonText.textContent = buttonText.dataset.defaultText;
        }
      }
    }
  }
  
  function updateDashboardUI() {
    // Update system status indicators
    updateSystemStatusIndicators();
    
    // Update resource metrics
    updateResourceMetrics();
    
    // Update database statistics
    updateDatabaseStatistics();
    
    // Update network information
    updateNetworkInformation();
  }
  
  function updateSystemStatusIndicators() {
    // Update issuer status
    updateStatusIndicator('issuer', state.healthData?.issuer?.status === 'online');
    
    // Update verifier status
    updateStatusIndicator('verifier', state.healthData?.verifier?.status === 'online');
    
    // Update WebSocket status
    updateStatusIndicator('websocket', state.healthData?.websocket?.status === 'available');
    
    // Update SSE status
    updateStatusIndicator('sse', state.healthData?.sse?.status === 'available');
    
    // Update database status
    updateStatusIndicator('database', state.healthData?.database?.status === 'Connected');
    
    // Update SSL status
    updateStatusIndicator('ssl', state.healthData?.ssl?.valid === true);
    
    // Update uptime
    const appUptimeElement = document.getElementById('app-uptime');
    if (appUptimeElement) {
      appUptimeElement.textContent = formatUptime(state.systemData?.os?.app_uptime || 0);
    }
    
    const systemUptimeElement = document.getElementById('system-uptime');
    if (systemUptimeElement) {
      systemUptimeElement.textContent = formatUptime(state.systemData?.os?.uptime || 0);
    }
  }
  
  function updateStatusIndicator(type, isActive) {
    const indicator = document.querySelector(`[data-status="${type}"]`);
    if (indicator) {
      const dot = indicator.querySelector('.status-dot');
      if (dot) {
        dot.classList.remove('bg-green-500', 'bg-red-500', 'bg-gray-400');
        
        if (isActive === true) {
          dot.classList.add('bg-green-500');
        } else if (isActive === false) {
          dot.classList.add('bg-red-500');
        } else {
          dot.classList.add('bg-gray-400');
        }
      }
    }
  }
  
  function updateResourceMetrics() {
    // Update CPU metrics
    const cpuUsageElement = document.getElementById('cpu-usage');
    if (cpuUsageElement) {
      cpuUsageElement.textContent = state.systemData?.cpu?.usage ? state.systemData.cpu.usage + '%' : 'Loading...';
    }
    
    const cpuCoresElement = document.getElementById('cpu-cores');
    if (cpuCoresElement) {
      cpuCoresElement.textContent = state.systemData?.cpu?.cores || 'N/A';
    }
    
    const cpuTempElement = document.getElementById('cpu-temp');
    if (cpuTempElement) {
      cpuTempElement.textContent = state.systemData?.cpu?.temperature ? state.systemData.cpu.temperature + '°C' : 'N/A';
    }
    
    // Update memory metrics
    const memoryUsageElement = document.getElementById('memory-usage');
    if (memoryUsageElement) {
      memoryUsageElement.textContent = state.systemData?.memory?.percentage ? state.systemData.memory.percentage + '%' : 'Loading...';
    }
    
    const memoryUsedElement = document.getElementById('memory-used');
    if (memoryUsedElement) {
      memoryUsedElement.textContent = formatBytes(state.systemData?.memory?.used || 0);
    }
    
    const memoryTotalElement = document.getElementById('memory-total');
    if (memoryTotalElement) {
      memoryTotalElement.textContent = formatBytes(state.systemData?.memory?.total || 0);
    }
    
    // Update disk metrics
    const diskUsageElement = document.getElementById('disk-usage');
    if (diskUsageElement) {
      diskUsageElement.textContent = state.systemData?.disk?.percentage ? state.systemData.disk.percentage + '%' : 'Loading...';
    }
    
    const diskUsedElement = document.getElementById('disk-used');
    if (diskUsedElement) {
      diskUsedElement.textContent = formatBytes(state.systemData?.disk?.used || 0);
    }
    
    const diskTotalElement = document.getElementById('disk-total');
    if (diskTotalElement) {
      diskTotalElement.textContent = formatBytes(state.systemData?.disk?.total || 0);
    }
  }
  
  function updateDatabaseStatistics() {
    // Update table count
    const tableCountElement = document.getElementById('db-table-count');
    if (tableCountElement) {
      tableCountElement.textContent = state.healthData?.database?.tables?.count || 0;
    }
    
    // Update record count
    const recordCountElement = document.getElementById('db-record-count');
    if (recordCountElement) {
      tableCountElement.textContent = state.healthData?.database?.tables?.total_records || 0;
    }
    
    // Update database size
    const dbSizeElement = document.getElementById('db-size');
    if (dbSizeElement) {
      dbSizeElement.textContent = formatBytes(state.healthData?.database?.size || 0);
    }
    
    // Update last backup
    const lastBackupElement = document.getElementById('db-last-backup');
    if (lastBackupElement) {
      lastBackupElement.textContent = state.healthData?.database?.backup?.last_backup || 'Never';
    }
  }
  
  function updateNetworkInformation() {
    // Update hostname
    const hostnameElement = document.getElementById('network-hostname');
    if (hostnameElement) {
      hostnameElement.textContent = state.systemData?.network?.hostname || 'N/A';
    }
    
    // Update local IP
    const localIpElement = document.getElementById('network-local-ip');
    if (localIpElement) {
      localIpElement.textContent = state.systemData?.network?.local_ip || 'N/A';
    }
    
    // Update public IP
    const publicIpElement = document.getElementById('network-public-ip');
    if (publicIpElement) {
      publicIpElement.textContent = state.systemData?.network?.public_ip || 'N/A';
    }
  }
  
  function updateSystemUI() {
    // Implementation depends on system tab layout
  }
  
  function updateNetworkUI() {
    // Populate form fields with current values
    document.getElementById('unified-ngrok-domain').value = state.systemNetworkData?.unified_config?.ngrok_domain || '';
    document.getElementById('unified-default-ip').value = state.systemNetworkData?.unified_config?.default_ip || '';
    document.getElementById('unified-default-port').value = state.systemNetworkData?.unified_config?.default_port || '8080';
    
    // Update state variables
    state.unifiedNgrokDomain = state.systemNetworkData?.unified_config?.ngrok_domain || '';
    state.unifiedDefaultIp = state.systemNetworkData?.unified_config?.default_ip || '';
    state.unifiedDefaultPort = state.systemNetworkData?.unified_config?.default_port || '8080';
    
    // Update network info display
    document.getElementById('network-info-local-ip').textContent = state.systemNetworkData?.network_info?.local_ip || 'Loading...';
    document.getElementById('network-info-public-ip').textContent = state.systemNetworkData?.network_info?.public_ip || 'Not available';
    document.getElementById('network-info-hostname').textContent = state.systemNetworkData?.network_info?.hostname || 'Unknown';
    document.getElementById('network-info-port').textContent = state.systemNetworkData?.network_info?.default_port || '8080';
    
    // Show the network content now that data is loaded
    document.getElementById('network-loading').classList.add('hidden');
    document.getElementById('network-content').classList.remove('hidden');
  }
  
  function updateDatabaseStatusUI() {
    // Implementation depends on database tab layout
  }
  
  function updateBackupListUI() {
    // Implementation depends on database tab layout
  }
  
  function displayNetworkConfigResult() {
    const resultElement = document.getElementById('network-config-result');
    if (!resultElement || !state.networkConfigurationResult) return;
    
    resultElement.classList.remove('hidden');
    
    if (state.networkConfigurationResult.success) {
      resultElement.classList.add('bg-green-50', 'dark:bg-green-900/20', 'border-green-200', 'dark:border-green-700');
      resultElement.classList.remove('bg-red-50', 'dark:bg-red-900/20', 'border-red-200', 'dark:border-red-700');
    } else {
      resultElement.classList.add('bg-red-50', 'dark:bg-red-900/20', 'border-red-200', 'dark:border-red-700');
      resultElement.classList.remove('bg-green-50', 'dark:bg-green-900/20', 'border-green-200', 'dark:border-green-700');
    }
    
    const messageElement = resultElement.querySelector('.message');
    if (messageElement) {
      messageElement.textContent = state.networkConfigurationResult.message;
    }
    
    // Hide after 5 seconds
    setTimeout(() => {
      resultElement.classList.add('hidden');
    }, 5000);
  }
  
  function displayNetworkDiagnostics() {
    // Implementation depends on network diagnostics layout
  }
  
  // Helper functions for network URLs
  function getIssuerUrl() {
    const useNgrok = state.systemNetworkData?.unified_config?.use_ngrok;
    const ngrokDomain = state.systemNetworkData?.unified_config?.ngrok_domain;
    const defaultIp = state.systemNetworkData?.unified_config?.default_ip;
    const port = state.systemNetworkData?.unified_config?.default_port;
    
    if (useNgrok && ngrokDomain) {
      return `https://${ngrokDomain}`;
    } else {
      const protocol = state.networkSettings?.use_https ? 'https' : 'http';
      return `${protocol}://${defaultIp}:${port}`;
    }
  }
  
  function getVerifierUrl() {
    const useNgrok = state.systemNetworkData?.unified_config?.use_ngrok;
    const ngrokDomain = state.systemNetworkData?.unified_config?.ngrok_domain;
    const defaultIp = state.systemNetworkData?.unified_config?.default_ip;
    const port = state.systemNetworkData?.unified_config?.default_port;
    
    if (useNgrok && ngrokDomain) {
      return `https://${ngrokDomain}/verifier`;
    } 
    //  else {
    //  const protocol = state.networkSettings?.use_https ? 'https' : 'http';
    //  return `${protocol}://${defaultIp}:${port}/verifier`;
   // }
  }
  
  function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
      .then(() => {
        showNotification('Copied to clipboard', 'success');
      })
      .catch(err => {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy to clipboard', 'error');
      });
  }
  
  function isValidNgrokUrl(url) {
    if (!url) return false;
    
    try {
      url = url.trim();
      const urlObj = new URL(url);
      return urlObj.protocol === 'https:' && 
        (url.includes('.ngrok.io') || url.includes('.ngrok-free.app'));
    } catch (e) {
      return false;
    }
  }
  
  // Manual refresh function
  function manualRefresh() {
    switch (state.activeTab) {
      case 'dashboard':
        fetchDashboardData();
        break;
      case 'system':
        fetchSystemData();
        break;
      case 'database':
        loadDatabaseStatus();
        loadBackupList();
        break;
      case 'network':
        fetchNetworkData();
        break;
    }
  }
  
  // Initialize the component
  init();
}); 
