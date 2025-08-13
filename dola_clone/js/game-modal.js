// Game Modal Implementation
// This file implements the games and points transfer modal functionality

class GameModal {
  constructor() {
    this.isOpen = false;
    this.currentGame = null;
    this.userBalance = 0;
    this.gameBalance = null;
    this.transferPoints = '';
    this.minValue = 30;
    this.maxValue = 1000000;
    this.loading = false;
    this.error = null;
    this.isDaga = false;
    
    this.init();
  }

  init() {
    this.createModalHTML();
    this.attachEventListeners();
    this.loadUserData();
  }

  createModalHTML() {
    const modalHTML = `
      <div id="game-modal" class="game-modal-overlay" style="display: none;">
        <div class="game-modal-wrapper">
          <div class="game-modal-header">
            <span class="game-modal-title">Game Transfer</span>
            <button class="game-modal-close" id="close-game-modal">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6L18 18" stroke="white" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          
          <div class="game-modal-content">
            <!-- User Balance Section -->
            <div class="balance-section">
              <div class="balance-input">
                <div class="balance-icon">
                  <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSI+CjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMlM2LjQ4IDIyIDEyIDIyUzIyIDE3LjUyIDIyIDEyUzE3LjUyIDIgMTIgMlpNMTMuNSAxNkgxMC41VjE0SDEzLjVWMTZaTTEzLjUgMTJIMTAuNVY4SDEzLjVWMTJaIiBmaWxsPSIjRkY5MjJCIi8+Cjwvc3ZnPgo=" alt="Balance">
                </div>
                <span class="balance-label">Your Balance</span>
                <span class="balance-amount" id="user-balance">0 K</span>
              </div>
            </div>

            <!-- Game Balance Section -->
            <div class="game-balance-section">
              <div class="game-balance-input">
                <div class="game-info">
                  <img id="game-icon" src="" alt="Game" class="game-icon">
                  <span id="game-name">Select Game</span>
                </div>
                <div class="game-balance-wrapper">
                  <span id="game-balance" class="game-balance">0</span>
                  <button id="refresh-balance" class="refresh-btn">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.65 2.35C12.2 0.9 10.21 0 8 0C3.58 0 0 3.58 0 8H2C2 4.69 4.69 2 8 2C9.66 2 11.14 2.69 12.22 3.78L10 6H16V0L13.65 2.35Z" fill="white"/>
                      <path d="M14 8C14 11.31 11.31 14 8 14C6.34 14 4.86 13.31 3.78 12.22L6 10H0V16L2.35 13.65C3.8 15.1 5.79 16 8 16C12.42 16 16 12.42 16 8H14Z" fill="white"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Transfer Points Section -->
            <div class="transfer-section">
              <label class="transfer-label">Transfer Points (K)</label>
              <div class="transfer-input-wrapper">
                <input 
                  type="number" 
                  id="transfer-points" 
                  class="transfer-input" 
                  placeholder="30"
                  min="30"
                >
                <div class="conversion-rate">30=1</div>
              </div>
            </div>

            <!-- Transfer All Button -->
            <div class="transfer-all-section">
              <button id="transfer-all-btn" class="transfer-all-btn">
                Transfer All Points
              </button>
            </div>

            <!-- Separator -->
            <div class="separator"></div>

            <!-- Error/Loading Section -->
            <div id="modal-status" class="modal-status"></div>

            <!-- Points Converter -->
            <div id="points-converter" class="points-converter">
              <div class="converter-label">Real</div>
              <div class="converter-content">
                <span id="points-from">0</span>
                <div id="daga-arrow" class="daga-arrow" style="display: none;">
                  <svg width="24" height="16" viewBox="0 0 24 16" fill="none">
                    <path d="M16 0L14.59 1.41L20.17 7H0V9H20.17L14.59 14.59L16 16L24 8L16 0Z" fill="#FF922B"/>
                  </svg>
                </div>
                <span id="points-to" style="display: none;">0</span>
              </div>
            </div>

            <!-- Min/Max Limits -->
            <div class="limits-section">
              <div class="limit-item">
                <span class="limit-label">Min:</span>
                <span id="min-limit" class="limit-value">30K</span>
              </div>
              <div class="limit-item">
                <span class="limit-label">Max:</span>
                <span id="max-limit" class="limit-value">1,000,000K</span>
              </div>
            </div>

            <!-- Play Now Button -->
            <button id="play-now-btn" class="play-now-btn" disabled>
              PLAY NOW
            </button>
          </div>
        </div>
      </div>
    `;

    // Add CSS styles
    const styles = `
      <style>
        .game-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
        }

        .game-modal-wrapper {
          background-color: #1b1d3f;
          border: 1px solid #0a151f;
          border-radius: 13px;
          padding: 24px 16px;
          max-width: 640px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
        }

        .game-modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 16px;
          border-bottom: 1px solid #7C8488;
          margin-bottom: 20px;
        }

        .game-modal-title {
          color: #ffffff;
          font-size: 18px;
          font-weight: 600;
        }

        .game-modal-close {
          background: none;
          border: none;
          cursor: pointer;
          padding: 4px;
        }

        .balance-section {
          margin-bottom: 16px;
        }

        .balance-input {
          display: flex;
          align-items: center;
          background-color: #0A151F;
          border: 1px solid #949494;
          border-radius: 4px;
          padding: 12px 16px;
          gap: 12px;
        }

        .balance-icon img {
          width: 26px;
          height: 26px;
        }

        .balance-label {
          color: white;
          font-size: 16px;
          flex: 1;
        }

        .balance-amount {
          color: #FF922B;
          font-size: 16px;
          font-weight: 600;
        }

        .game-balance-section {
          margin-bottom: 16px;
        }

        .game-balance-input {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background-color: #0A151F;
          border: 1px solid #949494;
          border-radius: 4px;
          padding: 12px 16px;
        }

        .game-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .game-icon {
          width: 30px;
          height: 30px;
          border-radius: 4px;
        }

        .game-balance-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .game-balance {
          color: #fce8ae;
          font-size: 16px;
        }

        .refresh-btn {
          background: none;
          border: none;
          cursor: pointer;
          padding: 4px;
        }

        .transfer-section {
          margin-bottom: 16px;
        }

        .transfer-label {
          display: block;
          color: white;
          font-size: 20px;
          margin-bottom: 16px;
        }

        .transfer-input-wrapper {
          position: relative;
        }

        .transfer-input {
          width: 100%;
          background-color: #0A151F;
          border: 1px solid #949494;
          border-radius: 4px;
          padding: 12px 16px;
          color: white;
          font-size: 16px;
          box-sizing: border-box;
        }

        .transfer-input:focus {
          outline: none;
          border-color: #FF922B;
        }

        .conversion-rate {
          position: absolute;
          right: 16px;
          bottom: -24px;
          color: #FF922B;
          font-size: 16px;
          font-weight: 500;
        }

        .transfer-all-section {
          margin: 32px 0 16px 0;
        }

        .transfer-all-btn {
          width: 100%;
          background: linear-gradient(180deg, #FF922B 42.79%, #C35F01 78.37%);
          border: none;
          border-radius: 8px;
          padding: 15px 24px;
          color: white;
          font-size: 18px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0px -4px 4px 0px #00000040 inset, 0px 4px 4px 0px #FFFFFFBF inset;
        }

        .transfer-all-btn:hover {
          background: linear-gradient(180deg, #C35F01 42.79%, #FF922B 78.37%);
        }

        .transfer-all-btn:disabled {
          background: #666;
          cursor: not-allowed;
        }

        .separator {
          height: 1px;
          background-color: #7C8488;
          margin: 16px 0;
        }

        .modal-status {
          text-align: center;
          margin: 16px 0;
          min-height: 24px;
        }

        .modal-status.error {
          color: #d32f2f;
          font-weight: bold;
        }

        .modal-status.loading {
          color: white;
        }

        .points-converter {
          margin: 16px 0;
        }

        .converter-label {
          color: white;
          font-size: 16px;
          font-weight: 500;
          margin-bottom: 8px;
        }

        .converter-content {
          display: flex;
          align-items: center;
          gap: 12px;
          color: white;
          font-size: 16px;
        }

        .daga-arrow {
          display: flex;
          align-items: center;
        }

        .limits-section {
          display: flex;
          justify-content: space-between;
          margin: 16px 0;
        }

        .limit-item {
          display: flex;
          gap: 4px;
        }

        .limit-label {
          color: #949494;
          font-size: 14px;
        }

        .limit-value {
          color: white;
          font-size: 14px;
        }

        .limit-value.invalid {
          color: #d32f2f;
        }

        .play-now-btn {
          width: 100%;
          background: linear-gradient(180deg, #FFCE40 34.62%, #8E6A00 76.44%);
          border: 1px solid #8E6A00;
          border-radius: 8px;
          padding: 15px 0;
          color: white;
          font-size: 18px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0px -4px 4px 0px #00000040 inset, 0px 4px 4px 0px #FFFFFFBF inset;
        }

        .play-now-btn:hover:not(:disabled) {
          background: linear-gradient(180deg, #8E6A00 34.62%, #FFCE40 76.44%);
        }

        .play-now-btn:disabled {
          background: #666;
          cursor: not-allowed;
          opacity: 0.6;
        }

        .loader {
          display: inline-block;
          width: 20px;
          height: 20px;
          border: 2px solid #f3f3f3;
          border-top: 2px solid #FF922B;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        #game-name {
          color: white;
          font-size: 16px;
        }
      </style>
    `;

    // Add to document
    document.head.insertAdjacentHTML('beforeend', styles);
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  attachEventListeners() {
    // Close modal
    document.getElementById('close-game-modal').addEventListener('click', () => {
      this.closeModal();
    });

    // Close on overlay click
    document.getElementById('game-modal').addEventListener('click', (e) => {
      if (e.target.id === 'game-modal') {
        this.closeModal();
      }
    });

    // Transfer points input
    document.getElementById('transfer-points').addEventListener('input', (e) => {
      this.transferPoints = e.target.value;
      this.updatePointsConverter();
      this.validateInput();
    });

    // Transfer all button
    document.getElementById('transfer-all-btn').addEventListener('click', () => {
      this.transferAllPoints();
    });

    // Refresh balance
    document.getElementById('refresh-balance').addEventListener('click', () => {
      this.refreshGameBalance();
    });

    // Play now button
    document.getElementById('play-now-btn').addEventListener('click', () => {
      this.playNow();
    });
  }

  openModal(game, isDaga = false) {
    this.currentGame = game;
    this.isDaga = isDaga;
    this.isOpen = true;
    
    // Update game info
    document.getElementById('game-icon').src = game.icon_image || '';
    document.getElementById('game-name').textContent = isDaga ? 'Daga' : (game.name || 'Game');
    
    // Show/hide daga-specific elements
    const dagaArrow = document.getElementById('daga-arrow');
    const pointsTo = document.getElementById('points-to');
    
    if (isDaga) {
      dagaArrow.style.display = 'flex';
      pointsTo.style.display = 'block';
    } else {
      dagaArrow.style.display = 'none';
      pointsTo.style.display = 'none';
    }
    
    // Show modal
    document.getElementById('game-modal').style.display = 'flex';
    
    // Load game balance
    this.loadGameBalance();
    
    // Reset form
    this.resetForm();
  }

  closeModal() {
    this.isOpen = false;
    document.getElementById('game-modal').style.display = 'none';
    this.resetForm();
  }

  resetForm() {
    this.transferPoints = '';
    this.error = null;
    this.loading = false;
    
    document.getElementById('transfer-points').value = '';
    document.getElementById('modal-status').innerHTML = '';
    document.getElementById('modal-status').className = 'modal-status';
    document.getElementById('play-now-btn').disabled = true;
    
    this.updatePointsConverter();
  }

  loadUserData() {
    // Simulate loading user balance - replace with actual API call
    this.userBalance = 50000; // Example balance
    this.updateUserBalance();
  }

  updateUserBalance() {
    const balanceElement = document.getElementById('user-balance');
    balanceElement.textContent = `${this.formatNumber(this.userBalance)} K`;
  }

  async loadGameBalance() {
    this.setLoading(true);
    
    try {
      // Simulate API call - replace with actual implementation
      await this.delay(1000);
      
      if (this.isDaga) {
        // Simulate Daga balance API
        this.gameBalance = Math.floor(Math.random() * 10000);
      } else {
        // Simulate regular game balance API
        this.gameBalance = Math.floor(Math.random() * 5000);
      }
      
      this.updateGameBalance();
    } catch (error) {
      this.gameBalance = 'Error';
      this.updateGameBalance();
    } finally {
      this.setLoading(false);
    }
  }

  async refreshGameBalance() {
    await this.loadGameBalance();
  }

  updateGameBalance() {
    const balanceElement = document.getElementById('game-balance');
    
    if (typeof this.gameBalance === 'number') {
      balanceElement.textContent = this.formatNumber(this.gameBalance);
      balanceElement.className = 'game-balance';
    } else {
      balanceElement.textContent = this.gameBalance;
      balanceElement.className = 'game-balance error';
    }
  }

  updatePointsConverter() {
    const pointsFrom = document.getElementById('points-from');
    const pointsTo = document.getElementById('points-to');
    
    const points = parseFloat(this.transferPoints) || 0;
    
    if (this.isDaga) {
      // Daga conversion: 30 points = 1 daga point
      const fromPoints = Math.trunc(points / 30) * 30;
      const toPoints = Math.trunc(points / 30);
      
      pointsFrom.textContent = this.formatNumber(fromPoints);
      pointsTo.textContent = this.formatNumber(toPoints);
    } else {
      pointsFrom.textContent = this.formatNumber(points);
    }
  }

  validateInput() {
    const points = parseFloat(this.transferPoints) || 0;
    const playNowBtn = document.getElementById('play-now-btn');
    const minLimit = document.getElementById('min-limit');
    const maxLimit = document.getElementById('max-limit');
    
    // Reset limit styles
    minLimit.className = 'limit-value';
    maxLimit.className = 'limit-value';
    
    let isValid = true;
    
    if (points < this.minValue) {
      minLimit.className = 'limit-value invalid';
      isValid = false;
    }
    
    if (points > this.maxValue) {
      maxLimit.className = 'limit-value invalid';
      isValid = false;
    }
    
    if (points > this.userBalance) {
      isValid = false;
    }
    
    playNowBtn.disabled = !isValid || points <= 0 || this.loading;
  }

  transferAllPoints() {
    if (this.userBalance > 0) {
      this.transferPoints = this.userBalance.toString();
      document.getElementById('transfer-points').value = this.transferPoints;
      this.updatePointsConverter();
      this.validateInput();
    }
  }

  async playNow() {
    if (this.loading) return;
    
    this.setLoading(true);
    this.clearError();
    
    try {
      const points = parseFloat(this.transferPoints);
      
      // Simulate API call
      await this.delay(2000);
      
      if (this.isDaga) {
        // Simulate Daga deposit API
        console.log('Daga deposit:', points);
      } else {
        // Simulate regular game deposit API
        console.log('Game deposit:', points);
      }
      
      // Update balances
      this.userBalance -= points;
      this.gameBalance += points;
      
      this.updateUserBalance();
      this.updateGameBalance();
      
      // Show success message
      this.showSuccess('Transfer successful!');
      
      // Reset form
      setTimeout(() => {
        this.resetForm();
      }, 2000);
      
    } catch (error) {
      this.showError('Transfer failed. Please try again.');
    } finally {
      this.setLoading(false);
    }
  }

  setLoading(loading) {
    this.loading = loading;
    const statusElement = document.getElementById('modal-status');
    const playNowBtn = document.getElementById('play-now-btn');
    
    if (loading) {
      statusElement.innerHTML = '<div class="loader"></div>';
      statusElement.className = 'modal-status loading';
      playNowBtn.disabled = true;
    } else {
      if (!this.error) {
        statusElement.innerHTML = '';
        statusElement.className = 'modal-status';
      }
      this.validateInput();
    }
  }

  showError(message) {
    this.error = message;
    const statusElement = document.getElementById('modal-status');
    statusElement.textContent = message;
    statusElement.className = 'modal-status error';
  }

  showSuccess(message) {
    const statusElement = document.getElementById('modal-status');
    statusElement.textContent = message;
    statusElement.className = 'modal-status';
    statusElement.style.color = '#4caf50';
  }

  clearError() {
    this.error = null;
    const statusElement = document.getElementById('modal-status');
    statusElement.innerHTML = '';
    statusElement.className = 'modal-status';
    statusElement.style.color = '';
  }

  formatNumber(num) {
    return num?.toLocaleString() || '0';
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize the game modal when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.gameModal = new GameModal();
  
  // Example: Add click handlers to game images
  // This should be integrated with your existing game selection logic
  document.addEventListener('click', (e) => {
    // Check if clicked element is a game image or has game data
    if (e.target.classList.contains('game-image') || e.target.dataset.game) {
      const gameData = {
        name: e.target.dataset.gameName || 'Game',
        icon_image: e.target.src || e.target.dataset.gameIcon,
        id: e.target.dataset.gameId
      };
      
      const isDaga = e.target.dataset.gameName === 'ĐÁGÀ' || e.target.dataset.isDaga === 'true';
      
      window.gameModal.openModal(gameData, isDaga);
    }
  });
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GameModal;
}