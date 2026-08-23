// Nav background on scroll
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 40);
});

// Scroll-reveal for service cards and gallery items
const revealTargets = document.querySelectorAll('.service-card, .gallery-item, .team-card');
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
revealTargets.forEach((el) => observer.observe(el));

// Ripple effect on buttons
document.querySelectorAll('.btn').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    const rect = btn.getBoundingClientRect();
    btn.style.setProperty('--rx', `${e.clientX - rect.left}px`);
    btn.style.setProperty('--ry', `${e.clientY - rect.top}px`);
    btn.classList.remove('rippling');
    // force reflow so the animation restarts
    void btn.offsetWidth;
    btn.classList.add('rippling');
  });
});

// Contact form (demo — no backend wired up yet)
const form = document.getElementById('contactForm');
const note = document.getElementById('formNote');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    note.textContent = "Thanks — we'll be in touch shortly.";
    form.reset();
  });
}
