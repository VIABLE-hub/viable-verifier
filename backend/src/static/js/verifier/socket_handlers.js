// Socket.IO Connection Handler and Event Handling
document.addEventListener('DOMContentLoaded', function() {
  // Get the server URL from the window object (will be set in the template)
  const serverUrl = window.SERVER_URL; //|| window.location.origin;
  const fallbackUrl = serverUrl;
  console.log('[Socket.IO] Primary server URL:', serverUrl);
  console.log('[Socket.IO] Fallback server URL:', fallbackUrl);
  
  // CRITICAL FIX: Automatic fallback for failed ngrok connections
  let socket = null;
  let connectionAttempts = 0;
  const maxAttempts = 2; // Try primary, then fallback
  
  function createSocketConnection(url, attemptNumber = 1) {
    console.log(`[Socket.IO] Connection attempt ${attemptNumber} to: ${url}`);
    
    // DOCKER SOCKET.IO FIX: Enhanced configuration for Docker environments
    const isDockerEnvironment = window.location.hostname === 'localhost' && 
                                (window.location.port === '8080' || 
                                 window.location.port === '8081' || 
                                 window.location.port === '8082');
    
    const socketConfig = {
      // DOCKER COMPATIBILITY: Use polling-first for Docker reliability
      transports: isDockerEnvironment ? ['polling'] : ['polling', 'websocket'],
      secure: window.location.protocol === 'https:',
      rejectUnauthorized: false, // Accept self-signed certificates
      reconnection: false, // Disable auto-reconnection to handle fallback manually
      timeout: isDockerEnvironment ? 20000 : 10000, // Longer timeout for Docker
      forceNew: true,
      // DOCKER SOCKET.IO: Enhanced compatibility options
      upgrade: !isDockerEnvironment, // Disable WebSocket upgrade in Docker
      rememberUpgrade: false,
      cors: {
        origin: "*",
        credentials: false
      }
    };
    
    console.log('[Socket.IO] Configuration:', socketConfig);
    console.log('[Socket.IO] Docker environment detected:', isDockerEnvironment);
    console.log('[Socket.IO] Using transport priority:', socketConfig.transports);
    
    const newSocket = io(url, socketConfig);
    
    // Connection success
    newSocket.on('connect', function() {
      console.log('[Socket.IO] Connected successfully to:', url);
      console.log('[Socket.IO] Transport:', newSocket.io.engine.transport.name);
      socket = newSocket; // Set the working socket
      connectionAttempts = maxAttempts; // Stop further attempts
      
      // VISUAL FEEDBACK FIX: Add connection success indicator
      addStatusFeedEntry('Socket.IO connection established', 'success');
    });
    
    // Connection errors
    newSocket.on('connect_error', function(error) {
      console.log('[Socket.IO] Connection Error:', error.message);
      console.log('[Socket.IO] Debug-Info: ', {
        url: window.location.href,
        socketURL: url,
        protocol: window.location.protocol,
        pathname: window.location.pathname,
        secure: window.location.protocol === 'https:',
        attempt: attemptNumber,
        dockerMode: isDockerEnvironment
      });
      
      // If this was the primary URL and we haven't tried fallback yet
      if (attemptNumber === 1 && url !== fallbackUrl) {
        console.log('[Socket.IO] Primary connection failed, trying fallback...');
        setTimeout(() => {
          createSocketConnection(fallbackUrl, 2);
        }, 1000);
      } else {
        console.log('[Socket.IO] All connection attempts failed');
        console.log('[Socket.IO] Troubleshooting: 1. Backend running? (make dev) 2. CORS configured? 3. SSL certificate accepted?');
        
        // VISUAL FEEDBACK FIX: Show connection error to user
        addStatusFeedEntry('Socket.IO connection failed - Live updates not available', 'error');
      }
      
      // Clean up failed connection
      newSocket.disconnect();
    });
    
    // Other error handlers remain the same
    newSocket.on('disconnect', function(reason) {
      console.log('[Socket.IO] Disconnected:', reason);
      // VISUAL FEEDBACK FIX: Show disconnection notice
      if (reason === 'io server disconnect') {
        addStatusFeedEntry('Socket.IO connection disconnected', 'warning');
      }
    });

    // Verification event handlers
    newSocket.on('presentation_requested', function(msg) {
      updateVerificationStep('presentation_requested', msg.status === 'success' ? 'success' : 'error');
    });

    newSocket.on('presentation_received', function(msg) {
      updateVerificationStep('presentation_requested', msg.status === 'success' ? 'success' : 'error');
    });

    newSocket.on('key_extraction', function(msg) {
      updateVerificationStep('key_extraction', msg.status === 'success' ? 'success' : 'error');
    });

    newSocket.on('signature_verification', function(msg) {
      updateVerificationStep('signature_verification', msg.status === 'success' ? 'success' : 'error');
      
      // Update dynamic details for both Crypto and Identity sections
      if (msg.details) {
          [ 'code-signature', 'code-holder-binding' ].forEach(id => {
              const el = document.getElementById(id);
              if (el) {
                  // Update Title if SD-JWT
                  if (msg.format === 'sd_jwt') {
                      const title = el.querySelector('.font-semibold');
                      if (title) {
                          if (id === 'code-signature') title.textContent = '✅ ECDSA Signature Verification';
                          if (id === 'code-holder-binding') title.textContent = '👤 Holder Binding (KB-JWT)';
                      }
                  }
                  
                  // Update Content
                  const content = el.querySelector('.space-y-1');
                  if (content) {
                      let html = '';
                      for (const [key, value] of Object.entries(msg.details)) {
                           // Filter fields based on section logic
                           let show = true;
                           if (id === 'code-signature' && key === 'key_binding') show = false;
                           if (id === 'code-holder-binding' && (key === 'serialization' || key === 'hashing')) show = false;
                           
                           if (show) {
                               const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                               html += `<div><span class="text-blue-600">${label}:</span> ${value}</div>`;
                           }
                      }
                      
                      const colorClass = msg.status === 'success' ? 'text-green-600' : 'text-red-600';
                      const icon = msg.status === 'success' ? '✓' : '✗';
                      html += `<div><span class="${colorClass}">Status:</span> ${icon} ${msg.status === 'success' ? 'Verified' : 'Failed'}</div>`;
                      content.innerHTML = html;
                  }
              }
          });
      }
    });

    newSocket.on('issuer_pub_key_verification', function(msg) {
      updateVerificationStep('issuer_pub_key_verification', msg.status === 'success' ? 'success' : 'error');
      
      if (msg.details) {
          const el = document.getElementById('code-issuer-trust');
          if (el) {
              const content = el.querySelector('.space-y-1');
              if (content) {
                  let html = '';
                  for (const [key, value] of Object.entries(msg.details)) {
                      const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      html += `<div><span class="text-blue-600">${label}:</span> ${value}</div>`;
                  }
                  const colorClass = msg.status === 'success' ? 'text-green-600' : 'text-red-600';
                  const icon = msg.status === 'success' ? '✓' : '✗';
                  html += `<div><span class="${colorClass}">Status:</span> ${icon} ${msg.status === 'success' ? 'Trusted' : 'Untrusted'}</div>`;
                  content.innerHTML = html;
              }
          }
      }
    });

    newSocket.on('mandatory_fields_verification', function(msg) {
      updateVerificationStep('mandatory_fields_verification', msg.status === 'success' ? 'success' : 'error');
      // If error, display the message
      if (msg.status === 'error') {
        addStatusFeedEntry(`ERROR - Mandatory fields: ${msg.message}`, 'error');
      }
    });

    newSocket.on('credential_validity_status', function(msg) {
      updateVerificationStep('credential_validity_status', msg.status === 'success' ? 'success' : 'error');
      
      // Update the details view
      const detailsElement = document.getElementById('code-credential-status');
      if (detailsElement) {
          const colorClass = msg.status === 'success' ? 'text-green-600' : 'text-red-600';
          const icon = msg.status === 'success' ? '✓' : '✗';
          const validValue = msg.status === 'success' ? 1 : 0;
          
          detailsElement.innerHTML = `
             <div><span class="text-blue-600">Registry:</span> StatusList2021 (W3C Specification)</div>
             <div><span class="text-blue-600">Endpoint:</span> GET /vcstatus/isvalid/{credentialId}</div>
             <div><span class="text-blue-600">Database Query:</span> PostgreSQL lookup in vc_credentials table</div>
             <div><span class="text-blue-600">Response:</span> {"valid": ${validValue}}</div>
             <div><span class="${colorClass}">Status:</span> ${icon} ${msg.message}</div>
          `;
      }
    });

    newSocket.on('issuer_bbs_key_verification', function(msg) {
      updateVerificationStep('issuer_bbs_key_verification', msg.status === 'success' ? 'success' : 'error');
      
      // Update dynamic details if available (switching between BBS+ and SD-JWT)
      if (msg.details) {
        const keyElement = document.getElementById('code-bbs-key');
        if (keyElement) {
           // Update Title
           if (msg.format === 'sd_jwt') {
              const title = keyElement.querySelector('.font-semibold');
              if (title) title.textContent = '🔐 ECDSA Public Key Validation';
           }
           
           // Update Content
           const content = keyElement.querySelector('.space-y-1');
           if (content) {
               let html = '';
               for (const [key, value] of Object.entries(msg.details)) {
                   const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                   html += `<div><span class="text-blue-600">${label}:</span> ${value}</div>`;
               }
               // Status line is usually part of details in my backend construction, but let's ensure it ends with status
               if (!msg.details.status) {
                    const colorClass = msg.status === 'success' ? 'text-green-600' : 'text-red-600';
                    const icon = msg.status === 'success' ? '✓' : '✗';
                    html += `<div><span class="${colorClass}">Status:</span> ${icon} ${msg.message}</div>`;
               }
               content.innerHTML = html;
           }
        }
      }
    });

    newSocket.on('verification_result', function(msg) {
      console.log('FINAL: Verification result received:', msg);
      
      // ENHANCED VISUAL FEEDBACK: Better success/error handling
      if (msg.status === 'success') {
        updateVerificationStep('verification_result', 'success');
        // All verification steps completed successfully
        updateProgressBar();
        
        // ENHANCED SUCCESS FEEDBACK: More prominent success message
        const issuerInfo = msg.issuer || 'root'; // Get issuer from backend response
        const successMessage = `Verification completed successfully!<br/>Valid student ID issued by <strong>${issuerInfo}</strong>`;
        addStatusFeedEntry(successMessage, 'success');
        
        // VISUAL SUCCESS ENHANCEMENT: Add celebratory visual elements
        setTimeout(() => {
          addStatusFeedEntry('Credential successfully verified! Mobile wallet can be closed.', 'success');
        }, 1000);
        
        // Display transmitted field values
        if (msg.transmitted_fields) {
          displayTransmittedFields(msg.transmitted_fields);
        }
        
        // Process disclosure validation if present
        if (msg.credential_data && msg.credential_data.disclosure_summary) {
          displayDisclosureResults(msg.credential_data);
        }
      } else if (msg.status === 'error') {
        updateVerificationStep('verification_result', 'error');
        // Verification failed 
        updateProgressBar();
        const errorMessage = msg.message || 'Verification failed';
        addStatusFeedEntry(`ERROR: ${errorMessage}`, 'error');
        
        // Process disclosure validation errors if present
        if (msg.disclosure_validation) {
          displayDisclosureErrors(msg.disclosure_validation);
        }
      } else if (msg.valid === 1) {
        // Legacy format support
        updateVerificationStep('verification_result', 'success');
        updateProgressBar();
        
        // ENHANCED SUCCESS FEEDBACK: Legacy support with enhanced visuals
        const issuerInfo = msg.issuer || 'root'; // Get issuer from backend response, fallback to 'root'
        const successMessage = `Verification completed successfully!<br/>Valid student ID issued by <strong>${issuerInfo}</strong>`;
        addStatusFeedEntry(successMessage, 'success');
        
        // VISUAL SUCCESS ENHANCEMENT: Add celebratory visual elements (legacy)
        setTimeout(() => {
          addStatusFeedEntry('Credential successfully verified! Mobile wallet can be closed.', 'success');
        }, 1000);
        
        if (msg.credential_data && msg.credential_data.disclosure_summary) {
          displayDisclosureResults(msg.credential_data);
        }
      } else if (msg.valid === 0) {
        // Legacy format support
        updateVerificationStep('verification_result', 'error');
        updateProgressBar();
        addStatusFeedEntry('ERROR: Verification failed', 'error');
        
        if (msg.disclosure_validation) {
          displayDisclosureErrors(msg.disclosure_validation);
        }
      } else {
        console.warn('WARNING: Ambiguous verification result:', msg);
        updateVerificationStep('verification_result', 'error');
        updateProgressBar();
        addStatusFeedEntry('WARNING: Unclear verification result', 'error');
      }
    });

    return newSocket;
  }
  
  // Start the connection process
  createSocketConnection(serverUrl, 1);
}); 

