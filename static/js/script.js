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

// Contact form
const form = document.getElementById('contactForm');
const note = document.getElementById('formNote');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    note.textContent = 'Sending your enquiry…';
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      });
      const result = await response.json();
      note.textContent = result.message;
      if (response.ok) form.reset();
    } catch (error) {
      note.textContent = 'We could not send your enquiry. Please call us instead.';
    } finally {
      button.disabled = false;
    }
  });
}
