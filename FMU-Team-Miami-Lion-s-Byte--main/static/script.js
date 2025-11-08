const slides = document.querySelectorAll('.slide');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
let currentSlide = 0;

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove('active');
        if (i === index) slide.classList.add('active');
    });
}

nextBtn.addEventListener('click', () => {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
});

prevBtn.addEventListener('click', () => {
    currentSlide = (currentSlide - 1 + slides.length) % slides.length;
    showSlide(currentSlide);
});
// Optional: Add smooth scrolling for nav links (already handled by CSS in most browsers)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});


// Location selector handler: persist choice and show a small toast confirmation
document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('locationSelect');
    if (!select) return;

    // Restore previous choice if any
    try {
        const saved = localStorage.getItem('selectedLocation');
        if (saved) select.value = saved;
    } catch (err) {
        // ignore storage errors
        console.warn('localStorage unavailable', err);
    }

    select.addEventListener('change', (e) => {
        const val = e.target.value;
        const opt = e.target.options[e.target.selectedIndex];
        const label = (opt && opt.text) || val;
        try {
            localStorage.setItem('selectedLocation', val);
        } catch (err) {
            console.warn('Could not save location', err);
        }

        showLocationToast(`Location set: ${label}`);

        // Optional: dispatch a custom event so other scripts can react
        const evt = new CustomEvent('locationChanged', { detail: { value: val, label } });
        document.dispatchEvent(evt);
    });
});

function showLocationToast(message, timeout = 2500) {
    const toast = document.createElement('div');
    toast.className = 'location-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = message;
    document.body.appendChild(toast);
    // trigger reflow for CSS animation
    void toast.offsetWidth;
    toast.classList.add('visible');
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, timeout);
}