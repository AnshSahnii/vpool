// Global small helpers used across pages
document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 5s
    document.querySelectorAll('.alert').forEach((alertEl) => {
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            alert.close();
        }, 5000);
    });
});

// Simple fetch wrapper for our JSON REST API
async function vpoolApi(url, options = {}) {
    const opts = Object.assign({
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
    }, options);
    if (opts.body && typeof opts.body !== 'string') {
        opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, opts);
    const data = await res.json();
    if (!res.ok || data.success === false) {
        throw new Error(data.message || 'Request failed');
    }
    return data;
}
