// Virtual Influencer Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initAnimations();
    
    // Initialize event listeners
    initEventListeners();
    
    // Initialize form handlers
    initFormHandlers();
});

// Initialize animations for elements
function initAnimations() {
    // Add animation classes to elements as they come into view
    const animatedElements = document.querySelectorAll('.benefits-section, .influencers-section, .how-it-works-section');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
    
    // Add staggered animations to cards
    const cards = document.querySelectorAll('.influencer-card, .step-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate__animated', 'animate__fadeInUp');
    });
}

// Initialize event listeners
function initEventListeners() {
    // Rent Now button click handler
    const rentButtons = document.querySelectorAll('.rent-btn');
    rentButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const influencerId = this.getAttribute('data-influencer-id');
            openBookingModal(influencerId);
        });
    });
    
    // Details button click handler
    const detailsButtons = document.querySelectorAll('.details-btn');
    detailsButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const influencerId = this.getAttribute('data-influencer-id');
            showInfluencerDetails(influencerId);
        });
    });
    
    // Create Virtual Influencer button handlers
    const createVirtualInfluencerBtn = document.getElementById('createVirtualInfluencerBtn');
    if (createVirtualInfluencerBtn) {
        createVirtualInfluencerBtn.addEventListener('click', function() {
            $('#createInfluencerModal').modal('show');
        });
    }
    
    const createVirtualInfluencerLLMBtn = document.getElementById('createVirtualInfluencerLLMBtn');
    if (createVirtualInfluencerLLMBtn) {
        createVirtualInfluencerLLMBtn.addEventListener('click', function() {
            $('#llmInfluencerModal').modal('show');
        });
    }
    
    // Generate Influencer button handler
    const generateInfluencerBtn = document.getElementById('generateInfluencerBtn');
    if (generateInfluencerBtn) {
        generateInfluencerBtn.addEventListener('click', function() {
            generateVirtualInfluencer();
        });
    }
    
    // Quality level slider handler
    const qualityLevelSlider = document.getElementById('qualityLevel');
    if (qualityLevelSlider) {
        qualityLevelSlider.addEventListener('input', function() {
            updateQualityLevel(this.value);
        });
    }
}

// Initialize form handlers
function initFormHandlers() {
    // Image Generation Form
    const imageGenForm = document.getElementById('imageGenForm');
    if (imageGenForm) {
        imageGenForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateImage();
        });
    }
    
    // LLM Influencer Form
    const llmInfluencerForm = document.getElementById('llmInfluencerForm');
    if (llmInfluencerForm) {
        llmInfluencerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            generateLLMInfluencer();
        });
    }
    
    // Booking Form
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            processBooking();
        });
    }
}

// Open booking modal with influencer details
function openBookingModal(influencerId) {
    // Find the influencer data
    const influencerCard = document.querySelector(`.influencer-card [data-influencer-id="${influencerId}"]`).closest('.influencer-card');
    const influencerName = influencerCard.querySelector('.card-title').textContent;
    const influencerRate = influencerCard.querySelector('.price').textContent;
    
    // Set the modal title
    document.getElementById('bookingModalLabel').textContent = `Rent ${influencerName}`;
    
    // Set the influencer ID in the form
    document.getElementById('influencerId').value = influencerId;
    
    // Show the modal
    $('#bookingModal').modal('show');
}

// Show influencer details
function showInfluencerDetails(influencerId) {
    // This would typically open a modal or navigate to a details page
    console.log(`Showing details for influencer: ${influencerId}`);
    
    // For now, just scroll to the influencer card and highlight it
    const influencerCard = document.querySelector(`.influencer-card [data-influencer-id="${influencerId}"]`).closest('.influencer-card');
    
    influencerCard.classList.add('animate__animated', 'animate__pulse');
    
    // Scroll to the card
    influencerCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Remove the animation class after it completes
    setTimeout(() => {
        influencerCard.classList.remove('animate__animated', 'animate__pulse');
    }, 1000);
}

// Generate image from form data
function generateImage() {
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('resultImage').style.display = 'none';
    
    // In a real implementation, this would send the form data to the server
    // For demo purposes, we'll simulate a delay and then show a placeholder image
    setTimeout(() => {
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        
        // Show result image (placeholder for demo)
        const resultImage = document.getElementById('resultImage');
        resultImage.src = 'https://via.placeholder.com/800x600/6c63ff/ffffff?text=Generated+Image';
        resultImage.style.display = 'block';
        resultImage.classList.add('animate__animated', 'animate__fadeIn');
        
        // Show success message
        showToast('Image generated successfully!', 'success');
    }, 3000);
}

// Generate LLM influencer from form data
function generateLLMInfluencer() {
    // Get the prompt
    const prompt = document.getElementById('llmPrompt').value;
    
    // Show loading indicator
    const resultContainer = document.getElementById('llmImageResult');
    resultContainer.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Generating your virtual influencer...</p>
    `;
    
    // In a real implementation, this would send the prompt to the server
    // For demo purposes, we'll simulate a delay and then show a placeholder image
    setTimeout(() => {
        // Show result image (placeholder for demo)
        resultContainer.innerHTML = `
            <img src="https://via.placeholder.com/400x400/6c63ff/ffffff?text=AI+Generated+Influencer" 
                 class="img-fluid rounded animate__animated animate__fadeIn" 
                 style="max-height: 300px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
            <div class="mt-3">
                <h6>Your Virtual Influencer</h6>
                <p class="text-muted">Generated based on your description</p>
                <button class="btn btn-primary mt-2">Save Influencer</button>
            </div>
        `;
        
        // Show success message
        showToast('Virtual influencer generated successfully!', 'success');
    }, 4000);
}

// Generate virtual influencer using Fooocus
function generateVirtualInfluencer() {
    // Get form data
    const name = document.getElementById('influencerName').value;
    const prompt = document.getElementById('influencerPrompt').value;
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const style = document.getElementById('stylePreset').value;
    const quality = document.getElementById('qualityLevel').value;
    
    // Show loading in preview
    const previewContainer = document.querySelector('.preview-container');
    previewContainer.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Generating preview...</p>
    `;
    
    // In a real implementation, this would send the data to the server
    // For demo purposes, we'll simulate a delay and then show a placeholder image
    setTimeout(() => {
        // Show preview image (placeholder for demo)
        previewContainer.innerHTML = `
            <img src="https://via.placeholder.com/400x400/6c63ff/ffffff?text=Fooocus+Generated+Influencer" 
                 class="img-fluid rounded animate__animated animate__fadeIn" 
                 style="max-height: 300px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
            <div class="mt-3">
                <h6>${name}</h6>
                <p class="text-muted">Style: ${style}, Quality: ${quality}/5</p>
                <button class="btn btn-primary mt-2">Save Influencer</button>
            </div>
        `;
        
        // Show success message
        showToast('Preview generated successfully!', 'success');
    }, 3000);
}

// Update quality level display
function updateQualityLevel(value) {
    // This would update any UI elements that show the quality level
    console.log(`Quality level set to: ${value}`);
}

// Process booking form
function processBooking() {
    // Get form data
    const influencerId = document.getElementById('influencerId').value;
    const startDate = document.getElementById('startDate').value;
    const duration = document.getElementById('duration').value;
    const campaignName = document.getElementById('campaignName').value;
    
    // In a real implementation, this would send the booking data to the server
    // For demo purposes, we'll just show a success message and close the modal
    
    // Close the modal
    $('#bookingModal').modal('hide');
    
    // Show success message
    showToast('Booking submitted successfully!', 'success');
}

// Show toast notification
function showToast(message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}