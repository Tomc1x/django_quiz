export default class ToastManager {
    constructor() {
        this.toastContainer = document.getElementById('toast-container');
    }

    /**
     * Affiche un toast.
     * @param {string} type - Le type de toast (success, error, warning, info).
     * @param {string} message - Le message à afficher.
     */
    toast(type, message) {
        // Crée un nouvel élément toast
        const toastEl = document.createElement('div');
        toastEl.classList.add('toast');
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        // Ajoute les classes Bootstrap en fonction du type
        toastEl.classList.add('bg-' + type);

        // Structure interne du toast
        toastEl.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        // Ajoute le toast au conteneur
        this.toastContainer.appendChild(toastEl);

        // Initialise le toast avec Bootstrap
        const bootstrapToast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 5000, // Durée d'affichage du toast (5 secondes)
        });

        // Affiche le toast
        bootstrapToast.show();
    }

    /**
     * Affiche les messages Django sous forme de toasts.
     */
    showDjangoMessages() {
        // Récupère les messages Django depuis le template
        const messages = JSON.parse(document.getElementById('django-messages').textContent);

        // Affiche chaque message comme un toast
        messages.forEach(message => {
            this.toast(message.tags, message.message);
        });
    }
}

// Exporte la classe pour une utilisation globale
window.ToastManager = ToastManager;