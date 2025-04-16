document.addEventListener('DOMContentLoaded', () => {
  const moduleCards = document.querySelectorAll('.module-card');

  moduleCards.forEach(card => {
      // Add click listener to navigate to the module page
      card.addEventListener('click', () => {
          const target = card.getAttribute('data-target');
          if (target) {
              window.location.href = target;
          }
      });

      // Prevent click on the "Go to Module" button from triggering card navigation
      const moduleButton = card.querySelector('.module-button');
      if (moduleButton) {
          moduleButton.addEventListener('click', (event) => {
              event.stopPropagation(); // Prevent the card's click event
          });
      }
  });

  // Optional: Add some subtle animation on page load
  const mainContent = document.querySelector('.main-content .container');
  if (mainContent) {
      mainContent.classList.add('fade-in');
  }
});

// Optional: Basic fade-in animation class (can be moved to CSS if preferred)
const style = document.createElement('style');
style.textContent = `
  .fade-in {
      opacity: 0;
      animation: fadeIn 0.5s ease-out forwards;
  }

  @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
  }
`;
document.head.appendChild(style);