/**
 * Format a field name for display
 */
function formatFieldName(field) {
  try {
    // Remove namespaces like "vc.credentialSubject."
    let displayName = field.replace(/^(vc\.credentialSubject\.|vc\.|credentialSubject\.)/, '');
    
    // Handle iOS wallet field names
    const fieldMappings = {
      'bbsDPK': 'BBS+ Public Key',
      'totalMessages': 'Total Messages',
      'signedNonce': 'Signed Nonce',
      'validityIdentifier': 'Validity Identifier',
      'firstName': 'First Name',
      'lastName': 'Last Name',
      'studentId': 'Student ID',
      'studentIdPrefix': 'Student ID Prefix',
      'dateOfBirth': 'Date of Birth',
      'studyProgram': 'Study Program',
      'email': 'Email'
    };
    
    // Check if we have a direct mapping
    if (fieldMappings[displayName]) {
      return fieldMappings[displayName];
    }
    
    // Convert camelCase to Title Case with spaces
    displayName = displayName
      .replace(/([a-z])([A-Z])/g, '$1 $2') // Add space between lower to upper
      .replace(/^./, match => match.toUpperCase()); // Capitalize first letter
    
    return displayName;
  } catch (error) {
    console.error('Error formatting field name:', error);
    return field;
  }
}

