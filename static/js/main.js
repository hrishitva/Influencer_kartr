document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltips.length > 0) {
    Array.from(tooltips).forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }

  // Handle flash messages auto-dismiss
  const flashMessages = document.querySelectorAll('.alert.auto-dismiss');
  if (flashMessages.length > 0) {
    Array.from(flashMessages).forEach(message => {
      setTimeout(() => {
        const alert = new bootstrap.Alert(message);
        alert.close();
      }, 5000);
    });
  }

  // Handle YouTube URL validation
  const youtubeInputs = document.querySelectorAll('.youtube-url-input');
  if (youtubeInputs.length > 0) {
    Array.from(youtubeInputs).forEach(input => {
      input.addEventListener('blur', validateYouTubeUrl);
      input.form.addEventListener('submit', function(e) {
        if (!validateYouTubeUrl({ target: input })) {
          e.preventDefault();
        }
      });
    });
  }

  // Animate stats numbers
  const statsNumbers = document.querySelectorAll('.stats-number[data-value]');
  if (statsNumbers.length > 0) {
    Array.from(statsNumbers).forEach(statElement => {
      animateValue(statElement, 0, parseInt(statElement.dataset.value), 1500);
    });
  }
});

/**
 * Validate if the input contains a valid YouTube URL
 * @param {Event} event - The blur event
 * @returns {boolean} - Whether the URL is valid
 */
function validateYouTubeUrl(event) {
  const input = event.target;
  const value = input.value.trim();
  const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
  
  const isValid = value === '' || youtubeRegex.test(value);
  
  if (!isValid) {
    input.classList.add('is-invalid');
    
    // Create or update the feedback message
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
      feedback = document.createElement('div');
      feedback.classList.add('invalid-feedback');
      input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    feedback.textContent = 'Please enter a valid YouTube URL';
  } else {
    input.classList.remove('is-invalid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
      feedback.textContent = '';
    }
  }
  
  return isValid;
}

/**
 * Animate a number from start to end
 * @param {HTMLElement} obj - The element to animate
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} duration - Animation duration in ms
 */
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    
    // Format number with commas
    obj.textContent = value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element that was clicked
 */
function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    // Store original text
    const originalText = button.textContent;
    
    // Change button text
    button.textContent = 'Copied!';
    
    // Reset after 2 seconds
    setTimeout(() => {
      button.textContent = originalText;
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy text: ', err);
  });
}

/**
 * Toggle between different views
 * @param {string} viewId - ID of the view to show
 * @param {HTMLElement} button - Button that was clicked
 */
function toggleView(viewId, button) {
  // Hide all views
  const views = document.querySelectorAll('.toggle-view');
  views.forEach(view => {
    view.classList.add('d-none');
  });
  
  // Show selected view
  const selectedView = document.getElementById(viewId);
  if (selectedView) {
    selectedView.classList.remove('d-none');
  }
  
  // Update active button
  const buttons = document.querySelectorAll('.view-toggle-btn');
  buttons.forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Set clicked button as active
  button.classList.add('active');
}
