document.addEventListener("submit", function (event) {
  const message = event.target.dataset.confirm;
  if (message && !window.confirm(message)) event.preventDefault();
});

document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".mobile-nav-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (!toggle || !sidebar) return;

  toggle.addEventListener("click", function () {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!expanded));
    sidebar.classList.toggle("is-open", !expanded);
  });
});
