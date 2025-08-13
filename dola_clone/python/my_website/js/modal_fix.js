document.addEventListener('DOMContentLoaded', function() {
  const modal = document.querySelector('.ad-center');
  const closeButton = document.querySelector('.ad-center .close');

  if (modal && closeButton) {
    closeButton.addEventListener('click', function() {
      modal.style.display = 'none';
    });
  }
});
