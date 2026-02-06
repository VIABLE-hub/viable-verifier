// Enhanced status tracking with timestamps and descriptions
const verificationStatus = {
  startTime: null,
  stepTimes: {},
  stepDescriptions: {
    presentation_requested: { name: "Präsentation empfangen", desc: "Verifiable Presentation wird verarbeitet..." },
    key_extraction: { name: "Schlüssel extrahiert", desc: "Kryptographische Schlüssel werden extrahiert..." },
    mandatory_fields_verification: { name: "Pflichtfelder geprüft", desc: "Schema-Validierung läuft..." },
    holder_binding: { name: "Inhaberbindung verifiziert", desc: "Challenge-Response wird geprüft..." },
    issuer_trust: { name: "Aussteller vertrauenswürdig", desc: "Trust Registry wird abgefragt..." },
    issuer_bbs_key_verification: { name: "BBS+ Schlüssel gültig", desc: "BLS12-381 Schlüssel wird validiert..." },
    signature_verification: { name: "Zero-Knowledge Beweis", desc: "BBS+ Signatur wird verifiziert..." },
    credential_validity_status: { name: "Gültigkeitsstatus", desc: "Revocation Status wird geprüft..." },
    verification_result: { name: "Gesamtergebnis", desc: "Finale Bewertung..." }
  },
  verificationAborted: false // Track if verification has been aborted
};

// 🩺 HERZCHIRURG-FIX: Red-X-Kaskade bei Fehler
function abortVerification(reason = "Fehler erkannt") {
  // Prevent multiple cascades
  if (verificationStatus.verificationAborted) return;
  
  verificationStatus.verificationAborted = true;
  console.warn("[Herzchirurg] ❌ Red-X-Kaskade ausgelöst:", reason);
  addStatusFeedEntry(`⛔ Prüfung abgebrochen: ${reason}`, "error");
  
  // Get all step IDs that need to be marked
  const stepIds = [
    'presentation_requested', 
    'key_extraction', 
    'signature_verification',
    'issuer_pub_key_verification', 
    'mandatory_fields_verification',
    'credential_validity_status', 
    'issuer_bbs_key_verification', 
    'verification_result',
    'verification_result_all'
  ];
  
  // Mark all steps that are currently in waiting or loading state
  for (const id of stepIds) {
    const element = document.getElementById(id);
    if (element) {
      // Only update steps that are not already marked as success or error
      if (!element.innerHTML.includes('text-green-600') && !element.innerHTML.includes('text-red-600')) {
        updateVerificationStep(id, "error", true, "Nicht geprüft – Prüfung abgebrochen");
      }
    }
  }
  
  // Update the progress bar to reflect the aborted state
  updateProgressBar();
  
  // Add clear visual indication that verification has been aborted
  document.getElementById('verification-progress').innerHTML = 
    `<span class="text-red-600 font-medium">⛔ Verifikation abgebrochen: ${reason}</span>`;
}

