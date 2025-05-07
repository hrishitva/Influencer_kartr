document.addEventListener('DOMContentLoaded', function() {
    console.log('Password validation script loaded');
    
    const passwordField = document.getElementById('password-field');
    
    if (!passwordField) {
        console.error('Password field not found');
        return;
    }
    
    console.log('Password field found:', passwordField);
    
    const lengthCheck = document.getElementById('length-check');
    const complexityCheck = document.getElementById('complexity-check');
    const lowercaseCheck = document.getElementById('lowercase-check');
    const uppercaseCheck = document.getElementById('uppercase-check');
    const numberCheck = document.getElementById('number-check');
    const specialCheck = document.getElementById('special-check');
    
    if (!lengthCheck || !complexityCheck || !lowercaseCheck || !uppercaseCheck || !numberCheck || !specialCheck) {
        console.error('One or more requirement elements not found');
        return;
    }
    
    // Function to update requirement status
    function updateRequirement(element, isValid) {
        const icon = element.querySelector('i');
        
        if (isValid) {
            element.classList.add('text-success');
            element.classList.remove('text-dark');
            icon.classList.remove('fa-times-circle', 'text-danger');
            icon.classList.add('fa-check-circle', 'text-success');
        } else {
            element.classList.remove('text-success');
            element.classList.add('text-dark');
            icon.classList.remove('fa-check-circle', 'text-success');
            icon.classList.add('fa-times-circle', 'text-danger');
        }
    }
    
    // Initial check
    checkPassword();
    
    // Add event listener
    passwordField.addEventListener('input', checkPassword);
    
    function checkPassword() {
        const password = passwordField.value;
        console.log('Password changed:', password);
        
        // Check length
        updateRequirement(lengthCheck, password.length >= 8);
        
        // Check character types
        const hasLowercase = /[a-z]/.test(password);
        const hasUppercase = /[A-Z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
        
        // Update character type indicators
        updateRequirement(lowercaseCheck, hasLowercase);
        updateRequirement(uppercaseCheck, hasUppercase);
        updateRequirement(numberCheck, hasNumber);
        updateRequirement(specialCheck, hasSpecial);
        
        // Check complexity (at least 3 of 4 character types)
        const complexityCount = [hasLowercase, hasUppercase, hasNumber, hasSpecial].filter(Boolean).length;
        updateRequirement(complexityCheck, complexityCount >= 3);
    }
});