// Interactive features and animations

document.addEventListener('DOMContentLoaded', function() {
    // Animated background dots
    createAnimatedBackground();
    
    // Dropdown functionality
    const researchDropdown = document.getElementById('researchDropdown');
    if (researchDropdown) {
        researchDropdown.addEventListener('click', function() {
            // Toggle dropdown (you can add actual dropdown menu here)
            this.classList.toggle('active');
        });
    }
    
    // Modal functionality
    const modalOverlay = document.getElementById('modalOverlay');
    const modalClose = document.getElementById('modalClose');
    
    // Open modal (can be triggered by various buttons)
    function openModal() {
        if (modalOverlay) {
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Close modal
    function closeModal() {
        if (modalOverlay) {
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });
    }
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('active')) {
            closeModal();
        }
    });
    
    // Search input functionality
    const mainSearchInput = document.getElementById('mainSearchInput');
    const beginBtn = document.getElementById('beginBtn');
    
    if (mainSearchInput) {
        // Allow Enter key to trigger research
        mainSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleResearch();
            }
        });
        
        // Handle @ mentions
        mainSearchInput.addEventListener('input', function(e) {
            const value = e.target.value;
            if (value.includes('@')) {
                // You can add mention functionality here
                console.log('Mention detected');
            }
        });
    }
    
    // Begin Research button
    if (beginBtn) {
        beginBtn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
            
            handleResearch();
        });
    }
    
    // Handle research action
    function handleResearch() {
        const question = mainSearchInput ? mainSearchInput.value.trim() : '';
        
        if (!question) {
            // Add shake animation if input is empty
            if (mainSearchInput) {
                mainSearchInput.style.animation = 'shake 0.5s';
                setTimeout(() => {
                    mainSearchInput.style.animation = '';
                }, 500);
            }
            return;
        }
        
        // Visual feedback
        if (beginBtn) {
            beginBtn.style.opacity = '0.7';
            beginBtn.style.pointerEvents = 'none';
        }
        if (mainSearchInput) {
            mainSearchInput.disabled = true;
        }
        
        // Simulate processing (since no backend)
        setTimeout(() => {
            // Show a simple message (you can enhance this)
            alert('Research initiated! (Frontend demo - no backend connection)\n\nQuestion: ' + question);
            
            // Reset UI
            if (beginBtn) {
                beginBtn.style.opacity = '1';
                beginBtn.style.pointerEvents = 'auto';
            }
            if (mainSearchInput) {
                mainSearchInput.disabled = false;
                mainSearchInput.value = '';
            }
        }, 1000);
    }
    
    // Navigation tab switching
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            navTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Sidebar navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Search control buttons
    const searchControlBtns = document.querySelectorAll('.search-control-btn');
    searchControlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Toggle active state (except primary button)
            if (!this.classList.contains('primary')) {
                const group = this.closest('.search-controls-left') || this.closest('.search-controls-right');
                if (group) {
                    group.querySelectorAll('.search-control-btn').forEach(b => {
                        if (!b.classList.contains('primary')) {
                            b.classList.remove('active');
                        }
                    });
                    this.classList.add('active');
                }
            }
        });
    });
    
    // Radio button interactions
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });
    
    // Add scroll animations for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe info cards
    document.querySelectorAll('.info-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Parallax effect on mouse move
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', function(e) {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 10;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 10;
        
        const animatedBg = document.getElementById('animatedBg');
        if (animatedBg) {
            animatedBg.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
        }
    });
});

// Create animated background with dots
function createAnimatedBackground() {
    const animatedBg = document.getElementById('animatedBg');
    if (!animatedBg) return;
    
    // Create multiple animated dots
    for (let i = 0; i < 20; i++) {
        const dot = document.createElement('div');
        dot.className = 'animated-dot';
        const size = Math.random() * 4 + 2;
        const duration = 3 + Math.random() * 4;
        const delay = Math.random() * 2;
        const left = Math.random() * 100;
        const top = Math.random() * 100;
        
        dot.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: rgba(0, 188, 212, 0.4);
            border-radius: 50%;
            left: ${left}%;
            top: ${top}%;
            animation: floatDot ${duration}s ease-in-out infinite;
            animation-delay: ${delay}s;
            pointer-events: none;
        `;
        
        animatedBg.appendChild(dot);
    }
}

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes floatDot {
        0%, 100% {
            transform: translate(0, 0);
            opacity: 0.3;
        }
        50% {
            transform: translate(20px, -20px);
            opacity: 0.6;
        }
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .animated-dot {
        pointer-events: none;
    }
`;
document.head.appendChild(style);
