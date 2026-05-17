// Tailwind Konfiguration
if (typeof tailwind !== 'undefined') {
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          'berlin-blue': '#003f7f',
          'berlin-light': '#0066cc',
          'berlin-dark': '#002d5d'
        },
        animation: {
          'fade-in-down': 'fadeInDown 0.2s ease-out',
        },
        keyframes: {
          fadeInDown: {
            '0%': { opacity: '0', transform: 'translateY(-5px)' },
            '100%': { opacity: '1', transform: 'translateY(0)' },
          }
        }
      }
    }
  };
}

// PRÄZISE HERZCHIRURGISCHE FUNKTION FÜR ZUFALLSDATEN
function fillRandomData() {
  try {
    console.log("[Herzchirurg] Operation Zufallsdaten wird durchgeführt...");
    
    // Präzise ausgewählte Vornamen und Nachnamen
    const vorname = [
      'Anna', 'Max', 'Laura', 'Felix', 'Sophie', 'Leon', 'Emma', 'Paul', 'Julia', 'Lukas',
      'Lena', 'Jonas', 'Hannah', 'Niklas', 'Leonie', 'Tim', 'Marie', 'Jan', 'Sarah', 'Philipp'
    ];
    
    const nachname = [
      'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker',
      'Schulz', 'Hoffmann', 'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf'
    ];
    
    // PRÄZISE Berechnung der Zufallswerte mit 100% Erfolgsgarantie
    const randomFirstName = vorname[Math.floor(Math.random() * vorname.length)];
    const randomLastName = nachname[Math.floor(Math.random() * nachname.length)];
    const randomStudentId = Math.floor(100000 + Math.random() * 900000).toString();
    const randomStudentIdPrefix = Math.floor(10000 + Math.random() * 90000).toString();
    
    console.log("[Herzchirurg] Generierte Daten: " + randomFirstName + " " + randomLastName + ", ID: " + randomStudentId + ", Prefix: " + randomStudentIdPrefix);
    
    // DIREKTE und PRÄZISE DOM-Manipulation - jedes Element einzeln mit Fehlerprüfung
    const firstNameInput = document.getElementById("firstName");
    if (firstNameInput) {
      firstNameInput.value = randomFirstName;
      console.log("[Herzchirurg] Vorname gesetzt: " + randomFirstName);
    }
    
    const lastNameInput = document.getElementById("lastName");
    if (lastNameInput) {
      lastNameInput.value = randomLastName;
      console.log("[Herzchirurg] Nachname gesetzt: " + randomLastName);
    }
    
    const studentIdInput = document.getElementById("studentId");
    if (studentIdInput) {
      studentIdInput.value = randomStudentId;
      console.log("[Herzchirurg] StudentID gesetzt: " + randomStudentId);
    }
    
    const studentIdPrefixInput = document.getElementById("studentIdPrefix");
    if (studentIdPrefixInput) {
      studentIdPrefixInput.value = randomStudentIdPrefix;
      console.log("[Herzchirurg] StudentID-Prefix gesetzt: " + randomStudentIdPrefix);
    }
    
    // Berlin-Blau Farbwerte setzen
    document.getElementById('bg_color_card').value = '003f7f';
    document.getElementById('fg_color_title').value = 'FFFFFF';
    document.getElementById('accent_color').value = 'E6007E';
    document.getElementById('text_color').value = '333333';
    
    // DOPPELTE visuelle Bestätigung
    const randomBtn = document.getElementById('randomDataBtn');
    if (randomBtn) {
      // Grünes Feedback für Erfolg
      randomBtn.classList.add('bg-green-100', 'text-green-800', 'border-green-300');
      randomBtn.innerHTML = '<i class="fas fa-check mr-1"></i> Daten gesetzt';
      
      // Nach 800ms zurücksetzen
      setTimeout(() => {
        randomBtn.classList.remove('bg-green-100', 'text-green-800', 'border-green-300');
        randomBtn.innerHTML = '<i class="fas fa-random mr-1"></i> Zufäll. Daten';
      }, 800);
    }
    
    console.log("[Herzchirurg] Operation Zufallsdaten ERFOLGREICH abgeschlossen ✓");
    return true;
  } catch (fehler) {
    console.error("[Herzchirurg] FEHLER bei Zufallsdaten:", fehler);
    alert("Die Zufallsdaten konnten nicht gesetzt werden. Bitte kontaktieren Sie den Herzchirurgen.");
    return false;
  }
}

