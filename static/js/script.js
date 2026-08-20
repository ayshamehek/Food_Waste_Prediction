// Small UX helpers for the FoodSaver app

document.addEventListener("DOMContentLoaded", function () {
    const purchaseInput = document.querySelector('input[name="purchase_date"]');
    const expiryInput = document.querySelector('input[name="expiry_date"]');

    if (purchaseInput && !purchaseInput.value) {
        const today = new Date().toISOString().split("T")[0];
        purchaseInput.value = today;
    }

    if (purchaseInput && expiryInput) {
        const syncMin = () => {
            if (purchaseInput.value) {
                expiryInput.min = purchaseInput.value;
            }
        };
        syncMin();
        purchaseInput.addEventListener("change", syncMin);
    }

    document.querySelectorAll(".alert").forEach((alertEl) => {
        setTimeout(() => {
            alertEl.style.transition = "opacity 0.5s ease";
            alertEl.style.opacity = "0";
            setTimeout(() => alertEl.remove(), 500);
        }, 5000);
    });

    const rows = document.querySelectorAll(".inventory-row");
    rows.forEach((row, index) => {
        row.style.animation = `riseIn 0.45s ease ${index * 0.08}s both`;
    });

    const cards = document.querySelectorAll(".reveal-card");
    cards.forEach((card, index) => {
        card.style.animation = `riseIn 0.45s ease ${index * 0.08}s both`;
    });
});
