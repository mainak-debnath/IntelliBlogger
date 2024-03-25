document.addEventListener('DOMContentLoaded', function () {
    const alertDismissed = sessionStorage.getItem('alertDismissed');
    if (!alertDismissed) {
        // Alert has not been dismissed, show it
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.style.display = 'block';
        }
    }
});

function dismissAlert() {
    const alertDiv = document.getElementById('error-alert');
    alertDiv.style.display = 'none';
    sessionStorage.setItem('alertDismissed', 'true');
}