/**
 * Format a field value for display
 */
function formatFieldValue(value, field) {
  if (value === null || value === undefined) {
    return '';
  }
  
  try {
    // Format date fields
    if (field.includes('Date') || field.includes('date')) {
      // Check if it's a timestamp
      const timestamp = parseInt(value);
      if (!isNaN(timestamp) && timestamp > 1000000000) {
        return new Date(timestamp * 1000).toLocaleDateString();
      }
      
      // Try to parse as ISO date
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return date.toLocaleDateString();
      }
    }
    
    // Format technical fields (truncate long values)
    const technicalFields = ['bbsDPK', 'totalMessages', 'signedNonce', 'validityIdentifier', 'iss', 'sub'];
    if (technicalFields.some(tech => field.includes(tech))) {
      if (typeof value === 'string' && value.length > 20) {
        return value.substring(0, 20) + '...';
      }
    }
    
    return value.toString();
  } catch (error) {
    console.error('Error formatting field value:', error);
    return value.toString();
  }
}

/**
 * Display selective disclosure validation results
 */
function displayDisclosureResults(credentialData) {
  try {
    // Check if we have disclosure data
    if (!credentialData || !credentialData.disclosure_summary) return;
    
    const summary = credentialData.disclosure_summary;
    const disclosureElement = document.getElementById('disclosure-results');
    if (!disclosureElement) return;
    
    // Create disclosure summary
    let disclosureHtml = '<div class="space-y-3 mt-3">';
    
    // Process mandatory fields
    const mandatory = summary.mandatory || {};
    if (mandatory.disclosed && mandatory.disclosed.length > 0) {
      disclosureHtml += '<div class="disclosure-section">';
      disclosureHtml += '<h4 class="text-sm font-medium mb-2 text-blue-700">Mandatory Fields (Disclosed)</h4>';
      disclosureHtml += '<div class="grid grid-cols-2 gap-1">';
      mandatory.disclosed.forEach(field => {
        const value = mandatory.values[field] || '';
        disclosureHtml += `
          <div class="col-span-1 text-xs text-blue-800">${formatFieldName(field)}</div>
          <div class="col-span-1 text-xs flex items-center">
            <span class="text-green-600 mr-1">✓</span>
            <span class="text-gray-800">${formatFieldValue(value, field)}</span>
          </div>`;
      });
      disclosureHtml += '</div></div>';
    }
    
    // Process optional fields (disclosed)
    const optional = summary.optional || {};
    if (optional.disclosed && optional.disclosed.length > 0) {
      disclosureHtml += '<div class="disclosure-section">';
      disclosureHtml += '<h4 class="text-sm font-medium mb-2 text-purple-700">Optional Fields (Disclosed)</h4>';
      disclosureHtml += '<div class="grid grid-cols-2 gap-1">';
      optional.disclosed.forEach(field => {
        const value = optional.values[field] || '';
        disclosureHtml += `
          <div class="col-span-1 text-xs text-purple-800">${formatFieldName(field)}</div>
          <div class="col-span-1 text-xs flex items-center">
            <span class="text-green-600 mr-1">✓</span>
            <span class="text-gray-800">${formatFieldValue(value, field)}</span>
          </div>`;
      });
      disclosureHtml += '</div></div>';
    }
    
    // Process optional fields (missing but OK)
    if (optional.missing && optional.missing.length > 0) {
      disclosureHtml += '<div class="disclosure-section">';
      disclosureHtml += '<h4 class="text-sm font-medium mb-2 text-yellow-600">Optional Fields (Not Disclosed)</h4>';
      disclosureHtml += '<div class="grid grid-cols-2 gap-1">';
      optional.missing.forEach(field => {
        disclosureHtml += `
          <div class="col-span-1 text-xs text-yellow-700">${formatFieldName(field)}</div>
          <div class="col-span-1 text-xs flex items-center">
            <span class="text-yellow-600 mr-1">⚠️</span>
            <span class="text-gray-600">Not disclosed</span>
          </div>`;
      });
      disclosureHtml += '</div></div>';
    }
    
    // Process technical fields
    const technical = summary.technical || {};
    if (technical.disclosed && technical.disclosed.length > 0) {
      disclosureHtml += '<div class="disclosure-section">';
      disclosureHtml += '<h4 class="text-sm font-medium mb-2 text-gray-600">Technical Fields</h4>';
      disclosureHtml += '<div class="grid grid-cols-2 gap-1">';
      technical.disclosed.forEach(field => {
        const value = technical.values[field] || '';
        
        disclosureHtml += `
          <div class="col-span-1 text-xs text-gray-700">${formatFieldName(field)}</div>
          <div class="col-span-1 text-xs flex items-center">
            <span class="text-green-600 mr-1">✓</span>
            <span class="text-gray-500">${formatFieldValue(value, field)}</span>
          </div>`;
      });
      disclosureHtml += '</div></div>';
    }
    
    disclosureHtml += '</div>';
    
    // Add the disclosure summary to the page
    disclosureElement.innerHTML = disclosureHtml;
    disclosureElement.classList.remove('hidden');
    
    // Add disclosure entry to status feed
    const totalDisclosed = 
      (mandatory.disclosed?.length || 0) + 
      (optional.disclosed?.length || 0);
    const totalFields = 
      totalDisclosed + 
      (mandatory.missing?.length || 0) + 
      (optional.missing?.length || 0);
    
    addStatusFeedEntry(`📋 Disclosed ${totalDisclosed}/${totalFields} fields`, 'info');
    
    // Show the metadata
    if (credentialData.metadata) {
      const metadata = credentialData.metadata;
      let metadataHtml = '<div class="disclosure-section mt-4">';
      metadataHtml += '<h4 class="text-sm font-medium mb-2 text-gray-700">Credential Metadata</h4>';
      metadataHtml += '<div class="grid grid-cols-2 gap-1">';
      
      if (metadata.issuer) {
        metadataHtml += `
          <div class="col-span-1 text-xs text-gray-700">Issuer</div>
          <div class="col-span-1 text-xs text-gray-800">${metadata.issuer}</div>`;
      }
      
      if (metadata.issued_date) {
        const date = new Date(metadata.issued_date * 1000).toLocaleString();
        metadataHtml += `
          <div class="col-span-1 text-xs text-gray-700">Issued Date</div>
          <div class="col-span-1 text-xs text-gray-800">${date}</div>`;
      }
      
      if (metadata.expires) {
        const date = new Date(metadata.expires * 1000).toLocaleString();
        metadataHtml += `
          <div class="col-span-1 text-xs text-gray-700">Expires</div>
          <div class="col-span-1 text-xs text-gray-800">${date}</div>`;
      }
      
      metadataHtml += '</div></div>';
      
      // Add metadata to the disclosure element
      disclosureElement.innerHTML += metadataHtml;
    }
  } catch (error) {
    console.error('Error displaying disclosure results:', error);
    addStatusFeedEntry('⚠️ Error displaying disclosure information', 'warning');
  }
}