// Verbesserte Funktion zur Angleichung der Höhen in den Spalten
function adjustHeight() {
  const leftColumn = document.querySelector('.grid > div:first-child');
  const rightColumn = document.querySelector('.grid > div:last-child');
  
  if (leftColumn && rightColumn && window.innerWidth >= 1024) { // lg breakpoint
    // Berechnet die Höhe ohne den Details-Bereich, falls dieser geöffnet ist
    const detailsElement = leftColumn.querySelector('details');
    let leftHeight = leftColumn.offsetHeight;
    
    // Wenn Details geöffnet ist, ziehe dessen Höhe ab
    if (detailsElement && detailsElement.open) {
      const detailsContent = detailsElement.querySelector('summary + div');
      if (detailsContent) {
        leftHeight = leftHeight - detailsContent.offsetHeight;
      }
    }
    
    const mainRightPanel = rightColumn.querySelector('div:first-child');
    
    if (mainRightPanel) {
      mainRightPanel.style.minHeight = `${leftHeight}px`;
    }
  }
}

// Details Element Animation und Auto-Scroll
function setupDetailsAnimation() {
  const detailsElement = document.querySelector('details');
  if (detailsElement) {
    detailsElement.addEventListener('toggle', function() {
      // Wenn Details geöffnet wird, scrolle um sicherzustellen, dass der neue Inhalt sichtbar ist
      if (this.open) {
        setTimeout(() => {
          this.scrollIntoView({ behavior: 'smooth', block: 'start' });
          adjustHeight(); // Aktualisiere die Höhen nach dem Aufklappen
        }, 100);
      } else {
        // Wenn geschlossen, aktualisiere ebenfalls die Höhen
        setTimeout(() => {
          adjustHeight();
        }, 100);
      }
    });
  }
}

// Bildupload-Funktionalität für Studierendenfoto
function setupStudentPhotoUpload() {
  const profileImageInput = document.getElementById('profileImage');
  const imagePreview = document.getElementById('imagePreview');
  const resetImageBtn = document.getElementById('resetImageBtn');
  
  // Funktion zur Vorschau des ausgewählten Bildes
  function previewStudentPhoto(file) {
    if (file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        imagePreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  }
  
  // Event-Listener für Dateiauswahl
  if (profileImageInput) {
    profileImageInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        previewStudentPhoto(this.files[0]);
      }
    });
  }
  
  // Reset-Button Funktionalität
  if (resetImageBtn) {
    resetImageBtn.addEventListener('click', function() {
      imagePreview.src = '/static/student.png';
      if (profileImageInput) {
        profileImageInput.value = '';
      }
    });
  }
}

// University Logo Upload- und Preview-Funktionalität
function setupUniversityLogoUpload() {
  const themeIconInput = document.getElementById('theme_icon');
  const themeIconPreview = document.getElementById('themeIconPreview');
  const resetThemeIconBtn = document.getElementById('resetThemeIconBtn');
  
  // Funktion zur Vorschau des ausgewählten Bildes
  function previewUniversityLogo(file) {
    if (file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        themeIconPreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  }
  
  // Event-Listener für Dateiauswahl
  if (themeIconInput) {
    themeIconInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        previewUniversityLogo(this.files[0]);
      }
    });
  }
  
  // Reset-Button Funktionalität
  if (resetThemeIconBtn) {
    resetThemeIconBtn.addEventListener('click', function() {
      themeIconPreview.src = '/static/viable-credentials-logo-sora-cropped-darkmode.png';
      if (themeIconInput) {
        themeIconInput.value = '';
      }
    });
  }
}