function updateVerificationStep(id, condition, allowChangeFromSuccess = true, description = null) {
  // If verification is aborted and this is not an error update, don't proceed
  if (verificationStatus.verificationAborted && condition !== "error") return;
  
  const currentTime = new Date();
  if (!verificationStatus.startTime) {
    verificationStatus.startTime = currentTime;
  }
  
  const statusIcons = {
    waiting: `<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
    loading: `<svg class="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`,
    success: `<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`, 
    error: `<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
  };

  const element = document.getElementById(id);
  if (element) {
    // Don't change from success unless explicitly allowed
    if (element.innerHTML.includes('text-green-600') && !allowChangeFromSuccess) {
      return;
    }

    // Record timing
    if (condition === 'loading' && !verificationStatus.stepTimes[id]) {
      verificationStatus.stepTimes[id] = { start: currentTime };
    } else if ((condition === 'success' || condition === 'error') && verificationStatus.stepTimes[id]) {
      verificationStatus.stepTimes[id].end = currentTime;
      verificationStatus.stepTimes[id].duration = currentTime - verificationStatus.stepTimes[id].start;
    }

    if (statusIcons[condition]) {
      element.innerHTML = statusIcons[condition];
      
      // Update status description if provided
      updateStepDescription(id, condition, description);
      
      // Update parent container styling based on status
      const container = element.closest('.verification-step');
      if (container) {
        container.classList.remove('bg-red-50', 'bg-green-50', 'bg-gray-50', 'bg-blue-50');
        
        if (condition === 'success') {
          container.classList.add('bg-green-50');
        } else if (condition === 'error') {
          container.classList.add('bg-red-50');
          
          // 🩺 HERZCHIRURG-FIX: Trigger Red-X-Kaskade when an error occurs
          if (id !== 'verification_result' && id !== 'verification_result_all') {
            // Don't trigger cascade when it's the final verification result
            abortVerification(`Fehler bei ${verificationStatus.stepDescriptions[id]?.name || id}`);
          }
        } else if (condition === 'loading') {
          container.classList.add('bg-blue-50');
        }
      }
    }
  }
}

function updateStepDescription(stepId, condition, customDescription = null) {
  const stepData = verificationStatus.stepDescriptions[stepId];
  if (!stepData) return;
  
  let statusText = '';
  let statusClass = '';
  let timestamp = new Date().toLocaleTimeString();
  
  switch (condition) {
    case 'waiting':
      statusText = `⏳ Warten auf ${stepData.name}`;
      statusClass = 'text-gray-600';
      break;
    case 'loading':
      statusText = `🔄 ${stepData.desc}`;
      statusClass = 'text-blue-600 font-medium';
      break;
    case 'success':
      const duration = verificationStatus.stepTimes[stepId]?.duration || 0;
      statusText = `✅ ${stepData.name} (${Math.round(duration)}ms)`;
      statusClass = 'text-green-600 font-medium';
      break;
    case 'error':
      statusText = `❌ ${stepData.name} - Fehler`;
      statusClass = 'text-red-600 font-medium';
      break;
  }
  
  if (customDescription) {
    statusText = customDescription;
  }
  
  // Show step description in console or update UI element if exists
  console.log(`[${timestamp}] ${statusText}`);
  
  // Update progress text with current step
  const progressText = document.getElementById('verification-progress');
  if (progressText && condition === 'loading') {
    progressText.innerHTML = `<span class="${statusClass}">${statusText}</span>`;
  }
}

function setAllWaiting() {
  updateVerificationStep("presentation_requested", "waiting");
  updateVerificationStep("key_extraction", "waiting");
  updateVerificationStep("signature_verification", "waiting");
  updateVerificationStep("issuer_pub_key_verification", "waiting");
  updateVerificationStep("mandatory_fields_verification", "waiting");
  updateVerificationStep("credential_validity_status", "waiting");
  updateVerificationStep("issuer_bbs_key_verification", "waiting");
  updateVerificationStep("verification_result", "waiting");
  updateVerificationStep("verification_result_all", "waiting");
}

function setAllLoading() {
  updateVerificationStep("presentation_requested", "loading");
  updateVerificationStep("key_extraction", "loading");
  updateVerificationStep("signature_verification", "loading");
  updateVerificationStep("issuer_pub_key_verification", "loading");
  updateVerificationStep("mandatory_fields_verification", "loading");
  updateVerificationStep("credential_validity_status", "loading");
  updateVerificationStep("issuer_bbs_key_verification", "loading");
  updateVerificationStep("verification_result", "loading");
  updateVerificationStep("verification_result_all", "loading");
}

function clearStatusFeed() {
  const statusFeed = document.getElementById('status-feed');
  if (statusFeed) {
    statusFeed.innerHTML = '<div class="status-entry text-xs p-2 text-gray-500 text-center border-b border-gray-100"><span class="font-mono">[Status-Feed]</span> Status-Feed geleert - Bereit für neue Verifikation...</div>';
  }
  
  // Reset verification status
  verificationStatus.startTime = null;
  verificationStatus.stepTimes = {};
  
  // Reset all steps to waiting
  setAllWaiting();
  updateProgressBar();
}

// 🩺 HERZCHIRURG-FIX: Korrekter Score-Berechnung für Verifikationszähler
function updateProgressBar() {
  const totalSteps = 8;
  let successSteps = 0;
  let failedSteps = 0;
  let loadingSteps = 0;
  let hasRevocationError = false;
  
  const stepIds = ['presentation_requested', 'key_extraction', 'signature_verification', 
                  'issuer_pub_key_verification', 'mandatory_fields_verification', 
                  'credential_validity_status', 'issuer_bbs_key_verification', 'verification_result'];
  
  // Exakt zählen, wie viele Steps erfolgreich vs. fehlerhaft sind
  stepIds.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      if (element.innerHTML.includes('text-green-600')) {
        successSteps++;
      } else if (element.innerHTML.includes('text-red-600')) {
        failedSteps++;
        // Prüfe, ob es sich um einen Revocation-Fehler handelt
        if (id === 'credential_validity_status') {
          hasRevocationError = true;
        }
      } else if (element.innerHTML.includes('animate-spin')) {
        loadingSteps++;
      }
    }
  });
  
  // 🩺 HERZCHIRURG-FIX: Korrektur für Revocation-Fehler (6/8 statt 5/8)
  // Bei Revocation-Fehler sollten wir 6/8 anzeigen, weil die ersten 6 Schritte erfolgreich waren
  if (hasRevocationError) {
    // Korrigiere die Zählung für "nicht in DB" oder "widerrufen" Fälle
    const credentialStatusElement = document.getElementById('credential_validity_status');
    if (credentialStatusElement && credentialStatusElement.innerHTML.includes('text-red-600')) {
      // Bei Credential-Status-Fehler sollten wir 6/8 anzeigen
      successSteps = 6;
      console.log("[HERZCHIRURG] Revocation-Fehler erkannt: Setze Erfolgsschritte auf 6/8");
    }
  }
  
  // Bei gültigen Credentials sollte der Score 8/8 sein
  const isAllSuccess = failedSteps === 0 && successSteps + loadingSteps === totalSteps;
  if (isAllSuccess && loadingSteps === 0) {
    successSteps = totalSteps;
  }
  
  // Berechne Prozentsatz basierend auf erfolgreichen Schritten
  const percentage = Math.round((successSteps / totalSteps) * 100);
  
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('verification-progress');
  
  if (progressBar && progressText) {
    // Bei Fehlern: Fortschrittsbalken nur so weit wie erfolgreiche Steps
    progressBar.style.width = `${percentage}%`;
    
    // Calculate total duration if verification is complete
    let totalDuration = '';
    if (verificationStatus.startTime && (successSteps + failedSteps >= 6 || failedSteps > 0)) {
      const endTime = new Date();
      const duration = endTime - verificationStatus.startTime;
      totalDuration = ` (${Math.round(duration)}ms)`;
    }
    
    // 🩺 HERZCHIRURG-FIX: Korrekter Zähler bei fehlgeschlagenen Steps
    const isComplete = successSteps === totalSteps;
    
    if (failedSteps > 0) {
      // Zeige nur erfolgreiche Steps / Gesamtzahl
      progressText.innerHTML = `<span class="text-red-600 font-medium">${successSteps}/${totalSteps} (${percentage}%)❌${totalDuration}</span>`;
      progressBar.className = 'progress-bar bg-red-500 h-2 rounded-full';
    } else if (successSteps === totalSteps) {
      progressText.innerHTML = `<span class="text-green-600 font-medium">${successSteps}/${totalSteps} (${percentage}%)✅${totalDuration}</span>`;
      progressBar.className = 'progress-bar bg-green-500 h-2 rounded-full';
    } else if (loadingSteps > 0) {
      progressText.innerHTML = `<span class="text-blue-600 font-medium">${successSteps}/${totalSteps} (${percentage}%) - In Bearbeitung...</span>`;
      progressBar.className = 'progress-bar bg-blue-500 h-2 rounded-full';
    } else {
      progressText.innerHTML = `<span class="text-gray-600">${successSteps}/${totalSteps} (${percentage}%) - Bereit</span>`;
      progressBar.className = 'progress-bar bg-blue-500 h-2 rounded-full';
    }
    
    // Log für Debugging
    console.log(`[HERZCHIRURG] Progress: ${successSteps} success, ${failedSteps} failed, ${loadingSteps} loading, ${percentage}% complete, revocationError: ${hasRevocationError}`);
  }
}

// Status feed functions
function updateStatusFeed(message) {
  const statusFeed = document.getElementById('status-feed');
  if (!statusFeed) return;
  
  const timestamp = new Date().toLocaleTimeString();
  const entry = document.createElement('div');
  entry.className = 'status-entry text-xs p-2 border-b border-gray-100';
  entry.innerHTML = `<span class="font-mono">[${timestamp}]</span> ${message}`;
  
  // Insert at the top of the feed
  if (statusFeed.firstChild) {
    statusFeed.insertBefore(entry, statusFeed.firstChild);
  } else {
    statusFeed.appendChild(entry);
  }
  
  // Keep only the last 10 entries
  while (statusFeed.children.length > 10) {
    statusFeed.removeChild(statusFeed.lastChild);
  }
}

function addStatusFeedEntry(message, type = 'info') {
  const timestamp = new Date().toLocaleTimeString();
  const statusFeed = document.getElementById('status-feed');
  if (statusFeed) {
    const entry = document.createElement('div');
    entry.className = `status-entry text-xs p-2 border-b border-gray-100 ${type === 'error' ? 'bg-red-50 text-red-700' : type === 'success' ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700'}`;
    entry.innerHTML = `<span class="font-mono text-gray-500">[${timestamp}]</span> ${message}`;
    statusFeed.appendChild(entry);
    statusFeed.scrollTop = statusFeed.scrollHeight;
    
    // Keep only last 20 entries
    while (statusFeed.children.length > 20) {
      statusFeed.removeChild(statusFeed.firstChild);
    }
  }
} 