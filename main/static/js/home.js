// Enhanced Calculator
const calculateBtn = document.getElementById('calculate-btn');
const resultDisplay = document.querySelector('.result-display');
const resultAmount = document.querySelector('.result-amount');

if (calculateBtn) {
    calculateBtn.addEventListener('click', function() {
        // Loading state
        const originalText = calculateBtn.innerHTML;
        calculateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';
        calculateBtn.disabled = true;
        
        setTimeout(() => {
            const yearlyGallons = parseFloat(document.getElementById('yearly-gallons').value) || 0;
            
            if (yearlyGallons === 0) {
                alert('Please enter your yearly gallons');
                calculateBtn.innerHTML = originalText;
                calculateBtn.disabled = false;
                return;
            }
            
            // Formula: Average excise tax(0.679) * Yearly Gallons * 3 * 15%
            const exciseTaxRate = 0.679;
            const refundPercentage = 0.15;
            const refund = yearlyGallons * exciseTaxRate * 3 * refundPercentage;
            
            // Show result with animation
            resultAmount.textContent = '$0';
            resultDisplay.style.display = 'block';
            resultDisplay.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            // Animate counter
            let currentAmount = 0;
            const targetAmount = Math.round(refund);
            const increment = targetAmount / 50;
            
            const countAnimation = setInterval(() => {
                currentAmount += increment;
                if (currentAmount >= targetAmount) {
                    currentAmount = targetAmount;
                    clearInterval(countAnimation);
                }
                resultAmount.textContent = '$' + Math.round(currentAmount).toLocaleString();
            }, 30);
            
            calculateBtn.innerHTML = originalText;
            calculateBtn.disabled = false;
        }, 1500);
    });
}

// Mobile Navigation
const mobileToggle = document.querySelector('.mobile-toggle');
const navMenu = document.querySelector('.nav-menu');

if (mobileToggle) {
    mobileToggle.addEventListener('click', function() {
        navMenu.classList.toggle('active');
        mobileToggle.classList.toggle('active');
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });
    
    // Close menu when clicking links
    navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function() {
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
            document.body.style.overflow = '';
        });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!mobileToggle.contains(e.target) && !navMenu.contains(e.target)) {
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}

// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            const headerHeight = 100;
            const targetPosition = targetElement.offsetTop - headerHeight;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Stats animation
function animateStats() {
    const statNumbers = document.querySelectorAll('.stats-number, .stat-number');
    
    statNumbers.forEach(statEl => {
        if (statEl.dataset.animated) return;
        
        const targetValue = statEl.textContent;
        const isPercentage = targetValue.includes('%');
        const isRating = targetValue.includes('/');
        const isMoney = targetValue.includes('$');
        const hasPlus = targetValue.includes('+');
        
        let numValue;
        let prefix = '';
        let suffix = '';
        
        if (isPercentage) {
            numValue = parseFloat(targetValue.replace('%', ''));
            suffix = '%';
        } else if (isRating) {
            const parts = targetValue.split('/');
            numValue = parseFloat(parts[0]);
            suffix = '/' + parts[1];
        } else if (isMoney) {
            numValue = parseFloat(targetValue.replace('$', '').replace('K+', '').replace(',', ''));
            prefix = '$';
            suffix = targetValue.includes('K+') ? 'K+' : '';
        } else {
            numValue = parseFloat(targetValue.replace('+', '').replace(',', ''));
            suffix = hasPlus ? '+' : '';
        }
        
        let startValue = 0;
        const duration = 2000;
        const increment = (numValue / duration) * 20;
        
        statEl.textContent = prefix + startValue + suffix;
        
        const counter = setInterval(function() {
            startValue += increment;
            
            if (startValue >= numValue) {
                startValue = numValue;
                clearInterval(counter);
                statEl.dataset.animated = 'true';
            }
            
            if (isMoney && !targetValue.includes('M')) {
                statEl.textContent = prefix + Math.floor(startValue).toLocaleString() + suffix;
            } else if (isRating) {
                statEl.textContent = Math.floor(startValue * 10) / 10 + suffix;
            } else {
                statEl.textContent = prefix + Math.floor(startValue) + suffix;
            }
        }, 20);
    });
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.3,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            if (entry.target.classList.contains('floating-stats')) {
                animateStats();
            }
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Touch and gesture support for mobile
let touchStartX = 0;
let touchStartY = 0;
let touchEndX = 0;
let touchEndY = 0;

document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
}, false);

document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
    handleGesture();
}, false);

function handleGesture() {
    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;
    
    // Only handle horizontal swipes that are longer than vertical
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0 && navMenu.classList.contains('active')) {
            // Swipe right - close menu if open
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

// Lazy loading for images
const images = document.querySelectorAll('img[src]');
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.classList.add('loaded');
            observer.unobserve(img);
        }
    });
});

images.forEach(img => {
    imageObserver.observe(img);
});

// Optimize performance for mobile
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        // Recalculate layouts if needed
        if (window.innerWidth <= 768) {
            // Mobile specific adjustments
            const hero = document.querySelector('.hero');
            if (hero) {
                hero.style.minHeight = window.innerHeight + 'px';
            }
        }
    }, 250);
});

// Initialize animations and observers
document.addEventListener('DOMContentLoaded', function() {
    // Observe stats section
    const statsSection = document.querySelector('.floating-stats');
    if (statsSection) {
        observer.observe(statsSection);
    }
    
    // Fade in sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(section);
    });
    
    // Initial mobile height adjustment
    if (window.innerWidth <= 768) {
        const hero = document.querySelector('.hero');
        if (hero) {
            hero.style.minHeight = window.innerHeight + 'px';
        }
    }
    
    // Add loading class removal for smooth transitions
    document.body.classList.add('loaded');
});

// Prevent zoom on input focus for iOS
if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            document.querySelector('meta[name="viewport"]').setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0');
        });
        
        input.addEventListener('blur', function() {
            document.querySelector('meta[name="viewport"]').setAttribute('content', 'width=device-width, initial-scale=1.0');
        });
    });
}

// Enhanced form validation
const form = document.getElementById('tax-calculator');
if (form) {
    const inputs = form.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error')) {
                validateField(this);
            }
        });
    });
    
    function validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        
        field.classList.remove('error');
        
        if (isRequired && !value) {
            field.classList.add('error');
            return false;
        }
        
        if (field.type === 'number' && value && (isNaN(value) || parseFloat(value) < 0)) {
            field.classList.add('error');
            return false;
        }
        
        return true;
    }
}