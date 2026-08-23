const tabs = document.querySelectorAll('.tab-button');
const panels = document.querySelectorAll('.tab-panel');

function openTab(name) {
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === name));
  panels.forEach((panel) => panel.classList.toggle('active', panel.id === `${name}-panel`));
  const url = new URL(window.location.href);
  url.searchParams.set('tab', name);
  window.history.replaceState({}, '', url);
}

tabs.forEach((tab) => tab.addEventListener('click', () => openTab(tab.dataset.tab)));
const initialTab = new URLSearchParams(window.location.search).get('tab');
if (initialTab && document.getElementById(`${initialTab}-panel`)) openTab(initialTab);

const dialog = document.getElementById('editor-dialog');
const editorForm = document.getElementById('editor-form');
const sectionLabels = { services: 'service', works: 'work item', reviews: 'review', team_members: 'team member', treatments: 'water treatment option' };

function showEditor(section, item = {}) {
  if (!dialog || !editorForm) return;
  editorForm.reset();
  editorForm.action = `/admin/${section}/save`;
  document.getElementById('field-id').value = item.id || '';
  document.getElementById('field-sort-order').value = item.sort_order ?? 0;
  document.getElementById('field-published').checked = item.id ? Boolean(item.is_published) : true;
  document.getElementById('dialog-eyebrow').textContent = item.id ? 'Edit item' : 'Add item';
  document.getElementById('dialog-title').textContent = `${item.id ? 'Edit' : 'New'} ${sectionLabels[section]}`;
  document.querySelectorAll('.dynamic-fields').forEach((group) => {
    const active = group.id === `${section.slice(0, -1)}-fields` || (section === 'works' && group.id === 'work-fields') || (section === 'team_members' && group.id === 'team_member-fields');
    group.classList.toggle('active', active);
    group.querySelectorAll('input, textarea, select').forEach((field) => { field.disabled = !active; });
  });
  const mappings = {
    services: { 'service-title': 'title', 'service-description': 'description', 'service-icon': 'icon' },
    works: { 'work-title': 'title', 'work-location': 'location', 'work-image-url': 'image_url' },
    reviews: { 'review-quote': 'quote', 'review-customer-name': 'customer_name', 'review-location': 'location' },
    team_members: { 'team-member-name': 'name', 'team-member-role': 'role', 'team-member-bio': 'bio', 'team-member-image-url': 'image_url' },
    treatments: { 'treatment-audience': 'audience', 'treatment-title': 'title', 'treatment-description': 'description', 'treatment-icon': 'icon', 'treatment-features': 'features' },
  };
  Object.entries(mappings[section]).forEach(([id, key]) => { document.getElementById(id).value = item[key] || ''; });
  dialog.showModal();
}

document.querySelectorAll('.add-button').forEach((button) => button.addEventListener('click', () => showEditor(button.dataset.section)));
document.querySelectorAll('.edit-button').forEach((button) => button.addEventListener('click', () => showEditor(button.dataset.section, JSON.parse(button.dataset.item))));
document.querySelectorAll('.close-button').forEach((button) => button.addEventListener('click', () => dialog?.close()));
dialog?.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