/**
 * Display the actual transmitted field values in the enhanced UI
 */
function displayTransmittedFields(transmittedFields) {
  try {
    console.log('Transmitted fields received:', transmittedFields);
    
    const values = transmittedFields.values || {};
    const technicalFields = transmittedFields.technical || [];
    const personalFields = transmittedFields.personal || [];
    const additionalFields = transmittedFields.additional || [];
    
    console.log('Field counts from backend:', {
      technical: technicalFields.length,
      personal: personalFields.length, 
      additional: additionalFields.length
    });
    
    // Show the transmitted fields section
    const transmittedSection = document.getElementById('transmitted-fields-section');
    if (transmittedSection) {
      transmittedSection.style.display = 'block';
    }
    
    // Display technical fields
    displayFieldCategory('technical-fields-container', technicalFields, values, 'technical');
    
    // Display personal fields if any
    if (personalFields.length > 0) {
      document.getElementById('personal-fields-category').style.display = 'block';
      displayFieldCategory('personal-fields-container', personalFields, values, 'personal');
    }
    
    // Display additional fields if any
    if (additionalFields.length > 0) {
      document.getElementById('additional-fields-category').style.display = 'block';
      displayFieldCategory('additional-fields-container', additionalFields, values, 'additional');
    }
    
    // Use the actual field counts from backend categorization
    const totalFields = technicalFields.length + personalFields.length + additionalFields.length;
    addStatusFeedEntry(`📊 ${totalFields} Felder übertragen (${technicalFields.length} technische, ${personalFields.length} persönliche)`, 'info');
    
  } catch (error) {
    console.error('Error displaying transmitted fields:', error);
    addStatusFeedEntry('⚠️ Fehler beim Anzeigen der übertragenen Daten', 'warning');
  }
}

