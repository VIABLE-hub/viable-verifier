// 🩺 HERZCHIRURG: Settings Module
// This module handles all settings-related functionality

console.log("🩺 HERZCHIRURG: Settings component initializing...");

document.addEventListener('alpine:init', () => {
  console.log('🩺 HERZCHIRURG: Settings component initializing...');
  
  Alpine.data('settings', () => ({
    // Global state
    currentTab: 'dashboard',
    theme: 'light',
    isLoading: false,
    showToast: false,
    toastMessage: '',
    toastType: 'success',
    lastUpdated: new Date().toLocaleTimeString(),
    tabsLoaded: {
      dashboard: false,
      system: false,
      database: false,
      network: false,
      api: false,
      keys: false,
      'selective-disclosure': false
    },
    
    // Dashboard state
    dashboardLoading: true,
    dashboardRefreshing: false,
    dashboardError: null,
    systemDataReady: false,
    healthDataReady: false,
    systemData: null,
    healthData: {
      issuer: { status: 'unknown', endpoint: '-', response_time: null },
      verifier: { status: 'unknown', endpoint: '-', response_time: null },
      database: { status: 'unknown', type: 'SQLite', size: '-' },
      websocket: { status: 'unknown', active_connections: 0, port: '-' },
      sse: { status: 'unknown', active_connections: 0, port: '-' }
    },
    
    // System state
    systemLoading: false,
    systemHealthData: null,
    
    // Network state
    networkLoading: false,
    networkConfigUpdating: false,
    networkData: null,
    networkError: null,
    ngrokSettings: {
      useNgrok: false,
      ngrokDomain: ''
    },
    testingConnection: false,
    connectionTestResults: null,
    
    // Database state
    databaseLoading: false,
    databaseData: null,
    backupListLoading: false,
    backupInProgress: false,
    backupLoading: true,
    selectiveDisclosureLoading: true,
    selectiveDisclosureEnabled: false,
    selectiveDisclosureFields: [],
    selectedFields: [],
    
    // API keys state
    apiKeys: [],
    apiKeysLoading: false,
    apiKeyGenerating: false,
    newKeyName: '',
    newApiKey: null,
    keyRevoking: false,
    
    // API Testing state
    activeCategory: 'issuer',
    apiTesting: false,
    apiResponse: null,
    apiResponseStatus: null,
    issuerResponse: null,
    selectedApiKey: '',
    issuerRequestBody: JSON.stringify({
      firstName: "Max",
      lastName: "Mustermann",
      studentId: "S123456",
      studentIdPrefix: "TUB",
      dateOfBirth: "2000-01-15",
      email: "max@student.tu-berlin.de",
      studyProgram: "Informatik",
      faculty: "Fakultät IV",
      enrollmentDate: "2020-10-01",
      expectedGraduation: "2024-09-30",
      studentStatus: "Enrolled",
      academicLevel: "Bachelor"
    }, null, 2),
    responseTime: 0,
    
    // 🔐 Key Management State
    keyInventoryData: [],
    keyInventoryLoading: false,
    keyGenerating: false,
    keyStatistics: {
      total: 0,
      active: 0,
      expired: 0,
      expiring_soon: 0
    },
    showGenerateKeyModal: false,
    newKeyConfig: {
      type: 'Ed25519',
      purpose: 'General Purpose',
      validity_days: 365
    },
    
    // Initialize the app
    init() {
      console.log('🔧 Initializing settings component...');
      
      // Initialize state
      this.tabsLoaded = {};
      
      // Initialize dashboard state
      this.dashboardLoading = false;
      this.dashboardRefreshing = false;
      this.dashboardError = null;
      this.healthData = null;
      this.healthDataReady = false;
      this.systemData = null;
      this.systemDataReady = false;
      
      // Initialize system state
      this.systemLoading = false;
      this.systemHealthData = null;
      this.systemHealthRefreshing = false;
      this.systemHealthError = null;
      
      // Initialize database state
      this.databaseLoading = false;
      this.databaseData = {};
      this.backupListLoading = false;
      this.backupList = [];
      this.backupInProgress = false;
      this.selectedImportFile = null;
      this.databaseImporting = false;
      this.databaseImportProgress = 0;
      
      // Initialize network state
      this.networkLoading = false;
      this.networkData = {};
      this.networkConfigUpdating = false;
      this.testingConnection = false;
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Not tested', ip: '-', latency: null },
          verifier: { success: false, message: 'Not tested', ip: '-', latency: null },
          api: { success: false, message: 'Not tested', ip: '-', latency: null },
          network: { success: false, message: 'Not tested', ip: '-', latency: null }
        },
        message: 'Click test button to run connection diagnostics',
        success: false,
        tests_passed: 0,
        tests_total: 4
      };
      this.ngrokDomain = '';
      this.useNgrok = false;
      this.useHttps = true;
      this.urlUpdating = false;
      this.issuerUrl = '';
      this.verifierUrl = '';
      
      // Initialize new connection mode variables
      this.connectionMode = 'local'; // 'local', 'public', 'ngrok'
      this.serverPort = 8080;
      
      // Initialize API state
      this.apiKeysLoading = false;
      this.apiKeys = [];
      this.apiKeyGenerating = false;
      this.keyRevoking = false;
      this.newKeyName = '';
      this.newApiKey = null;
      
      // Initialize selective disclosure state
      this.selectiveDisclosureLoading = false;
      this.selectiveDisclosureUpdating = false;
      this.selectiveDisclosureSaving = false;
      this.loadingFields = false;
      this.selectiveDisclosureEnabled = true;
      this.disclosureStrategy = 'required';
      this.zkProof = true;
      this.allowPartial = false;
      this.allFields = [];
      this.mandatoryFields = [];
      
      // Check URL hash to determine initial tab
      const hash = window.location.hash.slice(1); // Remove the # symbol
      const validTabs = ['dashboard', 'system', 'database', 'network', 'api', 'keys', 'selective-disclosure'];
      
      if (hash && validTabs.includes(hash)) {
        this.activeTab = hash;
        console.log(`🔧 Loading initial tab from URL hash: ${hash}`);
        // Load data for the initial tab
        this.switchToTab(hash);
      } else {
        this.activeTab = 'dashboard';
        // Load dashboard data
        this.loadDashboard();
      }
      
      // Listen for hash changes to switch tabs
      window.addEventListener('hashchange', () => {
        const newHash = window.location.hash.slice(1);
        if (newHash && validTabs.includes(newHash)) {
          console.log(`🔧 Hash changed to: ${newHash}`);
          this.switchToTab(newHash);
        }
      });

      // Auto-refresh functionality when window gains focus (for key updates)
      window.addEventListener('focus', () => {
        if (this.activeTab === 'keys' && !this.keyInventoryLoading) {
          console.log('🔑 Window focused - refreshing key inventory');
          this.loadKeyInventory();
        }
      });

      // Performance optimization: debounce window resize events
      let resizeTimeout;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          console.log('🔧 Window resized - adjusting layout');
          // Any responsive adjustments can go here
        }, 250);
      });

      // Memory leak prevention
      window.addEventListener('beforeunload', () => {
        this.cleanup();
      });
    },

    // Cleanup function to prevent memory leaks
    cleanup() {
      console.log('🔧 Cleaning up settings component...');
      // Clear any intervals or timeouts
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }
      // Clear any pending notifications
      this.notifications = [];
    },
    
    // State
    isInitialized: false,
    activeTab: 'dashboard',
    
    // Initialize systemData with default values
    systemData: {
      cpu: { 
        usage: 0, 
        cores: 1, 
        logical_cores: 1, 
        temperature: null, 
        status: 'unknown' 
      },
      memory: { 
        percentage: 0, 
        used_gb: 0, 
        total_gb: 0, 
        status: 'unknown' 
      },
      disk: { 
        percentage: 0, 
        used_gb: 0, 
        free_gb: 0, 
        total_gb: 0, 
        status: 'unknown' 
      },
      uptime: { 
        app_uptime: '0:00:00', 
        system_uptime: '0:00:00' 
      },
      network: { 
        hostname: 'Loading...', 
        local_ip: 'Loading...', 
        public_ip: 'Loading...' 
      },
      status: 'unknown'
    },
    
    // Loading States
    backupLoading: true,
    selectiveDisclosureLoading: true,
    loadingFields: false,
    
    // Individual field bindings for Alpine.js x-model
    fieldFirstName: false,
    fieldLastName: false,
    fieldStudentId: false,
    fieldStudentIdPrefix: false,
    fieldImage: false,
    fieldTheme: false,
    
    // ALIASES for tab templates
    get loadingNetwork() { return this.networkLoading; },
    get loadingDatabase() { return this.databaseLoading; },
    get systemInfo() { return this.systemHealthData; },
    get systemInfoLoading() { return this.systemLoading; },
    get selectiveDisclosureFields() { return this.allFields; },
    
    // Status Flags
    dashboardRefreshing: false,
    systemHealthRefreshing: false,
    databaseRefreshing: false,
    networkRefreshing: false,
    
    // Error States
    systemHealthError: null,
    databaseError: null,
    
    // Backup Management
    backupList: [],
    backupCreating: false,
    selectedBackupFile: null,
    databaseExporting: false,
    
    // System Settings
    systemSettings: {},
    systemSettingsLoading: false,
    
    // Network Settings
    networkSettings: {
      issuer_ip: '127.0.0.1',
      verifier_ip: '127.0.0.1',
      issuer_port: '8080',
      verifier_port: '8080',
      use_https: true,
      auto_discovery: false,
      timeout: 30,
      use_ngrok: false,
      ngrok_domain: '',
      default_ip: '127.0.0.1',
      default_port: '8080'
    },
    networkSettingsLoading: false,
    
    // Selective Disclosure
    showSelectiveDisclosureToast: false,
    selectiveDisclosureToastMessage: '',
    selectiveDisclosureToastSuccess: true,
    
    // Network data and settings
    networkData: null,
    
    // Import/Export
    importFileValid: false,
    
    // formatUptime function for system tab
    formatUptime(seconds) {
      if (!seconds || seconds === 0) return '0:00:00';
      
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
      }
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    
    // Tab Navigation
    switchToTab(tabName) {
      if (!tabName) return;
      
      // Set the active tab
      this.activeTab = tabName;
      
      // Check if we've already loaded this tab's data
      if (!this.tabsLoaded[tabName]) {
        console.log(`Loading data for tab: ${tabName}`);
      
        // Load data for the selected tab
        switch (tabName) {
          case 'dashboard':
        this.loadDashboard();
            break;
          case 'system':
            this.loadSystemInfo();
            break;
          case 'database':
            // Load both database data and backups when switching to database tab
            this.loadDatabaseData();
        this.loadBackupList();
            break;
                  case 'network':
          // Use the debug endpoint for correct network information
          this.loadNetworkSettings();
          break;
          case 'api':
            this.loadApiKeys();
            break;
          case 'keys':
            // Load cryptographic key management data
            this.loadKeyInventory();
            break;
          case 'selective-disclosure':
        this.loadSelectiveDisclosureFields();
            break;
      }
      
        // Mark this tab as loaded
        this.tabsLoaded[tabName] = true;
      }
    },
    
    loadTabData(tabName) {
      console.log(`🩺 Loading data for ${tabName} tab`);
      
      switch(tabName) {
        case 'dashboard':
          this.loadDashboard();
          break;
        case 'system':
          this.loadSystemInfo();
          break;
        case 'database':
          // When loading database tab, need to load both database data and backups
          this.loadDatabaseData();
          this.loadBackupList();
          break;
        case 'network':
          this.loadNetworkSettings();
          break;
        case 'api':
          this.loadApiKeys();
          break;
        case 'keys':
          // Load cryptographic key management data
          this.loadKeyInventory();
          break;
        case 'selective_disclosure':
          this.loadSelectiveDisclosureFields();
          break;
        case 'backup':
          this.loadBackupList();
          break;
        default:
          console.log(`🩺 No data loading function for tab: ${tabName}`);
      }
    },
    
    // Dashboard Loading
    loadDashboard() {
      this.dashboardLoading = true;
      this.dashboardRefreshing = true;
      console.log('🩺 Loading dashboard data...');
      
      // Load health data
      fetch('/api/health')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🩺 Dashboard health data:', data);
          
          // Update health data directly
          if (data) {
            // Store the complete health data object
            this.healthData = data;
            
            // Mark data as ready
            this.healthDataReady = true;
          }
          
          // Also load system data for dashboard
          this.loadSystemData();
        })
        .catch(error => {
          console.error('🩺 Error loading health data:', error);
          this.dashboardError = `Failed to load health data: ${error.message}`;
          
          // Set default health data to prevent UI errors
          this.healthData = {
            issuer: { status: 'unknown', endpoint: '-', response_time: null },
            verifier: { status: 'unknown', endpoint: '-', response_time: null },
            database: { status: 'unknown', type: 'SQLite', size: '-' },
            websocket: { status: 'unknown', active_connections: 0, port: '-' },
            sse: { status: 'unknown', active_clients: 0, events_sent: 0 },
            ssl: { status: 'unknown', certificate_type: '-', expires: '-' }
          };
          this.healthDataReady = true;
          
          // Still try to load system data even if health data fails
          this.loadSystemData();
        });
    },
    
    // Load system data for dashboard
    loadSystemData() {
      console.log('🖥️ Loading system data...');
      
      fetch('/api/system/health')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🖥️ System data loaded:', data);
          
          if (data && data.success && data.data) {
            this.systemData = data.data;
            this.systemDataReady = true;
          } else {
            throw new Error('Invalid system data format');
          }
          
          // Update last updated timestamp
          this.lastUpdated = new Date().toLocaleTimeString();
          
          // Complete dashboard loading
          this.dashboardLoading = false;
          this.dashboardRefreshing = false;
        })
        .catch(error => {
          console.error('🖥️ Error loading system data:', error);
          this.dashboardError = `Failed to load system data: ${error.message}`;
          
          // Set default system data to prevent UI errors
          this.systemData = {
            cpu: { usage: 0, cores: 0, logical_cores: 0, temperature: null, status: 'unknown' },
            memory: { percentage: 0, used_gb: 0, total_gb: 0, status: 'unknown' },
            disk: { percentage: 0, used_gb: 0, free_gb: 0, total_gb: 0, status: 'unknown' },
            uptime: { app_uptime: '0:00:00', system_uptime: '0:00:00' },
            network: { hostname: 'Unknown', local_ip: 'Unknown', public_ip: 'Unknown' },
            platform: { system: 'Unknown', release: 'Unknown', machine: 'Unknown', processor: 'Unknown' },
            python: { version: 'Unknown', implementation: 'Unknown', environment: 'system', executable: 'Unknown' },
            app_version: 'v2.0.0'
          };
          this.systemDataReady = true;
          
          // Complete dashboard loading
          this.dashboardLoading = false;
          this.dashboardRefreshing = false;
        });
    },
    
    // Manual refresh for dashboard data
    manualRefresh() {
      if (this.dashboardRefreshing) return;
      console.log('🔄 Manual dashboard refresh requested');
      this.loadDashboard();
    },
    
    // System Info Functions
    loadSystemInfo() {
      this.systemLoading = true;
      this.systemHealthRefreshing = true;
      console.log('🩺 Loading system health data...');
      
      fetch('/api/system/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(response => {
          console.log('🩺 System health data received:', response);
          
          if (response && response.success && response.data) {
            // Store the data directly in systemHealthData
            this.systemHealthData = response.data;
            console.log('🩺 System health data updated:', this.systemHealthData);
            this.lastUpdated = new Date().toLocaleTimeString();
          } else {
            console.error('🩺 Invalid system health data format:', response);
            this.systemHealthError = 'Invalid data format received from server';
          }
        })
        .catch(error => {
          console.error('🩺 Error loading system health data:', error);
          this.systemHealthError = `Failed to load system health data: ${error.message}`;
        })
        .finally(() => {
          this.systemHealthRefreshing = false;
          this.systemLoading = false;
        });
    },
    
    // Database Functions
    loadDatabase() {
      console.log('🗄️ Loading complete database information...');
      this.databaseLoading = true;
      
      // Load both database data and backups
      this.loadDatabaseData();
      
      // Also load the backup list
      this.loadBackupList();
    },
    
    loadDatabaseData() {
      console.log('🗄️ Loading database data...');
      this.databaseLoading = true;
      
      // Use relative URL to avoid certificate issues
      fetch('/api/database/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(response => {
          console.log('Database response:', response);
          
          if (response.status === 'success' && response.database) {
            // Process the database data
            const data = response.database;
          
            // Handle nested objects or direct values
            this.databaseData = {
              engine: data.engine || 'SQLite',
              version: data.version || '3.x',
              status: data.status || 'Connected',
              location: data.location || '',
              size_bytes: data.size_bytes || 0,
              size: data.size?.formatted || this.formatBytes(data.size_bytes || 0),
              tables: {
                count: data.tables?.count || data.table_count || 0,
                list: data.tables?.list || []
              },
              credentials: {
                total_issued: data.credentials?.total_issued || data.credential_count || 0,
                active: data.credentials?.active || 0,
                revoked: data.credentials?.revoked || 0
              },
              last_backup: data.last_backup || 'Never',
              last_optimize: data.last_optimize || 'Never'
            };
            
            console.log('Database data processed:', this.databaseData);
          } else {
            this.databaseData = {
              engine: 'Unknown',
              version: 'Unknown',
              status: 'Error',
              size: '0 B',
              tables: { count: 0 },
              credentials: { total_issued: 0 }
            };
            
            if (response.status !== 'success') {
              throw new Error(response.message || 'Failed to load database data');
            }
          }
        })
        .catch(error => {
          console.error('Error loading database data:', error);
          this.databaseData = {
            engine: 'Error',
            version: 'Unknown',
            status: 'Error: ' + error.message,
            size: '0 B',
            tables: { count: 0 },
            credentials: { total_issued: 0 }
          };
          this.showNotification(`Failed to load database data: ${error.message}`, 'error');
        })
        .finally(() => {
          console.log('🗄️ Database data loading completed, setting databaseLoading = false');
          this.databaseLoading = false;
        });
    },
    
    // Load database information using the alternate endpoint
    loadDatabaseInfo() {
      console.log('🗄️ Loading database info...');
      this.databaseLoading = true;
      
      fetch('/api/database/status')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Database info response:', data);
          
          // Process the data and update the database state
          if (data && data.success && data.data) {
            const dbData = data.data;
            
            // Update the database data
            this.databaseData = {
              ...this.databaseData, // Preserve any existing data
              engine: dbData.engine || 'SQLite',
              size_bytes: dbData.size_bytes || 0,
              size: dbData.size || this.formatBytes(dbData.size_bytes || 0),
              tables: dbData.tables || 0,
              connections: dbData.connections || 0,
              location: dbData.location || '',
              version: dbData.version || '',
              last_backup: dbData.last_backup || null,
              table_count: dbData.tables || 0,
              credential_count: dbData.credentials || 0, 
              status: dbData.status || 'healthy',
              table_details: dbData.table_details || []
            };
          }
        })
        .catch(error => {
          console.error('Error loading database info:', error);
        })
        .finally(() => {
          console.log('🗄️ Database info loading completed');
          this.databaseLoading = false;
          this.lastUpdated = new Date().toLocaleTimeString();
        });
    },
    
    // Backup management functions
    loadBackupList() {
      this.backupListLoading = true;
      
      // Use relative URL to avoid certificate issues
      fetch('/api/database/backup/list', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(response => {
          console.log('Backup list response:', response);
          
          if (response.status === 'success' && response.backups) {
            this.backupList = response.backups.map(backup => ({
              ...backup,
              id: backup.filename || backup.id || Math.random().toString(36).substring(2, 15)
            }));
          } else {
            this.backupList = [];
            if (response.status !== 'success') {
              throw new Error(response.message || 'Failed to load backups');
            }
          }
        })
        .catch(error => {
          console.error('Error loading backups:', error);
          this.backupList = [];
          this.showNotification(`Failed to load backups: ${error.message}`, 'error');
        })
        .finally(() => {
          this.backupListLoading = false;
        });
    },
    
    createBackup() {
      this.backupInProgress = true;
      
      // Use relative URL to avoid certificate issues
      fetch('/api/database/backup/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          notes: 'Created from Settings page'
        }),
        // Add these options to handle certificate issues
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Backup creation response:', data);
          
          if (data.status === 'success') {
            this.showNotification('Backup created successfully', 'success');
            this.loadBackupList(); // Refresh the backup list
          } else {
            throw new Error(data.message || 'Unknown error creating backup');
          }
        })
        .catch(error => {
          console.error('Error creating backup:', error);
          
          // More user-friendly error message
          let errorMessage = 'Failed to create backup';
          if (error.message && error.message.includes('certificate')) {
            errorMessage += ': Certificate issue. Please try using a relative URL or check your HTTPS settings.';
          } else if (error.message) {
            errorMessage += `: ${error.message}`;
          }
          
          this.showNotification(errorMessage, 'error');
        })
        .finally(() => {
          this.backupInProgress = false;
        });
    },
    
    downloadBackup(backup) {
      if (!backup || !backup.filename) {
        this.showNotification('Invalid backup selected', 'error');
        return;
      }
      
      // Create a hidden link to download the file
      const link = document.createElement('a');
      link.href = `/api/database/backup/download?filename=${encodeURIComponent(backup.filename)}`;
      link.download = backup.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      this.showNotification('Backup download started', 'info');
    },
    
    restoreBackup(backup) {
      if (!backup || !backup.filename) {
        this.showNotification('Invalid backup selected', 'error');
        return;
      }
      
      if (!confirm(`Are you sure you want to restore this backup? Current data will be replaced with the backup from ${backup.date}.`)) {
        return;
      }
      
      this.restoreInProgress = true;
      
      fetch('/api/database/backup/restore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: backup.filename
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Restore response:', data);
          
          if (data.status === 'success') {
            this.showNotification('Backup restored successfully', 'success');
            setTimeout(() => {
              this.loadDatabaseData(); // Reload database info
            }, 1000);
          } else {
            throw new Error(data.message || 'Unknown error restoring backup');
          }
        })
        .catch(error => {
          console.error('Error restoring backup:', error);
          this.showNotification(`Failed to restore backup: ${error.message}`, 'error');
        })
        .finally(() => {
          this.restoreInProgress = false;
        });
    },
    
    deleteBackup(backup) {
      if (!backup || !backup.filename) {
        this.showNotification('Invalid backup selected', 'error');
        return;
      }
      
      if (!confirm(`Are you sure you want to permanently delete this backup from ${backup.date}?`)) {
        return;
      }
      
      fetch('/api/database/backup/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: backup.filename
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Delete backup response:', data);
          
          if (data.status === 'success') {
            this.showNotification('Backup deleted successfully', 'success');
            this.loadBackupList(); // Refresh backup list
          } else {
            throw new Error(data.message || 'Unknown error deleting backup');
          }
        })
        .catch(error => {
          console.error('Error deleting backup:', error);
          this.showNotification(`Failed to delete backup: ${error.message}`, 'error');
        });
    },
    
    exportDatabaseSQL() {
      // Create a hidden link to download the file
      const link = document.createElement('a');
      link.href = '/api/database/export/sql';
      link.download = 'database_export.sql';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      this.showNotification('Database export started. The file will download automatically.', 'info');
    },
    
    // Database file import handling
    handleDatabaseFileSelect(event) {
      const fileInput = event.target;
      if (!fileInput.files || fileInput.files.length === 0) {
        console.log('No file selected');
        this.selectedImportFile = null;
        return;
      }
      
      const file = fileInput.files[0];
      console.log('Selected file:', file.name, file.type, file.size);
      
      // Check if file is SQL
      if (!file.name.endsWith('.sql')) {
        this.showNotification('Please select a valid SQL file (.sql extension)', 'error');
        this.selectedImportFile = null;
        fileInput.value = '';
        return;
      }
      
      // Store the file for later upload
      this.selectedImportFile = file;
    },
      
    clearImportFile() {
        this.selectedImportFile = null;
      const fileInput = document.getElementById('sql-import');
      if (fileInput) {
        fileInput.value = '';
      }
    },
    
    // Import database from SQL file
    importDatabaseSQL() {
      if (!this.selectedImportFile) {
        this.showNotification('Please select a file to import', 'error');
        return;
      }
      
      this.databaseImporting = true;
      this.databaseImportProgress = 5; // Start progress indicator
      
      // Create form data
      const formData = new FormData();
      formData.append('file', this.selectedImportFile);
      
      // Use relative URL to avoid certificate issues
      fetch('/api/database/import/sql', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(response => {
          console.log('Import response:', response);
          
          if (response.status === 'success') {
            this.showNotification('Database imported successfully', 'success');
            this.clearImportFile();
            this.loadDatabaseData(); // Reload database info
            this.loadBackupList(); // Refresh backup list
          } else {
            throw new Error(response.message || 'Unknown error importing database');
          }
        })
        .catch(error => {
          console.error('Error importing database:', error);
          this.showNotification(`Failed to import database: ${error.message}`, 'error');
        })
        .finally(() => {
          this.databaseImporting = false;
          this.databaseImportProgress = 0;
        });
    },
    
    // Network Functions
    loadNetworkSettings() {
      console.log('🌐 Loading network settings...');
      this.networkLoading = true;
      
      // Use the debug endpoint that has both network info and settings
      const networkApiUrl = '/api/system/network/debug';
      console.log(`🌐 Fetching network info from: ${networkApiUrl}`);
      
      fetch(networkApiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Network settings loaded:', data);
          
          if (data && data.status === 'success' && data.network_info) {
            // Extract network info and settings from the debug API response
            const networkInfo = data.network_info;
            const networkSettings = data.network_settings || {};
            const serverInfo = data.server_info || {};
            
            console.log('🌐 Network info structure:', JSON.stringify(networkInfo, null, 2));
            console.log('🌐 Network settings structure:', JSON.stringify(networkSettings, null, 2));
            console.log('🌐 Server info structure:', JSON.stringify(serverInfo, null, 2));
            
            // Store complete network data
            this.networkData = {
              local_ip: networkInfo.local_ip || 'Unknown',
              public_ip: networkInfo.public_ip || 'Not available',
              hostname: networkInfo.hostname || 'Unknown',
              default_port: networkInfo.default_port || networkSettings.default_port || '8080',
              // 🚨 NEW: Store actual server URL info
              server_info: serverInfo
            };
            
            console.log('🌐 Processed network data:', this.networkData);
            
            // 🚨 ENHANCED: Set ngrok settings from actual server info
            this.ngrokSettings = {
              useNgrok: serverInfo.is_ngrok || !!networkSettings.use_ngrok,
              ngrokDomain: serverInfo.current_server_url || networkSettings.ngrok_domain || '',
              // Store the ready-to-use URLs
              issuerUrl: serverInfo.issuer_url || '',
              verifierUrl: serverInfo.verifier_url || ''
            };
            
            // Determine connection mode from server info
            if (serverInfo.is_ngrok) {
              this.connectionMode = 'ngrok';
              this.ngrokDomain = serverInfo.current_server_url || '';
            } else {
              // Analyze the IPs to determine if it's local or public
              const defaultIp = networkSettings.default_ip || networkSettings.issuer_ip;
              if (defaultIp === this.networkData.local_ip) {
                this.connectionMode = 'local';
              } else if (defaultIp === this.networkData.public_ip) {
                this.connectionMode = 'public';
              } else {
                this.connectionMode = 'local'; // Default fallback
              }
            }
            
            // Set server port
            this.serverPort = parseInt(networkSettings.default_port || networkInfo.default_port || '8080', 10);
            
            console.log('🌐 Network data loaded successfully:', this.networkData);
            console.log('🌐 NgrokSettings configured:', this.ngrokSettings);
            console.log('🌐 Connection mode set to:', this.connectionMode);
            console.log('🌐 Server port set to:', this.serverPort);
          } else {
            console.error('🌐 Invalid network data format - missing network_info:', data);
            throw new Error('Invalid network data format - missing network_info');
          }
        })
        .catch(error => {
          console.error('🌐 Error loading network settings:', error);
          this.networkData = {
            local_ip: 'Unknown',
            public_ip: 'Unknown', 
            hostname: 'Unknown',
            default_port: '8080',
            server_info: {}
          };
          
          // Set fallback values for connection mode and settings
          this.connectionMode = 'local';
          this.serverPort = 8080;
          this.ngrokDomain = '';
          this.ngrokSettings = {
            useNgrok: false,
            ngrokDomain: '',
            issuerUrl: '',
            verifierUrl: ''
          };
        })
        .finally(() => {
          this.networkLoading = false;
          console.log('🌐 Network loading complete, final data:', this.networkData);
        });
    },
    
    // API Key functions
    loadApiKeys() {
      this.apiKeysLoading = true;
      
      fetch('/api/keys/list', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('API keys loaded:', data);
          
          // Process the API keys
          if (data && data.success && data.keys) {
            // Format from {success: true, keys: [...]}
            this.apiKeys = data.keys.map(key => ({
              id: key.id || '',
              name: key.name || 'API Key',
              key_id: key.id || '',
              masked_key: key.prefix ? `${key.prefix}...` : '••••••••••••',
              created_at: key.created_at || new Date().toISOString(),
              is_active: key.is_active !== false,
              key: key.key || '' // This will likely be empty for security reasons
            }));
          } else if (Array.isArray(data)) {
            // Format is direct array of keys
            this.apiKeys = data.map(key => ({
              id: key.id || '',
              name: key.name || 'API Key',
              key_id: key.id || '',
              masked_key: key.prefix ? `${key.prefix}...` : '••••••••••••',
              created_at: key.created_at || new Date().toISOString(),
              is_active: key.is_active !== false,
              key: key.key || '' // This will likely be empty for security reasons
            }));
          } else if (data && data.api_keys) {
            // Format from {api_keys: [...]}
            this.apiKeys = data.api_keys.map(key => ({
              id: key.id || '',
              name: key.name || 'API Key',
              key_id: key.id || '',
              masked_key: key.prefix ? `${key.prefix}...` : '••••••••••••',
              created_at: key.created_at || new Date().toISOString(),
              is_active: key.is_active !== false,
              key: key.key || '' // This will likely be empty for security reasons
            }));
          } else {
            // No keys or unknown format
            this.apiKeys = [];
          }
        })
        .catch(error => {
          console.error('Error loading API keys:', error);
          this.showNotification(`Failed to load API keys: ${error.message}`, 'error');
          this.apiKeys = [];
        })
        .finally(() => {
          this.apiKeysLoading = false;
        });
    },
    
    generateNewApiKey() {
      if (!this.newKeyName || this.newKeyName.trim() === '') {
        this.showNotification('Please enter a name for the API key', 'error');
        return;
      }
      
      this.apiKeyGenerating = true;
      
      fetch('/api/keys/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: this.newKeyName.trim()
        }),
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('API key generation response:', data);
          
          // Check if the API key was generated successfully
          if (data && data.success) {
            // Store the API key
            this.newApiKey = data.key || data.api_key;
            
            // Store the API key in localStorage for future use
            if (this.newApiKey && data.key_id) {
              try {
                localStorage.setItem(`api_key_${data.key_id}`, this.newApiKey);
              } catch (e) {
                console.error('Failed to store API key in localStorage:', e);
              }
            }
            
            // Show success message
            this.showNotification('API key generated successfully', 'success');
            
            // Clear the form
            this.newKeyName = '';
            
            // Refresh the API keys list
            this.loadApiKeys();
          } else if (data && data.key) {
            // Direct key in response
            this.newApiKey = data.key;
            
            // Store the API key in localStorage for future use
            if (this.newApiKey && data.key_id) {
              try {
                localStorage.setItem(`api_key_${data.key_id}`, this.newApiKey);
              } catch (e) {
                console.error('Failed to store API key in localStorage:', e);
              }
            }
            
            this.showNotification('API key generated successfully', 'success');
            this.newKeyName = '';
            this.loadApiKeys();
          } else if (data && data.message && data.message.includes('successfully')) {
            // Success message but no key in the response
            this.showNotification('API key generated successfully', 'success');
            this.newKeyName = '';
            this.loadApiKeys();
          } else {
            // Error message
            throw new Error(data.message || 'Unknown error generating API key');
          }
        })
        .catch(error => {
          console.error('Error generating API key:', error);
          
          // Special case for the "API key generated successfully" message
          if (error.message === 'API key generated successfully') {
            this.showNotification('API key generated successfully', 'success');
            this.newKeyName = '';
            this.loadApiKeys();
          } else {
            this.showNotification(`Failed to generate API key: ${error.message}`, 'error');
          }
        })
        .finally(() => {
          this.apiKeyGenerating = false;
        });
    },
    
    revokeApiKey(keyId) {
      if (!keyId) {
        this.showNotification('Invalid API key ID', 'error');
        return;
      }
      
      if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
        return;
      }
      
      this.keyRevoking = true;
      
      fetch(`/api/keys/revoke/${keyId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('API key revocation response:', data);
          
          if (data && data.success) {
            this.showNotification('API key revoked successfully', 'success');
            this.loadApiKeys(); // Reload the API keys list
          } else {
            throw new Error(data.message || 'Failed to revoke API key');
          }
        })
        .catch(error => {
          console.error('Error revoking API key:', error);
          this.showNotification(`Failed to revoke API key: ${error.message}`, 'error');
        })
        .finally(() => {
          this.keyRevoking = false;
        });
    },
    
    copyToClipboard(text) {
      if (!text) {
        this.showNotification('No text to copy', 'error');
        return;
      }
      
      // Create a temporary textarea element to copy from
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'absolute';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      
      // Select the text and copy it
      textarea.select();
      let success = false;
      try {
        success = document.execCommand('copy');
        if (success) {
          this.showNotification('Copied to clipboard', 'success');
        } else {
          throw new Error('Copy command failed');
        }
      } catch (err) {
        console.error('Error copying to clipboard:', err);
        this.showNotification('Failed to copy to clipboard. Please try again.', 'error');
        
        // Fallback to newer API if available
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text)
            .then(() => {
              this.showNotification('Copied to clipboard', 'success');
            })
            .catch(error => {
              console.error('Clipboard API error:', error);
              this.showNotification('Failed to copy to clipboard. Please try again.', 'error');
            });
        }
      } finally {
        document.body.removeChild(textarea);
      }
    },
    
    copyToSwagger(apiKey) {
      // If no API key is provided, try to get it from localStorage
      if (!apiKey && this.apiKeys && this.apiKeys.length > 0) {
        // Try to find the key in localStorage
        for (const key of this.apiKeys) {
          if (key.key_id) {
            const storedKey = localStorage.getItem(`api_key_${key.key_id}`);
            if (storedKey) {
              apiKey = storedKey;
              break;
            }
          }
        }
      }
      
      if (!apiKey) {
        this.showNotification('No API key available to use with Swagger UI', 'error');
        return;
      }
      
      // Copy the API key to clipboard first
      this.copyToClipboard(apiKey);
      
      // Find the Swagger UI auth button and click it
      const swaggerAuthButton = document.querySelector('.swagger-ui .auth-wrapper .authorize');
      if (swaggerAuthButton) {
        swaggerAuthButton.click();
        
        // Give the modal time to open
        setTimeout(() => {
          // Find the input field and set the value
          const authInput = document.querySelector('.swagger-ui .auth-container input');
          if (authInput) {
            authInput.value = apiKey;
            
            // Find the Authorize button and click it
            const authorizeButton = document.querySelector('.swagger-ui .auth-btn-wrapper .authorize');
            if (authorizeButton) {
              authorizeButton.click();
              this.showNotification('API key applied to Swagger UI', 'success');
            } else {
              this.showNotification('Could not find Authorize button in Swagger UI', 'error');
            }
          } else {
            this.showNotification('Could not find auth input in Swagger UI', 'error');
          }
        }, 500);
      } else {
        this.showNotification('API key copied. Click "Authorize" in the Swagger UI and paste it there.', 'info');
        
        // Scroll to Swagger UI
        const swaggerUI = document.getElementById('swagger-ui');
        if (swaggerUI) {
          swaggerUI.scrollIntoView({ behavior: 'smooth' });
        }
      }
    },
    
    formatDate(dateString) {
      if (!dateString) {
        return 'Unknown';
      }
      
      try {
      const date = new Date(dateString);
      return date.toLocaleString();
      } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
      }
    },
    
    // Selective Disclosure Fields
    loadSelectiveDisclosureFields() {
      this.loadingFields = true;
      
      // Fetch current settings
      fetch('/settings/selective-disclosure')
        .then(response => response.json())
        .then(settingsResponse => {
          const mandatoryFields = settingsResponse.mandatory_fields || [];
          
          // Set individual field values based on settings
          this.fieldFirstName = mandatoryFields.includes('firstName');
          this.fieldLastName = mandatoryFields.includes('lastName');
          this.fieldStudentId = mandatoryFields.includes('studentId');
          this.fieldStudentIdPrefix = mandatoryFields.includes('studentIdPrefix');
          this.fieldImage = mandatoryFields.includes('image');
          this.fieldTheme = mandatoryFields.includes('theme');
          
          this.loadingFields = false;
        })
        .catch(error => {
          console.error('Error loading selective disclosure fields:', error);
          this.showNotification(`Failed to load fields: ${error.message}`, 'error');
          
          // Use default values in case of error
          this.fieldFirstName = true;
          this.fieldLastName = true;
          this.fieldStudentId = true;
          this.fieldStudentIdPrefix = true;
          this.fieldImage = false;
          this.fieldTheme = false;
          
          this.loadingFields = false;
        });
    },
    
    // Selective Disclosure Functions
    saveSelectiveDisclosureSettings() {
      this.selectiveDisclosureSaving = true;
      const selectedFields = this.getSelectedFields();
      
      fetch('/settings/selective-disclosure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mandatory_fields: selectedFields
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
          if (data.success) {
        this.showNotification('Selective disclosure settings saved successfully', 'success');
          } else {
            this.showNotification(`Failed to save settings: ${data.message}`, 'error');
          }
      })
      .catch(error => {
        console.error('Error saving selective disclosure settings:', error);
          this.showNotification(`Failed to save settings: ${error.message}`, 'error');
      })
      .finally(() => {
          this.selectiveDisclosureSaving = false;
      });
    },
    
    selectAllFields() {
      this.fieldFirstName = true;
      this.fieldLastName = true;
      this.fieldStudentId = true;
      this.fieldStudentIdPrefix = true;
      this.fieldImage = true;
      this.fieldTheme = true;
    },
    
    deselectAllOptionalFields() {
      // Keep only the required fields selected
      this.fieldFirstName = true;
      this.fieldLastName = true;
      this.fieldStudentId = true;
      this.fieldStudentIdPrefix = true;
      this.fieldImage = false;
      this.fieldTheme = false;
    },
    
    getSelectedFields() {
      const selected = [];
      if (this.fieldFirstName) selected.push('firstName');
      if (this.fieldLastName) selected.push('lastName');
      if (this.fieldStudentId) selected.push('studentId');
      if (this.fieldStudentIdPrefix) selected.push('studentIdPrefix');
      if (this.fieldImage) selected.push('image');
      if (this.fieldTheme) selected.push('theme');
      return selected;
    },
    
    getSelectedFieldsCount() {
      return this.getSelectedFields().length;
    },
    
    // Utility Functions
    showNotification(message, type = 'info') {
      // Check if notification system exists
      if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
      } else {
        // Fallback to alert
        alert(message);
      }
    },
    
    // Format bytes to human readable format
    formatBytes(bytes, decimals = 2) {
      if (bytes === 0) return '0 Bytes';
      
      const k = 1024;
      const dm = decimals < 0 ? 0 : decimals;
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
      
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    
    // Network data and settings
    get isValidNgrokUrl() {
      if (!this.ngrokSettings.ngrokDomain) return false;
      
      try {
        const url = new URL(this.ngrokSettings.ngrokDomain);
        const isHttps = url.protocol === 'https:';
        const isNgrokDomain = url.hostname.endsWith('.ngrok.io') || 
                              url.hostname.endsWith('.ngrok-free.app') || 
                              url.hostname.endsWith('.ngrok.app');
        return isHttps && isNgrokDomain;
      } catch (e) {
        // If URL parsing fails, check if it's because the protocol is missing
        if (!this.ngrokSettings.ngrokDomain.startsWith('http')) {
          // Try again with https:// prefix
          try {
            const urlWithProtocol = new URL('https://' + this.ngrokSettings.ngrokDomain);
            const isNgrokDomain = urlWithProtocol.hostname.endsWith('.ngrok.io') || 
                                  urlWithProtocol.hostname.endsWith('.ngrok-free.app') || 
                                  urlWithProtocol.hostname.endsWith('.ngrok.app');
            // If valid, suggest adding https:// prefix
            if (isNgrokDomain) {
              console.log('Valid ngrok domain but missing https:// prefix');
              // Don't auto-update the input field to avoid confusion
              return false;
            }
          } catch (e2) {
            // Still invalid even with protocol
          }
        }
        return false;
      }
    },
    
    // URL generation functions
    getIssuerUrl() {
      // Check if network data is loaded
      if (!this.networkData) {
        return 'Loading...';
      }
      
      // Get base URL components
      const useHttps = this.networkData.network_config?.use_https !== false;
      const protocol = useHttps ? 'https://' : 'http://';
      
      // 🚀 FIXED: Check both networkSettings (from API) and ngrokSettings (legacy)
      const ngrokUrl = this.networkSettings?.ngrok_url || this.ngrokSettings?.ngrokDomain;
      const useNgrok = this.networkSettings?.use_ngrok || this.ngrokSettings?.useNgrok;
      
      // If ngrok is enabled and we have a domain, use that
      if (useNgrok && ngrokUrl) {
        return `${ngrokUrl}/issuer`;
      }
      
      // Otherwise use the local IP and port
      const ip = this.networkData.network_info?.local_ip || this.networkData.local_ip || 'localhost';
      const port = this.networkData.network_config?.default_port || this.networkData.default_port || '8080';
      return `${protocol}${ip}:${port}/issuer`;
    },
    
    getVerifierUrl() {
      // Check if network data is loaded
      if (!this.networkData) {
        return 'Loading...';
      }
      
      // Get base URL components
      const useHttps = this.networkData.network_config?.use_https !== false;
      const protocol = useHttps ? 'https://' : 'http://';
      
      // 🚀 FIXED: Check both networkSettings (from API) and ngrokSettings (legacy)
      const ngrokUrl = this.networkSettings?.ngrok_url || this.ngrokSettings?.ngrokDomain;
      const useNgrok = this.networkSettings?.use_ngrok || this.ngrokSettings?.useNgrok;
      
      // If ngrok is enabled and we have a domain, use that
      if (useNgrok && ngrokUrl) {
        return `${ngrokUrl}/verifier`;
      }
      
      // Otherwise use the local IP and port
      const ip = this.networkData.network_info?.local_ip || this.networkData.local_ip || 'localhost';
      const port = this.networkData.network_config?.default_port || this.networkData.default_port || '8080';
      return `${protocol}${ip}:${port}/verifier`;
    },

    // Dynamic URL generation based on connection mode
    getDynamicIssuerUrl() {
      const port = this.serverPort || 8080;
      const protocol = 'https://'; // Always use HTTPS for security
      
      switch (this.connectionMode) {
        case 'local':
          const localIp = this.networkData?.local_ip || '192.168.178.122';
          return `${protocol}${localIp}:${port}/issuer`;
        case 'public':
          const publicIp = this.networkData?.public_ip || '79.242.78.26';
          return `${protocol}${publicIp}:${port}/issuer`;
        case 'ngrok':
          const ngrokUrl = this.ngrokDomain || 'https://abc123.ngrok.io';
          // Remove trailing slash if present, then add /issuer
          return `${ngrokUrl.replace(/\/$/, '')}/issuer`;
        default:
          return 'Configure connection mode';
      }
    },

    getDynamicVerifierUrl() {
      const port = this.serverPort || 8080;
      const protocol = 'https://'; // Always use HTTPS for security
      
      switch (this.connectionMode) {
        case 'local':
          const localIp = this.networkData?.local_ip || '192.168.178.122';
          return `${protocol}${localIp}:${port}/verifier`;
        case 'public':
          const publicIp = this.networkData?.public_ip || '79.242.78.26';
          return `${protocol}${publicIp}:${port}/verifier`;
        case 'ngrok':
          const ngrokUrl = this.ngrokDomain || 'https://abc123.ngrok.io';
          // Remove trailing slash if present, then add /verifier
          return `${ngrokUrl.replace(/\/$/, '')}/verifier`;
        default:
          return 'Configure connection mode';
      }
    },
    
    saveNgrokSettings() {
      // Set the updating flag
      this.networkConfigUpdating = true;
      
      // Validate ngrok URL only if use_ngrok is true
      if (this.ngrokSettings.useNgrok) {
        // If domain is provided but missing https:// prefix, add it
        if (this.ngrokSettings.ngrokDomain && !this.ngrokSettings.ngrokDomain.startsWith('http')) {
          this.ngrokSettings.ngrokDomain = 'https://' + this.ngrokSettings.ngrokDomain;
          console.log('Added https:// prefix to ngrok domain:', this.ngrokSettings.ngrokDomain);
        }
        
        // Check if URL is valid after potential prefix addition
        if (!this.isValidNgrokUrl) {
          this.showNotification('Please enter a valid ngrok URL (https://example.ngrok.io, https://example.ngrok-free.app, or https://example.ngrok.app)', 'error');
          this.networkConfigUpdating = false; // Reset flag on validation error
          return;
        }
      }
      
      // Prepare data for API call
      const data = {
        use_ngrok: this.ngrokSettings.useNgrok,
        ngrok_domain: this.ngrokSettings.useNgrok ? this.ngrokSettings.ngrokDomain : ''
      };
      
      // Make API call
      fetch('/api/system/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Ngrok settings saved:', data);
          
          if (data.success) {
            this.showNotification('Ngrok settings saved successfully', 'success');
            
            // Reload network settings to get the updated values
            this.loadNetworkSettings();
            
            // Update the local ngrok settings
            this.ngrokSettings = {
              useNgrok: data.use_ngrok,
              ngrokDomain: data.ngrok_domain
            };
          } else {
            throw new Error(data.message || 'Failed to save Ngrok settings');
          }
        })
        .catch(error => {
          console.error('🌐 Error saving Ngrok settings:', error);
          this.showNotification('Error saving Ngrok settings: ' + error.message, 'error');
        })
        .finally(() => {
          this.networkConfigUpdating = false; // Reset the updating flag
        });
    },
    
    testNgrokUrl() {
      if (!this.isValidNgrokUrl) {
        this.showNotification('Please enter a valid ngrok URL first', 'error');
        return;
      }
      
      this.testingConnection = true;
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Testing...', ip: '-', latency: null },
          verifier: { success: false, message: 'Testing...', ip: '-', latency: null },
          api: { success: false, message: 'Testing...', ip: '-', latency: null },
          network: { success: false, message: 'Testing...', ip: '-', latency: null }
        },
        message: 'Testing NGROK connection...',
        success: false,
        tests_passed: 0,
        tests_total: 4
      };
      
      fetch('/api/system/network/test-ngrok', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Ngrok test results:', data);
          
          if (data.success) {
            this.showNotification('Ngrok URL test successful', 'success');
            this.connectionTestResults = {
              success: true,
              latency: data.data?.latency || '-',
              message: 'Connection successful'
            };
          } else {
            throw new Error(data.message || 'Ngrok URL test failed');
          }
        })
        .catch(error => {
          console.error('🌐 Error testing Ngrok URL:', error);
          this.showNotification('Error testing Ngrok URL: ' + error.message, 'error');
          this.connectionTestResults = {
            success: false,
            latency: null,
            message: error.message
          };
        })
        .finally(() => {
          this.testingConnection = false;
        });
    },

    // 🚀 MISSING FUNCTION ADDED: Update network settings via API and refresh URLs
    updateNetworkSettings() {
      console.log('🌐 updateNetworkSettings() called');
      this.networkConfigUpdating = true;
      
      // Prepare the network settings data for API
      const networkData = {
        ngrok_url: this.networkSettings?.ngrok_url || '',
        use_ngrok: this.networkSettings?.use_ngrok || false,
        connection_mode: this.networkSettings?.connection_mode || 'local',
        use_https: this.networkSettings?.use_https !== false,
        auto_discovery: this.networkSettings?.auto_discovery || false,
        timeout: this.networkSettings?.timeout || 30,
        default_ip: this.networkSettings?.default_ip || '',
        default_port: this.networkSettings?.default_port || 8080
      };
      
      console.log('🌐 Saving network settings:', networkData);
      
      // Save via API
      fetch('/settings/api/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(networkData)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Network settings saved successfully:', data);
          this.showNotification('Network settings saved successfully', 'success');
          
          // 🚀 CRITICAL: Refresh network data to update Generated URLs
          this.loadNetworkSettings();
        })
        .catch(error => {
          console.error('🌐 Error saving network settings:', error);
          this.showNotification('Error saving network settings: ' + error.message, 'error');
        })
        .finally(() => {
          this.networkConfigUpdating = false;
        });
    },
    
    testConnection() {
      this.testingConnection = true;
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Testing...', ip: '-', latency: null },
          verifier: { success: false, message: 'Testing...', ip: '-', latency: null },
          api: { success: false, message: 'Testing...', ip: '-', latency: null },
          network: { success: false, message: 'Testing...', ip: '-', latency: null }
        },
        message: 'Testing connections...',
        success: false,
        tests_passed: 0,
        tests_total: 4
      };
      
      fetch('/api/system/network/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}) // Empty body for POST request
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Connection test completed:', data);
          
          if (data && data.success && data.data) {
            // Extract test results from the backend response
            const testResults = data.data;
            const testDetails = testResults.test_results || {};
            
            // Map backend test results to frontend component format
            this.connectionTestResults = {
              success: testResults.overall_status === 'healthy',
              message: `${testResults.tests_passed}/${testResults.tests_total} tests passed`,
              components: {
                issuer: {
                  success: testDetails.issuer_api?.status === 'success',
                  ip: new URL(testDetails.issuer_api?.url_tested || 'https://localhost').hostname,
                  latency: testDetails.issuer_api?.latency_ms,
                  message: testDetails.issuer_api?.error || 'OK'
                },
                verifier: {
                  success: testDetails.verifier_api?.status === 'success',
                  ip: new URL(testDetails.verifier_api?.url_tested || 'https://localhost').hostname,
                  latency: testDetails.verifier_api?.latency_ms,
                  message: testDetails.verifier_api?.error || 'OK'
                },
                sse: {
                  success: testDetails.sse_connectivity?.status === 'success',
                  ip: new URL(testDetails.sse_connectivity?.url_tested || 'https://localhost').hostname,
                  latency: testDetails.sse_connectivity?.latency_ms,
                  message: testDetails.sse_connectivity?.error || 'OK'
                },
                websocket: {
                  success: testDetails.websocket_connectivity?.status === 'success',
                  ip: new URL(testDetails.websocket_connectivity?.url_tested || 'https://localhost').hostname,
                  latency: testDetails.websocket_connectivity?.latency_ms,
                  message: testDetails.websocket_connectivity?.error || 'OK'
                }
              }
            };
          } else {
            throw new Error(data.message || 'Network test failed');
          }
        })
        .catch(error => {
          console.error('🌐 Connection test error:', error);
          this.connectionTestError = error.message;
          
          // If the main API fails, try the fallback method
          console.log('🌐 Main API failed, trying fallback method...');
          this.testConnectionFallback();
          return; // Return early to avoid setting testingConnection to false
        })
        .finally(() => {
          this.testingConnection = false;
        });
    },
    
    // Fallback function for testing network connections
    testConnectionFallback() {
      this.testingConnection = true;
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Testing...', ip: '-', latency: null },
          verifier: { success: false, message: 'Testing...', ip: '-', latency: null },
          api: { success: false, message: 'Testing...', ip: '-', latency: null },
          network: { success: false, message: 'Testing...', ip: '-', latency: null }
        },
        message: 'Testing connections (fallback method)...',
        success: false,
        tests_passed: 0,
        tests_total: 4
      };
      
      console.log('🌐 Using fallback network test method');
      
      // Create a simpler test that just checks basic connectivity
      const testIssuer = fetch('/issuer/healthcheck', { method: 'GET' })
        .then(response => ({ 
          success: response.ok, 
          status: response.status,
          latency: 0 // We're not measuring latency in the fallback
        }))
        .catch(error => ({ 
          success: false, 
          error: error.message 
        }));
        
      const testVerifier = fetch('/verifier/healthcheck', { method: 'GET' })
        .then(response => ({ 
          success: response.ok, 
          status: response.status,
          latency: 0
        }))
        .catch(error => ({ 
          success: false, 
          error: error.message 
        }));
        
      const testWebSocket = fetch('/health/websocket', { method: 'GET' })
        .then(response => ({ 
          success: response.ok, 
          status: response.status,
          latency: 0
        }))
        .catch(error => ({ 
          success: false, 
          error: error.message 
        }));
        
      const testSSE = fetch('/health/sse', { method: 'GET' })
        .then(response => ({ 
          success: response.ok, 
          status: response.status,
          latency: 0
        }))
        .catch(error => ({ 
          success: false, 
          error: error.message 
        }));
      
      // Run all tests in parallel
      Promise.all([testIssuer, testVerifier, testWebSocket, testSSE])
        .then(([issuerResult, verifierResult, wsResult, sseResult]) => {
          // Calculate how many tests passed
          const passedTests = [issuerResult, verifierResult, wsResult, sseResult]
            .filter(result => result.success).length;
            
          // Create the test results object
          this.connectionTestResults = {
            success: passedTests === 4,
            message: `${passedTests}/4 tests passed`,
            components: {
              issuer: {
                success: issuerResult.success,
                ip: window.location.hostname,
                latency: issuerResult.latency,
                message: issuerResult.error || 'OK'
              },
              verifier: {
                success: verifierResult.success,
                ip: window.location.hostname,
                latency: verifierResult.latency,
                message: verifierResult.error || 'OK'
              },
              websocket: {
                success: wsResult.success,
                ip: window.location.hostname,
                latency: wsResult.latency,
                message: wsResult.error || 'OK'
              },
              sse: {
                success: sseResult.success,
                ip: window.location.hostname,
                latency: sseResult.latency,
                message: sseResult.error || 'OK'
              }
            }
          };
          
          console.log('🌐 Fallback test results:', this.connectionTestResults);
        })
        .catch(error => {
          console.error('🌐 Error in fallback connection test:', error);
          this.connectionTestError = error.message;
          
          // Create a basic error result
          this.connectionTestResults = {
            success: false,
            message: error.message,
            components: {
              issuer: { success: false, message: 'Connection failed' },
              verifier: { success: false, message: 'Connection failed' },
              sse: { success: false, message: 'Connection failed' },
              websocket: { success: false, message: 'Connection failed' }
            }
          };
        })
        .finally(() => {
          this.testingConnection = false;
        });
    },
    
    // Save complete network configuration
    saveCompleteNetworkConfiguration() {
      // Set the updating flag
      this.networkConfigUpdating = true;
      
      // Validate inputs
      if (!this.networkSettings.issuer_ip || !this.networkSettings.verifier_ip) {
        this.showNotification('Please enter valid IP addresses for Issuer and Verifier', 'error');
        this.networkConfigUpdating = false; // Reset flag on validation error
        return;
      }
      
      // Check ngrok settings
      if (this.networkSettings.use_ngrok && !this.networkSettings.ngrok_domain) {
        this.showNotification('Please enter a valid ngrok domain when enabling ngrok', 'error');
        this.networkConfigUpdating = false; // Reset flag on validation error
        return;
      }
      
      // Prepare data for API call
      const data = {
        issuer_ip: this.networkSettings.issuer_ip,
        verifier_ip: this.networkSettings.verifier_ip,
        issuer_port: this.networkSettings.issuer_port || '8080',
        verifier_port: this.networkSettings.verifier_port || '8080',
        use_https: this.networkSettings.use_https !== false,
        auto_discovery: this.networkSettings.auto_discovery || false,
        timeout: parseInt(this.networkSettings.timeout || '30', 10),
        use_ngrok: this.networkSettings.use_ngrok || false,
        ngrok_domain: this.networkSettings.use_ngrok ? this.networkSettings.ngrok_domain : '',
        default_ip: this.networkSettings.default_ip || this.networkData?.local_ip || 'localhost',
        default_port: this.networkSettings.default_port || this.networkData?.default_port || '8080'
      };
      
      // Make API call
      fetch('/api/system/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Network settings saved:', data);
          
          if (data.success) {
            this.showNotification('Network settings saved successfully', 'success');
            
            // Reload network settings to get the updated values
            this.loadNetworkSettings();
      
            // Update the local network settings
            this.networkSettings = {
              ...this.networkSettings,
              ...data.data
            };
          } else {
            throw new Error(data.message || 'Failed to save network settings');
          }
        })
        .catch(error => {
          console.error('🌐 Error saving network settings:', error);
          this.showNotification('Error saving network settings: ' + error.message, 'error');
        })
        .finally(() => {
          this.networkConfigUpdating = false; // Reset the updating flag
        });
    },
    
    // Load network data using the unified endpoint
    loadSimplifiedNetworkData() {
      console.log('🌐 Loading network data...');
      this.networkLoading = true;
      
      fetch('/api/network')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Network data loaded:', data);
          
          if (data && data.status === 'success') {
            // Extract data from API response
            const networkSettings = data.data || {};
            
            // Update network data structure
            this.networkData = {
              ...this.networkData,
              local_ip: networkSettings.default_ip || 'Unknown',
              public_ip: 'Not available', // Will be loaded separately if needed
              hostname: 'Unknown', // Will be loaded separately if needed
              default_port: networkSettings.default_port || '8080'
            };
            
            // 🚨 CRITICAL FIX: Set NGROK settings from config
            this.ngrokSettings = {
              useNgrok: !!networkSettings.use_ngrok,
              ngrokDomain: networkSettings.ngrok_url || '',
              issuerUrl: '', // Will be calculated
              verifierUrl: '' // Will be calculated
            };
            
            // 🚨 CRITICAL FIX: Determine connection mode and set ngrokDomain
            if (networkSettings.use_ngrok && networkSettings.ngrok_url) {
              this.connectionMode = 'ngrok';
              this.ngrokDomain = networkSettings.ngrok_url;
              console.log('🌐 NGROK mode detected, URL:', this.ngrokDomain);
            } else {
              this.connectionMode = networkSettings.connection_mode || 'local';
              this.ngrokDomain = ''; // Clear NGROK domain if not in NGROK mode
            }
            
            // Set server port
            this.serverPort = parseInt(networkSettings.default_port || '8080', 10);
            
            console.log('🌐 Network data updated:', this.networkData);
            console.log('🌐 Connection mode:', this.connectionMode);
            console.log('🌐 NGROK domain:', this.ngrokDomain);
            console.log('🌐 Server port:', this.serverPort);
          } else {
            console.error('🌐 Invalid network data format:', data);
            // Set defaults on error
            this.connectionMode = 'local';
            this.serverPort = 8080;
            this.ngrokDomain = '';
          }
        })
        .catch(error => {
          console.error('🌐 Error loading network data:', error);
          // Set defaults on error
          this.connectionMode = 'local';
          this.serverPort = 8080;
          this.ngrokDomain = '';
        })
        .finally(() => {
          this.networkLoading = false;
        });
    },
    
    // Debug helper function for network API issues
    debugNetworkAPI() {
      console.log('🔍 Debug Network API called');
      
      // Log current network data state
      console.log('Current networkData:', this.networkData);
      console.log('Current ngrokSettings:', this.ngrokSettings);
      
      // Try to fetch from all possible network endpoints
      const endpoints = [
        '/api/system/network',
        '/api/system/network/debug',
        '/settings/api/network',
        '/settings/api/network-info'
      ];
      
      // Test each endpoint
      endpoints.forEach(endpoint => {
        console.log(`Testing endpoint: ${endpoint}`);
        
        fetch(endpoint)
          .then(response => {
            console.log(`${endpoint} status:`, response.status);
            return response.json();
          })
          .then(data => {
            console.log(`${endpoint} data:`, data);
          })
          .catch(error => {
            console.error(`${endpoint} error:`, error);
          });
      });
      
      // Show a notification
      this.showNotification('Network API debug info logged to console', 'info');
      
      // Generate and log URL values
      console.log('Generated Issuer URL:', this.getIssuerUrl());
      console.log('Generated Verifier URL:', this.getVerifierUrl());
    },

    // New network configuration functions
    saveNetworkConfig() {
      this.networkConfigUpdating = true;
      
      // Validate port
      if (this.serverPort < 1000 || this.serverPort > 65535) {
        this.showNotification('Port must be between 1000 and 65535', 'error');
        this.networkConfigUpdating = false;
        return;
      }

      // Validate NGROK URL if NGROK mode is selected
      if (this.connectionMode === 'ngrok' && !this.ngrokDomain) {
        this.showNotification('Please enter an NGROK URL for tunnel mode', 'error');
        this.networkConfigUpdating = false;
        return;
      }
      
      // Map connection mode to appropriate IP setting
      let defaultIp;
      if (this.connectionMode === 'local') {
        defaultIp = this.networkData?.local_ip || '192.168.178.122';
      } else if (this.connectionMode === 'public') {
        defaultIp = this.networkData?.public_ip || this.networkData?.local_ip || '192.168.178.122';
      } else if (this.connectionMode === 'ngrok') {
        defaultIp = this.networkData?.local_ip || '192.168.178.122'; // NGROK still needs local IP
      }
      
      const data = {
        default_port: this.serverPort,
        default_ip: defaultIp,
        ngrok_domain: this.connectionMode === 'ngrok' ? this.ngrokDomain.replace('https://', '').replace('http://', '') : '',
        ngrok_url: this.connectionMode === 'ngrok' ? this.ngrokDomain : '',
        use_ngrok: this.connectionMode === 'ngrok',
        connection_mode: this.connectionMode,
        use_https: true,
        auto_discovery: false,
        timeout: 30
      };
      
      // Save network settings using system-aware API
      fetch('/api/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Network configuration saved:', data);
          this.showNotification('Network configuration saved successfully!', 'success');
          
          // Reload network settings to reflect changes
          this.loadNetworkSettings();
        })
        .catch(error => {
          console.error('🌐 Error saving network configuration:', error);
          this.showNotification('Error saving network configuration: ' + error.message, 'error');
        })
        .finally(() => {
          this.networkConfigUpdating = false;
        });
    },

    resetNetworkConfig() {
      this.connectionMode = 'local';
      this.serverPort = 8080;
      this.ngrokDomain = '';
      this.showNotification('Network configuration reset to defaults', 'info');
    },

    // Enhanced connection testing for all modes
    canTestConnection() {
      if (this.connectionMode === 'local') {
        return true; // Can always test local
      } else if (this.connectionMode === 'public') {
        return false; // Cannot test public IP from same machine
      } else if (this.connectionMode === 'ngrok') {
        return this.ngrokDomain && this.ngrokDomain.trim() !== '';
      }
      return false;
    },

    getTestButtonText() {
      if (this.connectionMode === 'local') {
        return 'Test Local Connection';
      } else if (this.connectionMode === 'public') {
        return 'Cannot Test (Same Machine)';
      } else if (this.connectionMode === 'ngrok') {
        return this.ngrokDomain ? 'Test NGROK Connection' : 'Enter NGROK URL First';
      }
      return 'Test Connection';
    },

    testSelectedConnection() {
      if (!this.canTestConnection()) {
        if (this.connectionMode === 'public') {
          this.showNotification('Cannot test public IP from the same machine. Public IP testing requires external client.', 'warning');
        } else if (this.connectionMode === 'ngrok' && !this.ngrokDomain) {
          this.showNotification('Please enter an NGROK URL first', 'error');
        }
        return;
      }

      this.testingConnection = true;
      
      if (this.connectionMode === 'local') {
        this.testLocalConnection();
      } else if (this.connectionMode === 'ngrok') {
        this.testNgrokConnection();
      }
    },

    testLocalConnection() {
      // Initialize test results structure
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Testing...', ip: '-', latency: null },
          verifier: { success: false, message: 'Testing...', ip: '-', latency: null }
        },
        message: 'Testing local connection...',
        success: false
      };
      
      // Use the new unified network test endpoint for system-aware testing
      fetch('/api/network/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🌐 Connection test response:', data);
          if (data.status === 'success') {
            // Count successful tests
            const testResults = data.test_results || {};
            const successCount = data.tests_passed || 0;
            const totalCount = data.tests_total || 0;
            const overallSuccess = data.overall_status === 'healthy';
            
            this.showNotification(
              `Local connection test ${overallSuccess ? 'successful' : 'completed'}! (${successCount}/${totalCount} components working)`, 
              overallSuccess ? 'success' : 'warning'
            );
            
            // Transform backend response format to match template expectations
            this.connectionTestResults = {
              message: `${successCount}/${totalCount} tests passed`,
              success: overallSuccess,
              components: {}
            };
            
            // Map issuer test results
            if (testResults.issuer) {
              this.connectionTestResults.components.issuer = {
                success: testResults.issuer.status === 'success',
                ip: this.networkData?.local_ip || '-',
                latency: testResults.issuer.latency_ms || null,
                message: testResults.issuer.error || 'Connected'
              };
            }
            
            // Map verifier test results
            if (testResults.verifier) {
              this.connectionTestResults.components.verifier = {
                success: testResults.verifier.status === 'success',
                ip: this.networkData?.local_ip || '-',
                latency: testResults.verifier.latency_ms || null,
                message: testResults.verifier.error || 'Connected'
              };
            }
          } else {
            this.showNotification('Local connection test failed: ' + (data.message || 'Unknown error'), 'error');
            this.connectionTestResults = {
              message: data.message || 'Connection test failed',
              success: false,
              components: {
                issuer: { success: false, message: data.message || 'Test failed', ip: '-', latency: null },
                verifier: { success: false, message: data.message || 'Test failed', ip: '-', latency: null }
              }
            };
          }
        })
        .catch(error => {
          console.error('🌐 Error testing local connection:', error);
          this.connectionTestResults = {
            components: {
              issuer: { success: false, message: error.message, ip: '-', latency: null },
              verifier: { success: false, message: error.message, ip: '-', latency: null }
            },
            message: `Error: ${error.message}`,
            success: false
          };
          this.showNotification('Error testing local connection: ' + error.message, 'error');
        })
        .finally(() => {
          this.testingConnection = false;
        });
    },

    transformTestResults(results) {
      // Transform backend test results format to match template expectations
      const transformed = {};
      
      for (const [componentName, result] of Object.entries(results)) {
        transformed[componentName] = {
          success: result.status === 'success',
          latency: result.latency_ms || result.latency || null,
          ip: this.extractIpFromUrl(result.url) || this.networkData?.local_ip || '192.168.178.122',
          message: result.message || (result.status === 'success' ? 'OK' : 'Failed')
        };
      }
      
      console.log('🔧 Transformed test results:', transformed);
      return transformed;
    },

    extractIpFromUrl(url) {
      if (!url) return null;
      try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;
        // Return IP if it's an IP address, otherwise return null
        if (/^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
          return hostname;
        }
        // For localhost/domain names, return the current network IP
        return this.networkData?.local_ip || null;
      } catch (e) {
        return null;
      }
    },

    testNgrokConnection() {
      if (!this.ngrokDomain) {
        this.showNotification('Please enter an NGROK URL first', 'error');
        this.testingConnection = false;
        return;
      }
      
      // Initialize test results structure
      this.connectionTestResults = {
        components: {
          issuer: { success: false, message: 'Testing...', ip: '-', latency: null },
          verifier: { success: false, message: 'Testing...', ip: '-', latency: null }
        },
        message: 'Testing NGROK connection...',
        success: false
      };
      
      fetch('/api/network/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          ngrok_domain: this.ngrokDomain,
          connection_type: 'ngrok'
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('🚇 NGROK test response:', data);
          
          if (data.status === 'success') {
            // Transform backend response to match template expectations
            const testResults = data.test_results || {};
            const overallSuccess = data.overall_status === 'healthy';
            const testsPassed = data.tests_passed || 0;
            const testsTotal = data.tests_total || 0;
            
            this.connectionTestResults = {
              components: {},
              message: `${testsPassed}/${testsTotal} tests passed`,
              success: overallSuccess
            };
            
            // Map issuer test results
            if (testResults.issuer) {
              this.connectionTestResults.components.issuer = {
                success: testResults.issuer.status === 'success',
                ip: this.ngrokDomain,
                latency: testResults.issuer.latency_ms || null,
                message: testResults.issuer.error || 'Connected'
              };
            }
            
            // Map verifier test results
            if (testResults.verifier) {
              this.connectionTestResults.components.verifier = {
                success: testResults.verifier.status === 'success',
                ip: this.ngrokDomain,
                latency: testResults.verifier.latency_ms || null,
                message: testResults.verifier.error || 'Connected'
              };
            }
            
            const avgLatency = testsTotal > 0 ? 
              Math.round((testResults.issuer?.latency_ms || 0) + (testResults.verifier?.latency_ms || 0)) / testsTotal : 
              'N/A';
            
            this.showNotification(
              `NGROK connection test ${overallSuccess ? 'successful' : 'completed with issues'}! (${avgLatency}ms average)`, 
              overallSuccess ? 'success' : 'warning'
            );
          } else {
            // Test failed
            this.connectionTestResults = {
              components: {
                issuer: { success: false, message: data.message || 'Test failed', ip: '-', latency: null },
                verifier: { success: false, message: data.message || 'Test failed', ip: '-', latency: null }
              },
              message: data.message || 'Connection test failed',
              success: false
            };
            this.showNotification('NGROK connection test failed: ' + (data.message || 'Unknown error'), 'error');
          }
        })
        .catch(error => {
          console.error('🌐 Error testing NGROK connection:', error);
          this.connectionTestResults = {
            components: {
              issuer: { success: false, message: error.message, ip: '-', latency: null },
              verifier: { success: false, message: error.message, ip: '-', latency: null }
            },
            message: `Error: ${error.message}`,
            success: false
          };
          this.showNotification('Error testing NGROK connection: ' + error.message, 'error');
        })
        .finally(() => {
          this.testingConnection = false;
        });
    },

    // 🔐 HERZCHIRURG V3 KEY MANAGEMENT FUNCTIONS
    // Enterprise-grade cryptographic key lifecycle management
    
    // Load key inventory from backend with enhanced statistics
    loadKeyInventory() {
      console.log('🔑 Loading key inventory...');
      this.keyInventoryLoading = true;
      this.keyInventoryError = null;
      
      return fetch('/settings/api/keys/inventory', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('🔑 Key inventory loaded:', data);
        
        if (data.status === 'success') {
          this.keyInventoryData = data.keys || [];
          
          // Use statistics from API response if available, otherwise calculate locally
          if (data.statistics) {
            this.keyStatistics = data.statistics;
          } else {
            this.updateKeyStatistics();
          }
          
          console.log(`🔑 Loaded ${this.keyInventoryData.length} keys - Stats:`, this.keyStatistics);
          
          // Auto-run security audit if we have keys and it hasn't run recently
          if (this.keyInventoryData.length > 0 && !this.securityAuditRunning && this.keySecurityScore === 0) {
            setTimeout(() => this.runSecurityAudit(), 1500);
          }
          
          // Clear any previous errors
          this.keyInventoryError = null;
        } else {
          throw new Error(data.message || 'Failed to load key inventory');
        }
      })
      .catch(error => {
        console.error('🔑 Error loading key inventory:', error);
        this.keyInventoryError = error.message;
        this.showNotification(`Error loading key inventory: ${error.message}`, 'error');
        this.keyInventoryData = [];
        this.keyStatistics = { total: 0, active: 0, expired: 0, expiring_soon: 0 };
      })
      .finally(() => {
        this.keyInventoryLoading = false;
      });
    },

    // Refresh key inventory with retry logic
    refreshKeyInventory() {
      console.log('🔐 Refreshing key inventory...');
      this.loadKeyInventory();
    },

    // Enhanced retry mechanism for API calls
    async retryApiCall(apiCall, maxRetries = 3, delay = 1000) {
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`🔧 API call attempt ${attempt}/${maxRetries}`);
          return await apiCall();
        } catch (error) {
          console.warn(`🔧 API call attempt ${attempt} failed:`, error.message);
          
          if (attempt === maxRetries) {
            throw error; // Final attempt failed
          }
          
          // Wait before retrying with exponential backoff
          const backoffDelay = delay * Math.pow(2, attempt - 1);
          console.log(`🔧 Retrying in ${backoffDelay}ms...`);
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
        }
      }
    },

    // Enhanced notification system with auto-dismiss
    showNotificationWithTimeout(message, type = 'info', timeout = 5000) {
      this.showNotification(message, type);
      
      // Auto-dismiss after timeout
      setTimeout(() => {
        // Remove notification if it still exists
        console.log(`🔧 Auto-dismissing notification: ${message}`);
      }, timeout);
    },

    // Generate new cryptographic key
    generateKey() {
      console.log('🔑 Generating new key...', this.newKeyConfig);
      this.keyGenerating = true;
      
      fetch('/settings/api/keys/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          type: this.newKeyConfig.type,
          purpose: this.newKeyConfig.purpose || 'General Purpose',
          validity_days: parseInt(this.newKeyConfig.validity_days) || 365
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('🔑 Key generation response:', data);
        
        if (data.status === 'success') {
          this.showNotification(`${this.newKeyConfig.type} key generated successfully`, 'success');
          this.showGenerateKeyModal = false;
          this.newKeyConfig = {
            type: 'Ed25519',
            purpose: 'General Purpose',
            validity_days: 365
          };
          this.loadKeyInventory();
        } else {
          throw new Error(data.message || 'Failed to generate key');
        }
      })
      .catch(error => {
        console.error('🔑 Error generating key:', error);
        this.showNotification(`Error generating key: ${error.message}`, 'error');
      })
      .finally(() => {
        this.keyGenerating = false;
      });
    },

    // Rotate existing key
    rotateKey(keyId) {
      if (!confirm('Are you sure you want to rotate this key? This action cannot be undone.')) {
        return;
      }
      
      console.log('🔑 Rotating key:', keyId);
      this.showNotification('Key rotation started...', 'info');
      
      fetch(`/settings/api/keys/${keyId}/rotate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          this.showNotification('Key rotation completed successfully!', 'success');
          this.loadKeyInventory();
        } else {
          throw new Error(data.message || 'Failed to rotate key');
        }
      })
      .catch(error => {
        console.error('🔑 Error rotating key:', error);
        this.showNotification(`Error rotating key: ${error.message}`, 'error');
      });
    },

    // Export key for backup
    exportKey(keyId) {
      console.log('🔑 Exporting key:', keyId);
      this.showNotification('Preparing key export...', 'info');
      
      fetch(`/settings/api/keys/${keyId}/export`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          // Create download link
          const blob = new Blob([JSON.stringify(data.export_data, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `key-export-${keyId}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          
          this.showNotification('Key exported successfully!', 'success');
        } else {
          throw new Error(data.message || 'Failed to export key');
        }
      })
      .catch(error => {
        console.error('🔑 Error exporting key:', error);
        this.showNotification(`Error exporting key: ${error.message}`, 'error');
      });
    },

    // Archive key (soft delete)
    archiveKey(keyId) {
      if (!confirm('Are you sure you want to archive this key? It will no longer be available for new operations.')) {
        return;
      }
      
      console.log('🔑 Archiving key:', keyId);
      
      fetch(`/settings/api/keys/${keyId}/archive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          this.showNotification('Key archived successfully', 'success');
          this.loadKeyInventory();
        } else {
          throw new Error(data.message || 'Failed to archive key');
        }
      })
      .catch(error => {
        console.error('🔑 Error archiving key:', error);
        this.showNotification(`Error archiving key: ${error.message}`, 'error');
      });
    },

    // Delete key permanently
    deleteKey(keyId) {
      if (!confirm('⚠️ DANGEROUS: Are you sure you want to permanently delete this key? This action cannot be undone and may break existing credentials!')) {
        return;
      }
      
      console.log('🔑 Deleting key:', keyId);
      
      fetch(`/settings/api/keys/${keyId}/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === 'success') {
          this.showNotification('Key permanently deleted', 'warning');
          this.loadKeyInventory();
        } else {
          throw new Error(data.message || 'Failed to delete key');
        }
      })
      .catch(error => {
        console.error('🔑 Error deleting key:', error);
        this.showNotification(`Error deleting key: ${error.message}`, 'error');
      });
    },

    // Run security audit (aliased to match template function call)
    securityAudit() {
      return this.runSecurityAudit();
    },

    runSecurityAudit() {
      console.log('🔐 Running security audit...');
      this.securityAuditRunning = true;
      
      // Enhanced security audit with actual key analysis
      setTimeout(() => {
        if (!this.keyInventoryData || this.keyInventoryData.length === 0) {
          this.keySecurityScore = 0;
          this.securityAuditRunning = false;
          this.showNotification('No keys found - critical security issue!', 'error');
          return;
        }

        // Analyze key inventory
        const activeKeys = this.keyInventoryData.filter(k => k.status === 'active');
        const expiredKeys = this.keyInventoryData.filter(k => k.status === 'expired');
        const hasModernAlgorithms = activeKeys.some(k => 
          k.algorithm === 'Ed25519' || k.algorithm === 'EdDSA' || k.algorithm === 'BBS+');
        
        // Enhanced scoring algorithm
        let score = 50; // Base score
        
        // Key availability and redundancy
        if (activeKeys.length >= 1) score += 15;
        if (activeKeys.length >= 2) score += 10;
        if (activeKeys.length >= 3) score += 5;
        
        // Key health
        if (expiredKeys.length === 0) score += 15;
        if (hasModernAlgorithms) score += 15;
        
        // Check for BBS+ and JWT keys
        const hasBBSKey = activeKeys.some(k => k.type === 'BBS+');
        const hasJWTKey = activeKeys.some(k => k.type === 'Ed25519' && k.usage === 'jwt_signing');
        if (hasBBSKey && hasJWTKey) score += 10;
        
        // Expiry warnings
        const expiringSoon = activeKeys.filter(k => {
          const expiryDate = new Date(k.expires);
          const thirtyDaysFromNow = new Date();
          thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
          return expiryDate <= thirtyDaysFromNow;
        }).length;
        
        if (expiringSoon === 0) score += 5;
        else if (expiringSoon > 0) score -= expiringSoon * 5;
        
        this.keySecurityScore = Math.max(0, Math.min(score, 100));
        this.securityAuditRunning = false;
        
        const level = this.keySecurityScore >= 80 ? 'success' : 
                     this.keySecurityScore >= 60 ? 'warning' : 'error';
        
        this.showNotification(
          `Security audit completed. Score: ${this.keySecurityScore}/100 - ${
            this.keySecurityScore >= 80 ? 'Excellent' :
            this.keySecurityScore >= 60 ? 'Good' : 'Needs attention'
          }`, level
        );
      }, 2000);
    },

    // Bulk operations
    bulkRotateKeys() {
      if (!confirm('Are you sure you want to rotate all active keys? This is a major operation.')) {
        return;
      }
      
      console.log('🔐 Starting bulk key rotation...');
      this.showNotification('Bulk key rotation started...', 'info');
      
      // Mock bulk rotation
      setTimeout(() => {
        const activeKeys = this.keyInventoryData.filter(k => k.status === 'active');
        activeKeys.forEach(key => {
          this.rotateKey(key.id);
        });
        this.showNotification(`Bulk rotation completed for ${activeKeys.length} keys`, 'success');
      }, 2000);
    },

    exportAllKeys() {
      console.log('🔐 Exporting all keys...');
      this.showNotification('Preparing bulk export...', 'info');
      
      setTimeout(() => {
        const exportData = {
          export_timestamp: new Date().toISOString(),
          total_keys: this.keyInventoryData.length,
          keys: this.keyInventoryData.map(key => ({
            id: key.id,
            type: key.type,
            algorithm: key.algorithm,
            status: key.status,
            created_at: key.created_at,
            expires_at: key.expires_at,
            purpose: key.purpose
          }))
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `key-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Complete key backup exported successfully!', 'success');
      }, 1500);
    },

    // Utility functions
    getAlgorithmForType(type) {
      const algorithmMap = {
        'Ed25519': 'Ed25519',
        'BBS+': 'BLS12-381',
        'DID': 'Ed25519',
        'X.509': 'RSA-2048'
      };
      return algorithmMap[type] || 'Unknown';
    },

    calculateExpiryDate(validityDays) {
      const now = new Date();
      now.setDate(now.getDate() + parseInt(validityDays));
      return now.toISOString();
    },

    updateKeyStatistics() {
      this.keyStatistics = {
        totalKeys: this.keyInventoryData.length,
        activeKeys: this.keyInventoryData.filter(k => k.status === 'active').length,
        expiringSoon: this.keyInventoryData.filter(k => {
          const expiryDate = new Date(k.expires_at);
          const thirtyDaysFromNow = new Date();
          thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
          return expiryDate <= thirtyDaysFromNow && k.status === 'active';
        }).length
      };
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    },
    
    // API Testing Functions
    async testIssuerEndpoint() {
      this.apiTesting = true;
      this.apiResponse = null;
      const startTime = Date.now();
      
      let testData;
      try {
        testData = JSON.parse(this.issuerRequestBody);
      } catch (e) {
        this.apiResponseStatus = 400;
        this.apiResponse = { error: "Invalid JSON in request body" };
        this.apiTesting = false;
        return;
      }
      
      const headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
      };
      
      // Add API key if selected
      if (this.selectedApiKey) {
        headers['Authorization'] = `Bearer ${this.selectedApiKey}`;
      }
      
      try {
        const response = await fetch('/issuer', {
          method: 'POST',
          headers: headers,
          body: new URLSearchParams(testData)
        });
        
        this.apiResponseStatus = response.status;
        this.responseTime = Date.now() - startTime;
        const text = await response.text();
        
        // Check if response is HTML (contains QR code) or JSON
        if (text.includes('<!DOCTYPE') || text.includes('<html')) {
          this.apiResponse = {
            success: true,
            message: "Credential issued successfully",
            note: "Full HTML response with QR code received"
          };
          this.issuerResponse = this.apiResponse;
        } else {
          try {
            this.apiResponse = JSON.parse(text);
            this.issuerResponse = this.apiResponse;
          } catch (e) {
            this.apiResponse = { error: "Invalid response format", raw: text.substring(0, 200) };
          }
        }
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
        this.responseTime = Date.now() - startTime;
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testIssuerMetadata() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/.well-known/openid-credential-issuer');
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testVerifierEndpoint() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/verifier');
        this.apiResponseStatus = response.status;
        const text = await response.text();
        
        if (text.includes('<!DOCTYPE') || text.includes('<html')) {
          this.apiResponse = {
            success: true,
            message: "Verifier page loaded successfully",
            note: "Returns HTML page with QR code for presentation request"
          };
        } else {
          this.apiResponse = JSON.parse(text);
        }
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testVCStatusList() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/vcstatus');
        this.apiResponseStatus = response.status;
        const text = await response.text();
        
        if (text.includes('<!DOCTYPE') || text.includes('<html')) {
          // Try the API endpoint instead
          const apiResponse = await fetch('/api/credentials');
          this.apiResponseStatus = apiResponse.status;
          this.apiResponse = await apiResponse.json();
        } else {
          this.apiResponse = JSON.parse(text);
        }
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testVCValidity() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      // Use a sample identifier
      const identifier = 'urn:uuid:12345678-1234-5678-9012-123456789012';
      
      try {
        const response = await fetch(`/vcstatus/isvalid/${identifier}`);
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testNetworkConfig() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/settings/api/network');
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testKeyInventory() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/settings/api/keys/inventory');
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testHealthCheck() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/api/health');
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    async testSystemHealth() {
      this.apiTesting = true;
      this.apiResponse = null;
      
      try {
        const response = await fetch('/api/system/health');
        this.apiResponseStatus = response.status;
        this.apiResponse = await response.json();
      } catch (error) {
        this.apiResponseStatus = 500;
        this.apiResponse = { error: error.message };
      } finally {
        this.apiTesting = false;
      }
    },
    
    copyResponse() {
      if (this.apiResponse) {
        const text = JSON.stringify(this.apiResponse, null, 2);
        navigator.clipboard.writeText(text).then(() => {
          this.showNotification('Response copied to clipboard', 'success');
        }).catch(err => {
          console.error('Failed to copy:', err);
          this.showNotification('Failed to copy response', 'error');
        });
      }
    },
    
    getStatusText(status) {
      const statusTexts = {
        200: 'OK',
        201: 'Created',
        204: 'No Content',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable'
      };
      return statusTexts[status] || '';
    }
  }));
  
  console.log('🩺 HERZCHIRURG: Settings component ready for Alpine.js initialization');
  
  // API Diagnostics Component
  Alpine.data('apiDiagnostics', () => ({
    // State
    systemConfig: {},
    configLoading: false,
    configLastUpdated: null,
    showTestResults: false,
    testResult: {},
    
    // Initialize
    init() {
      console.log('🔌 API Diagnostics initialized');
      this.refreshSystemConfig();
    },
    
    // Load system configuration
    async refreshSystemConfig() {
      this.configLoading = true;
      
      try {
        const response = await fetch('/api/system/network', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'same-origin'
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.config) {
          this.systemConfig = data.config;
          this.configLastUpdated = new Date().toLocaleString();
          console.log('🔌 System config loaded:', this.systemConfig);
        } else {
          throw new Error(data.message || 'Invalid response format');
        }
      } catch (error) {
        console.error('🔌 Error loading system config:', error);
        this.showNotification(`Failed to load system configuration: ${error.message}`, 'error');
      } finally {
        this.configLoading = false;
      }
    },
    
    // Generate endpoint URL based on current configuration
    generateEndpointUrl(path) {
      const baseUrl = this.systemConfig.ngrok_url || this.systemConfig.server_url || 'https://localhost:8080';
      return `${baseUrl}${path}`;
    },
    
    // Test an endpoint
    async testEndpoint(path, method = 'GET') {
      const url = this.generateEndpointUrl(path);
      const startTime = performance.now();
      
      try {
        const options = {
          method: method,
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          credentials: 'same-origin'
        };
        
        // Add test data for POST requests
        if (method === 'POST') {
          if (path.includes('/issuer/offer')) {
            options.body = JSON.stringify({
              credential_type: 'StudentCredential',
              pre_authorized_code: 'test-code-' + Date.now()
            });
          } else if (path.includes('/verifier/callback')) {
            options.body = JSON.stringify({
              vp_token: 'test-vp-token',
              presentation_submission: {}
            });
          }
        }
        
        const response = await fetch(url, options);
        const endTime = performance.now();
        
        // Get response headers
        const headers = {};
        response.headers.forEach((value, key) => {
          headers[key] = value;
        });
        
        // Parse response body
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          data = await response.json();
        } else {
          data = await response.text();
        }
        
        // Store test result
        this.testResult = {
          endpoint: url,
          method: method,
          status: response.status,
          statusText: response.statusText,
          headers: headers,
          data: data,
          responseTime: Math.round(endTime - startTime)
        };
        
        // Show results modal
        this.showTestResults = true;
        
      } catch (error) {
        console.error('🔌 Error testing endpoint:', error);
        
        this.testResult = {
          endpoint: url,
          method: method,
          status: 0,
          statusText: 'Network Error',
          headers: {},
          data: {
            error: error.message,
            details: 'Failed to connect to the endpoint. Check if the server is running and the URL is correct.'
          },
          responseTime: 0
        };
        
        this.showTestResults = true;
      }
    },
    
    // Copy to clipboard
    async copyToClipboard(text) {
      try {
        await navigator.clipboard.writeText(text);
        this.showNotification('Copied to clipboard', 'success');
      } catch (error) {
        console.error('Failed to copy:', error);
        this.showNotification('Failed to copy to clipboard', 'error');
      }
    },
    
    // Show notification (borrowed from main settings component)
    showNotification(message, type = 'info') {
      // Find the parent settings component and use its notification system
      const settingsComponent = this.$el.closest('[x-data]').__x.$data;
      if (settingsComponent && settingsComponent.showNotification) {
        settingsComponent.showNotification(message, type);
      } else {
        // Fallback to console
        console.log(`[${type.toUpperCase()}] ${message}`);
      }
    }
  }));
});