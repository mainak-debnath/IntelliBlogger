document.addEventListener('DOMContentLoaded', function () {
    const clearButton = document.getElementById('clear-search-btn');
    const searchInput = document.getElementById('search-input');

    function toggleClearButton() {
        clearButton.style.display = searchInput.value.trim() !== '' ? 'block' : 'none';
    }
    searchInput.addEventListener('keyup', toggleClearButton);

    clearButton.addEventListener('click', function () {
        searchInput.value = '';
        clearButton.style.display = 'none';
    });

    toggleClearButton();
});