/**
 * Display a category of fields with their values
 */
function displayFieldCategory(containerId, fields, values, category) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  console.log(`displayFieldCategory - ${category} fields:`, fields);
  console.log(`displayFieldCategory - Values structure:`, values);
  
  container.innerHTML = '';
  
  // Process the field list
  fields.forEach(field => {
    let fieldValue = null;
    let displayFieldName = field;
    
    // Handle vc.credentialSubject.fieldName structure
    if (field.startsWith('vc.credentialSubject.')) {
      const fieldKey = field.replace('vc.credentialSubject.', '');
      if (values.vc && values.vc.credentialSubject && values.vc.credentialSubject[fieldKey] !== undefined) {
        fieldValue = values.vc.credentialSubject[fieldKey];
        displayFieldName = fieldKey; // Use clean field name for display
        console.log(`Found vc.credentialSubject field ${fieldKey} with value:`, fieldValue);
      }
    }
    // Handle credentialSubject.fieldName structure
    else if (field.startsWith('credentialSubject.')) {
      const fieldKey = field.replace('credentialSubject.', '');
      if (values.credentialSubject && values.credentialSubject[fieldKey] !== undefined) {
        fieldValue = values.credentialSubject[fieldKey];
        displayFieldName = fieldKey; // Use clean field name for display
        console.log(`Found credentialSubject field ${fieldKey} with value:`, fieldValue);
      }
    }
    // Handle direct field access
    else {
      fieldValue = values[field];
      if (fieldValue !== undefined && fieldValue !== null) {
        console.log(`Found direct field ${field} with value:`, fieldValue);
      }
    }
    
    // Create and display the field element if we have a value
    if (fieldValue !== undefined && fieldValue !== null) {
      const fieldElement = createFieldValueElement(displayFieldName, fieldValue, category);
      container.appendChild(fieldElement);
    }
  });
}

