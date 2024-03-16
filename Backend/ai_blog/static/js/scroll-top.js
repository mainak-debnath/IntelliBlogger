document.addEventListener('DOMContentLoaded', function () {
    const scrollToTopBtn = document.getElementById('return-to-top');

    // Show or hide the arrow based on scroll position
    window.addEventListener('scroll', function () {
        if (window.pageYOffset > 100) {
            scrollToTopBtn.style.display = 'block';
        } else {
            scrollToTopBtn.style.display = 'none';
        }
    });

    // Scroll to top when the arrow is clicked
    scrollToTopBtn.addEventListener('click', function (event) {
        event.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});