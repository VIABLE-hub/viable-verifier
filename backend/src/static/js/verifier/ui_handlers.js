// Professional collapsible state management - ALL START CLOSED
const collapsibles = {
  'code-presentation': false,
  'code-key-extraction': false,
  'code-mandatory-fields': false,
  'code-holder-binding': false,
  'code-issuer-trust': false,
  'code-bbs-key': false,
  'code-signature': false,
  'code-credential-status': false
};

// Ensure all elements start in closed state
function initializeCodeSnippets() {
  Object.keys(collapsibles).forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.classList.remove('expanded');
      collapsibles[id] = false;
    }
  });
}

// Professional code snippet toggle functionality - ONLY SHOW ON CLICK
function toggleCodeSnippet(id) {
  const element = document.getElementById(id);
  if (element) {
    // Toggle state
    collapsibles[id] = !collapsibles[id];
    
    if (collapsibles[id]) {
      // Show: remove display:none and add expanded class
      element.style.display = '';
      element.classList.add('expanded');
    } else {
      // Hide: remove expanded class and add display:none
      element.classList.remove('expanded');
      setTimeout(() => {
        if (!element.classList.contains('expanded')) {
          element.style.display = 'none';
        }
      }, 300); // Wait for CSS transition to complete
    }
    
    // Update button icon state with smooth transition
    const button = document.querySelector(`[onclick="toggleCodeSnippet('${id}')"]`);
    if (button) {
      const icon = button.querySelector('svg');
      if (icon) {
        icon.style.transition = 'transform 0.3s ease-in-out';
        if (collapsibles[id]) {
          icon.style.transform = 'rotate(180deg)';
          button.setAttribute('title', 'Hide Code Details');
        } else {
          icon.style.transform = 'rotate(0deg)';
          button.setAttribute('title', 'Show Code Details');
        }
      }
    }
  }
}

// 🩺 HERZCHIRURG-FIX: Komplett neu implementierte Collapsible-Logik mit garantierter Funktionalität
function initializeCollapsibleGroups() {
  console.log("🩺 HERZCHIRURG: Initialisiere Collapsible-Gruppen");
  
  // Schließe zuerst alle Gruppen, um sauberen Ausgangszustand zu haben
  document.querySelectorAll('.collapsible-content').forEach(content => {
    content.classList.remove('expanded');
  });
  
  // Globaler State für aktuell geöffnete Gruppe
  let currentlyOpenGroup = null;
  
  document.querySelectorAll('.group-toggle').forEach(button => {
    button.addEventListener('click', function(e) {
      // Prevent default behavior and stop propagation
      e.preventDefault();
      e.stopPropagation();
      
      const groupId = this.getAttribute('data-group');
      console.log(`🩺 HERZCHIRURG: Toggle-Klick auf Gruppe ${groupId}`);
      
      const content = document.querySelector(`.collapsible-content[data-group="${groupId}"]`);
      const arrow = this.querySelector('svg:last-child');
      
      if (!content || !arrow) {
        console.error(`Missing content or arrow for group: ${groupId}`);
        return;
      }
      
      // Bestimme aktuellen Zustand
      const isCurrentlyExpanded = content.classList.contains('expanded');
      console.log(`🩺 HERZCHIRURG: Gruppe ${groupId} ist aktuell ${isCurrentlyExpanded ? 'geöffnet' : 'geschlossen'}`);
      
      // Schließe zuerst alle anderen geöffneten Gruppen
      document.querySelectorAll('.collapsible-content.expanded').forEach(openContent => {
        if (openContent !== content) {
          const openGroupId = openContent.getAttribute('data-group');
          const openButton = document.querySelector(`.group-toggle[data-group="${openGroupId}"]`);
          const openArrow = openButton ? openButton.querySelector('svg:last-child') : null;
          
          console.log(`🩺 HERZCHIRURG: Schließe andere geöffnete Gruppe ${openGroupId}`);
          
          // Schließe diese Gruppe
          openContent.classList.remove('expanded');
          if (openArrow) openArrow.style.transform = 'rotate(0deg)';
        }
      });
      
      // Alle Buttons zurücksetzen
      document.querySelectorAll('.group-toggle').forEach(btn => {
        if (btn !== this) {
          const btnArrow = btn.querySelector('svg:last-child');
          if (btnArrow) btnArrow.style.transform = 'rotate(0deg)';
        }
      });
      
      // Toggle-Logik
      if (isCurrentlyExpanded) {
        // SCHLIESSEN
        console.log(`🩺 HERZCHIRURG: Schließe Gruppe ${groupId}`);
        content.classList.remove('expanded');
        arrow.style.transform = 'rotate(0deg)';
        currentlyOpenGroup = null;
      } else {
        // ÖFFNEN
        console.log(`🩺 HERZCHIRURG: Öffne Gruppe ${groupId}`);
        content.classList.add('expanded');
        arrow.style.transform = 'rotate(180deg)';
        currentlyOpenGroup = groupId;
        
        // Scrolle zum Inhalt, falls er nicht vollständig sichtbar ist
        setTimeout(() => {
          const contentRect = content.getBoundingClientRect();
          const contentBottom = contentRect.bottom;
          const viewportHeight = window.innerHeight;
          
          console.log(`🩺 HERZCHIRURG: Content bottom: ${contentBottom}, Viewport height: ${viewportHeight}`);
          
          if (contentBottom > viewportHeight) {
            // Scrolle so, dass der Inhalt vollständig sichtbar ist
            const scrollOffset = contentBottom - viewportHeight + 50; // 50px extra Platz
            console.log(`🩺 HERZCHIRURG: Scrolle um ${scrollOffset}px nach unten`);
            window.scrollBy({ top: scrollOffset, behavior: 'smooth' });
          }
        }, 50);
      }
    });
  });
  
  console.log("🩺 HERZCHIRURG: Collapsible-Gruppen initialisiert");
}