/**
 * Create a field value display element
 */
function createFieldValueElement(field, value, category) {
  const fieldDiv = document.createElement('div');
  fieldDiv.className = `field-value-item ${category}`;
  
  // Get friendly field name
  const displayName = getFieldDisplayName(field);
  
  // Format the value
  const formattedValue = formatFieldValueForDisplay(value, field);
  
  // Get value type
  const valueType = getValueType(value);
  
  // Generate unique ID for this field
  const fieldId = `field-${Math.random().toString(36).substr(2, 9)}`;
  
  fieldDiv.innerHTML = `
    <div class="field-value-header">
      <div class="field-value-label">
        <i class="fas ${getFieldIcon(field)}"></i>
        ${displayName}
      </div>
    </div>
    <div class="field-value-content" id="${fieldId}" data-raw-value="${escapeHtml(value.toString())}" onclick="selectFieldContent('${fieldId}')" title="Klicken um zu markieren, Strg+C zum Kopieren">
      ${formattedValue}
      <button class="copy-button" onclick="copyFieldValue(event, '${fieldId}')" title="Kopieren">
        <i class="fas fa-copy"></i>
      </button>
      <div class="copy-feedback">Kopiert!</div>
    </div>
    <div class="field-value-type">${valueType}</div>
  `;
  
  return fieldDiv;
}

