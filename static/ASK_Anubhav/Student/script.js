function toggleFilters() {
    var filters = document.querySelector('.filters');
    filters.classList.toggle('d-none');
  }
  
document.querySelector('#filter-button').addEventListener('click', function() {
      this.classList.toggle('btn-outline-primary');
      this.classList.toggle('btn-primary');
});

function goToCreatePage() {
    window.location.href = '/create_post';
}