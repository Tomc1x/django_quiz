import toastManager from './toastManager.js';

document.addEventListener('DOMContentLoaded', function () {
    const toastManager = new ToastManager();

    // Affiche les messages Django au chargement de la page
    toastManager.showDjangoMessages();

    // Exemple d'utilisation manuelle
    toastManager.toast('success', 'Ceci est un toast de succès !');
    toastManager.toast('error', 'Ceci est un toast d\'erreur !');
});