/**
 * Get a user-friendly display name for a field
 */
function getFieldDisplayName(field) {
  const displayNames = {
    // Technical fields
    'total_messages': 'Nachrichten-Anzahl',
    'totalMessages': 'Nachrichten-Anzahl',
    'bbs_dpk': 'BBS+ Öffentlicher Schlüssel',
    'bbsDPK': 'BBS+ Öffentlicher Schlüssel',
    'iss': 'Aussteller-ID',
    'sub': 'Inhaber-ID',
    'nonce': 'Sicherheits-Token',
    'signed_nonce': 'Signierter Token',
    'signedNonce': 'Signierter Token',
    'validity_identifier': 'Gültigkeits-ID',
    'validityIdentifier': 'Gültigkeits-ID',
    'exp': 'Ablaufzeit',
    'nbf': 'Gültig ab',
    'jti': 'Token-ID',
    
    // Personal fields
    'firstName': 'Vorname',
    'lastName': 'Nachname',
    'studentId': 'Studenten-ID',
    'studentIdPrefix': 'ID-Präfix',
    'email': 'E-Mail-Adresse',
    'dateOfBirth': 'Geburtsdatum',
    'studyProgram': 'Studiengang',
    'faculty': 'Fakultät',
    'enrollmentDate': 'Einschreibungsdatum',
    'expectedGraduation': 'Erwarteter Abschluss',
    'studentStatus': 'Studierendenstatus',
    'academicLevel': 'Akademischer Level',
    
    // Credential path fields
    'vc.credentialSubject.firstName': 'Vorname',
    'vc.credentialSubject.lastName': 'Nachname',
    'vc.credentialSubject.studentId': 'Studenten-ID',
    'vc.credentialSubject.studentIdPrefix': 'ID-Präfix',
    'vc.credentialSubject.email': 'E-Mail-Adresse',
    'vc.credentialSubject.dateOfBirth': 'Geburtsdatum',
    'vc.credentialSubject.studyProgram': 'Studiengang',
    'vc.credentialSubject.faculty': 'Fakultät'
  };
  
  return displayNames[field] || field.replace(/^vc\.credentialSubject\./, '').replace(/([a-z])([A-Z])/g, '$1 $2');
}

/**
 * Get an appropriate icon for a field
 */
function getFieldIcon(field) {
  if (field.includes('iss') || field.includes('issuer')) return 'fa-certificate';
  if (field.includes('sub') || field.includes('holder')) return 'fa-user';
  if (field.includes('exp') || field.includes('Date')) return 'fa-calendar';
  if (field.includes('nonce') || field.includes('token')) return 'fa-key';
  if (field.includes('bbs') || field.includes('dpk')) return 'fa-shield-alt';
  if (field.includes('validity')) return 'fa-check-circle';
  if (field.includes('firstName') || field.includes('lastName')) return 'fa-user-tag';
  if (field.includes('studentId') || field.includes('student')) return 'fa-id-card';
  if (field.includes('email')) return 'fa-envelope';
  if (field.includes('study') || field.includes('faculty')) return 'fa-graduation-cap';
  return 'fa-info-circle';
}

