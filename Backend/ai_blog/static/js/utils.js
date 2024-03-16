document.addEventListener('DOMContentLoaded', function () {
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent default link behavior
            window.history.back(); // Navigate to previous page in history
        });
    }

    const readMoreBtn = document.getElementById('read-more-btn');
    const remainingContent = document.getElementById('remaining-content');
    if (readMoreBtn && remainingContent) {
        readMoreBtn.addEventListener('click', function () {
            if (remainingContent.style.display === 'none') {
                remainingContent.style.display = 'block';
                readMoreBtn.innerText = 'Read less';
            } else {
                remainingContent.style.display = 'none';
                readMoreBtn.innerText = 'Read more...';
            }
        });
    }
});