// Funktion zum Drucken des QR-Codes und der Daten
function printCredential() {
  // Erstellen einer Druck-optimierten Ansicht
  const printWindow = window.open('', '_blank');
  
  if (!printWindow) {
    alert("Bitte erlauben Sie Pop-ups, um den QR-Code drucken zu können.");
    return;
  }
  
  // QR Code aus dem DOM holen
  const qrCodeImg = document.getElementById('picture');
  const qrCodeSrc = qrCodeImg ? qrCodeImg.src : '';
  
  // Formulardaten sammeln - Servereitige form_data oder direkt aus dem DOM
  let firstName, lastName, studentId, studentIdPrefix, themeName;
  
  // Lese die Werte entweder aus den vorausgefüllten Feldern oder direkt aus den Eingabefeldern
  firstName = document.getElementById('firstName').value || document.getElementById('firstName').placeholder;
  lastName = document.getElementById('lastName').value || document.getElementById('lastName').placeholder;
  studentId = document.getElementById('studentId').value || document.getElementById('studentId').placeholder;
  studentIdPrefix = document.getElementById('studentIdPrefix').value || document.getElementById('studentIdPrefix').placeholder;
  themeName = document.getElementById('theme_name').value || '';
  
  // Einfache HTML-Escape-Funktion für Sicherheit
  function escape(s) {
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
  }
  
  // Druckbares HTML generieren
  const html = `
    <!DOCTYPE html>
    <html lang="de">
    <head>
      <meta charset="UTF-8">
      <title>VIABLE Credentials für ${escape(firstName)} ${escape(lastName)}</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 2cm;
          color: #333;
        }
        .container {
          max-width: 800px;
          margin: 0 auto;
        }
        .header {
          border-bottom: 2px solid #003f7f;
          padding-bottom: 15px;
          margin-bottom: 20px;
        }
        .header h1 {
          color: #003f7f;
          margin: 0;
        }
        .qr-section {
          display: flex;
          margin-bottom: 30px;
        }
        .qr-code {
          flex: 0 0 200px;
          margin-right: 20px;
        }
        .qr-code img {
          max-width: 100%;
          border: 1px solid #ddd;
          padding: 10px;
          background: white;
        }
        .student-info {
          flex: 1;
        }
        .info-table {
          width: 100%;
          border-collapse: collapse;
        }
        .info-table th, .info-table td {
          border: 1px solid #ddd;
          padding: 8px 12px;
          text-align: left;
        }
        .info-table th {
          background-color: #f9f9f9;
          width: 40%;
        }
        .footer {
          margin-top: 40px;
          font-size: 12px;
          color: #666;
          text-align: center;
        }
        .instructions {
          background-color: #f0f4ff;
          border-left: 4px solid #003f7f;
          padding: 15px;
          margin: 20px 0;
          font-size: 14px;
        }
        @media print {
          body {
            margin: 1cm;
          }
          .no-print {
            display: none;
          }
          button {
            display: none;
          }
          .instructions {
            border: 1px solid #ddd;
            background-color: #f9f9f9;
          }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Verifiable Credential - Studierendenausweis</h1>
          <p>${themeName ? escape(themeName) : 'Technische Universität Berlin'}</p>
        </div>
        
        <div class="qr-section">
          <div class="qr-code">
            <img src="${qrCodeSrc}" alt="QR Code für Credentials">
          </div>
          <div class="student-info">
            <h2>Studierendendendaten</h2>
            <table class="info-table">
              <tr>
                <th>Vorname</th>
                <td>${escape(firstName)}</td>
              </tr>
              <tr>
                <th>Nachname</th>
                <td>${escape(lastName)}</td>
              </tr>
              <tr>
                <th>Matrikelnummer</th>
                <td>${escape(studentId)}</td>
              </tr>
              <tr>
                <th>Matrikelnummer-Präfix</th>
                <td>${escape(studentIdPrefix)}</td>
              </tr>
            </table>
          </div>
        </div>
        
        <div class="instructions">
          <h3>Anleitung zum Import in Ihre Wallet-App</h3>
          <ol>
            <li>Öffnen Sie Ihre VIABLE Credentials Wallet App</li>
            <li>Scannen Sie den QR-Code mit der "Credential hinzufügen" Funktion</li>
            <li>Bestätigen Sie den Import in Ihre Wallet</li>
            <li>Ihr digitaler Studierendenausweis ist nun einsatzbereit!</li>
          </ol>
        </div>
        
        <div class="footer">
          <p>Dieses Credential wurde mit BBS+ Signaturen erstellt und ist kryptographisch überprüfbar.</p>
          <p>© ${new Date().getFullYear()} VIABLE Credentials</p>
        </div>
      </div>
      
      <script>
        window.onload = function() {
          // Automatisch drucken, wenn alles geladen ist
          window.print();
        }
      </script>
    </body>
    </html>
  `;
  
  printWindow.document.write(html);
  printWindow.document.close();
}

// Führt die Funktionen aus, wenn das Dokument geladen ist
document.addEventListener('DOMContentLoaded', function() {
  console.log("[Herzchirurg] DOM vollständig geladen, initialisiere Funktionen...");
  
  // Initialisierung der Bild-Upload-Funktionen
  setupStudentPhotoUpload();
  setupUniversityLogoUpload();
  
  // Event-Listener für den Zufallsdaten-Button - REDUNDANTE SICHERHEIT
  const randomDataBtn = document.getElementById('randomDataBtn');
  if (randomDataBtn) {
    randomDataBtn.addEventListener('click', function(event) {
      event.preventDefault();
      fillRandomData();
      return false;
    });
    console.log("[Herzchirurg] Random-Data-Button erfolgreich mit Event-Listener initialisiert");
  }
  
  // HERZCHIRURG: FINALE ÜBERPRÜFUNG DES BUTTONS NACH TIMEOUT
  setTimeout(() => {
    const btnCheck = document.getElementById('randomDataBtn');
    if (btnCheck) {
      console.log("[Herzchirurg] FINALE Überprüfung: Random-Data-Button existiert ✓");
      // Zusätzliche Sicherheit durch direktes Zuweisen der onclick-Funktion
      btnCheck.onclick = function(e) {
        if(e) e.preventDefault();
        console.log("[Herzchirurg] Button wurde über onclick-Fallback geklickt");
        return fillRandomData();
      };
    } else {
      console.error("[Herzchirurg] WARNUNG: Button konnte nicht gefunden werden!");
    }
  }, 500);
});

// HERZCHIRURG: GLOBALE NOTFALLFUNKTION FÜR DEN ZUFALLSDATEN-BUTTON
window.notfallRandomDaten = function() {
  console.log("[Herzchirurg] NOTFALL-FUNKTION AKTIVIERT");
  return fillRandomData();
}; 