/**
 * Format field value for user-friendly display
 */
function formatFieldValueForDisplay(value, field) {
  if (value === null || value === undefined) {
    return '<em>Nicht verfügbar</em>';
  }
  
  // Handle dates
  if (field.includes('Date') || field.includes('date') || field.includes('exp') || field.includes('nbf')) {
    const timestamp = parseInt(value);
    if (!isNaN(timestamp) && timestamp > 1000000000) {
      return new Date(timestamp * 1000).toLocaleString('de-DE');
    }
    
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toLocaleString('de-DE');
    }
  }
  
  // Truncate very long values (like keys and hashes)
  const technicalFields = ['bbs_dpk', 'bbsDPK', 'iss', 'sub', 'signed_nonce', 'signedNonce', 'validity_identifier', 'validityIdentifier', 'jti'];
  if (technicalFields.some(tech => field.includes(tech))) {
    const str = value.toString();
    if (str.length > 40) {
      return str.substring(0, 20) + '...' + str.substring(str.length - 10);
    }
  }
  
  // Handle JSON objects
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  
  return value.toString();
}

/**
 * Get the type of a value for display
 */
function getValueType(value) {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'string') {
    if (value.length > 50) return `string (${value.length} Zeichen)`;
    return 'string';
  }
  if (typeof value === 'number') {
    if (Number.isInteger(value) && value > 1000000000 && value < 2000000000) {
      return 'timestamp';
    }
    return 'number';
  }
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'object') return 'object';
  return typeof value;
}

/**
 * Copy field value to clipboard
 */
function copyFieldValue(event, fieldId) {
  event.stopPropagation();
  
  const fieldElement = document.getElementById(fieldId);
  const rawValue = fieldElement.getAttribute('data-raw-value');
  
  // Try to copy using the modern Clipboard API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(rawValue).then(() => {
      showCopyFeedback(fieldElement);
    }).catch(err => {
      console.error('Failed to copy via Clipboard API:', err);
      fallbackCopy(rawValue, fieldElement);
    });
  } else {
    fallbackCopy(rawValue, fieldElement);
  }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopy(text, fieldElement) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    document.execCommand('copy');
    showCopyFeedback(fieldElement);
  } catch (err) {
    console.error('Fallback copy failed:', err);
  } finally {
    document.body.removeChild(textArea);
  }
}

/**
 * Select field content for manual copying
 */
function selectFieldContent(fieldId) {
  const fieldElement = document.getElementById(fieldId);
  const range = document.createRange();
  range.selectNodeContents(fieldElement);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

/**
 * Show copy feedback animation
 */
function showCopyFeedback(fieldElement) {
  const feedback = fieldElement.querySelector('.copy-feedback');
  const button = fieldElement.querySelector('.copy-button');
  
  // Show feedback
  feedback.classList.add('show');
  button.classList.add('copied');
  
  // Hide after 1.5 seconds
  setTimeout(() => {
    feedback.classList.remove('show');
    button.classList.remove('copied');
  }, 1500);
}

/**
 * Escape HTML for safe insertion
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Display errors from selective disclosure validation
 */
function displayDisclosureErrors(validationData) {
  try {
    if (!validationData) return;
    
    const errors = validationData.errors || [];
    const results = validationData.results || {};
    
    // Add error entries to the status feed
    errors.forEach(error => {
      addStatusFeedEntry(`❌ ${error}`, 'error');
    });
    
    // Display missing mandatory fields
    const missingMandatory = Object.entries(results)
      .filter(([_, result]) => result.status === 'missing_mandatory')
      .map(([field, _]) => formatFieldName(field));
    
    if (missingMandatory.length > 0) {
      addStatusFeedEntry(`❌ Missing mandatory fields: ${missingMandatory.join(', ')}`, 'error');
    }
    
  } catch (error) {
    console.error('Error displaying disclosure errors:', error);
    addStatusFeedEntry('⚠️ Error processing disclosure validation', 'warning');
  }
} 
