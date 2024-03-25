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
    const readMoreContainer = document.getElementById('read-more-container');

    if (readMoreBtn && remainingContent && readMoreContainer) {
        readMoreBtn.addEventListener('click', function () {
            if (remainingContent.style.display === 'none') {
                remainingContent.style.display = 'block';
                // Update button text to "Read less" and move it inside the remaining content
                readMoreBtn.innerText = 'Read less';
                remainingContent.appendChild(readMoreBtn);
                // Hide the "Read more..." container
                readMoreContainer.style.display = 'none';
            } else {
                remainingContent.style.display = 'none';
                // Move button back to its original position and update text to "Read more..."
                readMoreBtn.innerText = 'Read more...';
                readMoreContainer.insertBefore(readMoreBtn, readMoreContainer.firstChild); // Insert before first child
                // Show the "Read more..." container
                readMoreContainer.style.display = 'block';
            }
        });
    }


});