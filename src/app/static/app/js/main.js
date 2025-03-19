import toastManager from './toastManager.js';

document.addEventListener('DOMContentLoaded', function () {
    const toastManager = new ToastManager();

    // Affiche les messages Django au chargement de la page
    toastManager.showDjangoMessages();


});



// Loader login
document.addEventListener('DOMContentLoaded', function () {
    const loader = document.getElementById('loader');
    const loginForm = document.getElementById('login-form');

    // Affiche le loader lors de la soumission du formulaire
    if (loginForm) {
        loginForm.addEventListener('submit', function () {
            loader.style.display = 'flex';  // Affiche le loader
        });
    }
});