// 🩺 HERZCHIRURG-FIX: Komplett überarbeitetes Tooltip-System mit garantierter Sichtbarkeit
function initializeTooltips() {
  // Handle tooltip-container structure
  const tooltipContainers = document.querySelectorAll('.tooltip-container');
  
  tooltipContainers.forEach(container => {
    const trigger = container.querySelector('.cursor-help');
    const tooltip = container.querySelector('.tooltip-content');
    
    if (trigger && tooltip) {
      // Entferne vorhandene Event-Listener, um Duplikate zu vermeiden
      const clonedTrigger = trigger.cloneNode(true);
      trigger.parentNode.replaceChild(clonedTrigger, trigger);
      
      // Füge neue Event-Listener hinzu
      clonedTrigger.addEventListener('mouseenter', () => handleTooltipShow(tooltip, clonedTrigger, container));
      clonedTrigger.addEventListener('mouseleave', () => handleTooltipHide(tooltip));
      clonedTrigger.addEventListener('focus', () => handleTooltipShow(tooltip, clonedTrigger, container));
      clonedTrigger.addEventListener('blur', () => handleTooltipHide(tooltip));
    }
  });
}

// Zeige Tooltip mit intelligenter Positionierung
function handleTooltipShow(tooltip, trigger, container) {
  // Entferne hidden-Klasse
  tooltip.classList.remove('hidden');
  tooltip.style.visibility = 'visible';
  tooltip.style.opacity = '1';
  
  // Positioniere den Tooltip intelligent
  const triggerRect = trigger.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  
  // Setze den Tooltip zuerst auf sichtbar, um seine Dimensionen zu messen
  tooltip.style.display = 'block';
  const tooltipHeight = tooltip.offsetHeight;
  const tooltipWidth = tooltip.offsetWidth;
  
  // Bestimme die beste Position (oben oder unten)
  const spaceAbove = triggerRect.top;
  const spaceBelow = viewportHeight - triggerRect.bottom;
  
  // Standardmäßig über dem Trigger platzieren, es sei denn, es ist nicht genug Platz
  let positionBelow = spaceAbove < (tooltipHeight + 10) && spaceBelow > spaceAbove;
  
  // Aktualisiere Container-Klasse basierend auf Position
  if (positionBelow) {
    container.classList.add('bottom');
  } else {
    container.classList.remove('bottom');
  }
  
  // Horizontale Positionierung - zentriert, aber innerhalb des Viewports
  let leftPos = triggerRect.left + (triggerRect.width / 2) - (tooltipWidth / 2);
  
  // Stelle sicher, dass der Tooltip nicht über den Rand hinausragt
  if (leftPos < 10) {
    leftPos = 10;
  } else if (leftPos + tooltipWidth > viewportWidth - 10) {
    leftPos = viewportWidth - tooltipWidth - 10;
  }
  
  // Wende die berechnete Position an
  tooltip.style.left = `${leftPos - triggerRect.left}px`;
  
  // Logge für Debugging
  console.log(`Tooltip positioniert: ${positionBelow ? 'unten' : 'oben'}, Breite: ${tooltipWidth}px`);
}

// Verstecke Tooltip
function handleTooltipHide(tooltip) {
  tooltip.style.visibility = 'hidden';
  tooltip.style.opacity = '0';
}

// Initialize UI components when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  // Initialize enhanced UI
  initializeCollapsibleGroups();
  initializeTooltips();
  initializeCodeSnippets();
  
  // Force immediate hiding to prevent any flash of content
  setTimeout(() => {
    Object.keys(collapsibles).forEach(id => {
      const element = document.getElementById(id);
      if (element && !element.classList.contains('expanded')) {
        element.style.display = 'none';
      }
    });
  }, 50);
}); 