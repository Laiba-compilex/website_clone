// Game Integration Script
// This script integrates the game modal with existing game elements

document.addEventListener('DOMContentLoaded', () => {
  // Wait for game modal to be available
  const waitForGameModal = () => {
    if (window.gameModal) {
      initializeGameIntegration();
    } else {
      setTimeout(waitForGameModal, 100);
    }
  };
  
  waitForGameModal();
});

function initializeGameIntegration() {
  console.log('Initializing game integration...');
  
  // Add click handlers to all game images
  const gameImages = document.querySelectorAll('img[src*="game"], img[alt*="game"], .game-item img, .game-image');
  
  gameImages.forEach((img, index) => {
    // Skip if already has click handler
    if (img.dataset.gameHandlerAdded) return;
    
    img.style.cursor = 'pointer';
    img.dataset.gameHandlerAdded = 'true';
    
    img.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      // Extract game information from the image
      const gameData = extractGameData(img);
      const isDaga = isDagaGame(img, gameData);
      
      console.log('Opening game modal for:', gameData.name, 'isDaga:', isDaga);
      window.gameModal.openModal(gameData, isDaga);
    });
  });
  
  // Add handlers to any elements with game-related classes or data attributes
  const gameElements = document.querySelectorAll('[data-game], .game-card, .game-item, [class*="game"]');
  
  gameElements.forEach((element) => {
    if (element.dataset.gameHandlerAdded) return;
    
    // Skip if it's an image (already handled above)
    if (element.tagName === 'IMG') return;
    
    element.style.cursor = 'pointer';
    element.dataset.gameHandlerAdded = 'true';
    
    element.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const gameData = extractGameDataFromElement(element);
      const isDaga = isDagaGame(element, gameData);
      
      console.log('Opening game modal for:', gameData.name, 'isDaga:', isDaga);
      window.gameModal.openModal(gameData, isDaga);
    });
  });
  
  // Special handler for Daga-specific elements
  const dagaElements = document.querySelectorAll('[alt*="daga"], [src*="daga"], [class*="daga"], [data-game*="daga"]');
  
  dagaElements.forEach((element) => {
    if (element.dataset.dagaHandlerAdded) return;
    
    element.style.cursor = 'pointer';
    element.dataset.dagaHandlerAdded = 'true';
    
    element.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const dagaGame = {
        name: 'ĐÁGÀ',
        icon_image: element.src || '/path/to/daga-icon.png',
        id: 'daga'
      };
      
      console.log('Opening Daga modal');
      window.gameModal.openModal(dagaGame, true);
    });
  });
  
  console.log(`Game integration complete. Added handlers to ${gameImages.length} images, ${gameElements.length} elements, and ${dagaElements.length} Daga elements.`);
}

function extractGameData(img) {
  // Try to extract game data from various sources
  const gameData = {
    name: img.alt || img.dataset.gameName || img.title || 'Unknown Game',
    icon_image: img.src,
    id: img.dataset.gameId || img.id || generateGameId(img.src)
  };
  
  // Clean up the name
  if (gameData.name === 'Unknown Game') {
    // Try to extract from src filename
    const srcParts = img.src.split('/');
    const filename = srcParts[srcParts.length - 1];
    const nameFromFile = filename.split('.')[0].replace(/[-_]/g, ' ');
    if (nameFromFile) {
      gameData.name = nameFromFile.charAt(0).toUpperCase() + nameFromFile.slice(1);
    }
  }
  
  return gameData;
}

function extractGameDataFromElement(element) {
  // Extract game data from non-image elements
  const gameData = {
    name: element.dataset.gameName || 
           element.textContent?.trim() || 
           element.getAttribute('title') || 
           'Unknown Game',
    icon_image: element.dataset.gameIcon || 
                element.querySelector('img')?.src || 
                '/path/to/default-game-icon.png',
    id: element.dataset.gameId || 
        element.id || 
        generateGameId(element.textContent)
  };
  
  return gameData;
}

function isDagaGame(element, gameData) {
  // Check if this is a Daga game
  const dagaKeywords = ['daga', 'đágà', 'cock', 'fighting'];
  
  // Check element attributes
  const elementText = (
    element.alt + ' ' + 
    element.src + ' ' + 
    element.className + ' ' + 
    (element.dataset.gameName || '') + ' ' +
    gameData.name
  ).toLowerCase();
  
  return dagaKeywords.some(keyword => elementText.includes(keyword));
}

function generateGameId(source) {
  // Generate a simple ID from the source string
  return source?.toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .substring(0, 10) || 'game_' + Date.now();
}

// Add some CSS for better visual feedback
const style = document.createElement('style');
style.textContent = `
  .game-hover-effect {
    transition: transform 0.2s ease, opacity 0.2s ease;
  }
  
  .game-hover-effect:hover {
    transform: scale(1.05);
    opacity: 0.9;
  }
  
  [data-game-handler-added="true"]:hover,
  [data-daga-handler-added="true"]:hover {
    transform: scale(1.02);
    transition: transform 0.2s ease;
  }
`;
document.head.appendChild(style);

// Export for debugging
window.gameIntegration = {
  reinitialize: initializeGameIntegration,
  extractGameData,
  isDagaGame
};