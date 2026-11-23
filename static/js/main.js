document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach((item) => {
    window.setTimeout(() => { item.style.transition = 'opacity .4s'; item.style.opacity = '0'; }, 5500);
  });
});
