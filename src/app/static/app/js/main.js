import toastManager from './toastManager.js';

document.addEventListener('DOMContentLoaded', function () {
    const toastManager = new ToastManager();

    // Affiche les messages Django au chargement de la page
    toastManager.showDjangoMessages();


});



// Loader for all forms
document.addEventListener('DOMContentLoaded', function () {
    const loader = document.getElementById('loader');
    const forms = document.getElementsByTagName('form');

    // Affiche le loader lors de la soumission de chaque formulaire
    for (let i = 0; i < forms.length; i++) {
        forms[i].addEventListener('submit', function () {
            loader.style.display = 'flex';  // Affiche le loader
        });
    }
});

//Listener to backbutton 
document.addEventListener('DOMContentLoaded', function () {
    const backButtons = document.getElementsByClassName('returnButton');
    for (let i = 0; i < backButtons.length; i++) {
        backButtons[i].innerHTML = '<i class="bi bi-arrow-left-circle"></i>';
        backButtons[i].addEventListener('click', function () {
            backButtons[i].innerHTML = '<i class="bi bi-arrow-left-circle-fill"></i>';
        });

    }
})

