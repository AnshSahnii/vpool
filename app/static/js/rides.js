// Client-side helpers for ride search & matching page
document.addEventListener('DOMContentLoaded', () => {
    const matchForm = document.getElementById('match-form');
    if (matchForm) {
        matchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(matchForm);
            const payload = Object.fromEntries(formData.entries());
            const resultsEl = document.getElementById('match-results');
            resultsEl.innerHTML = '<div class="text-muted">Searching for best matches...</div>';
            try {
                const res = await vpoolApi('/api/rides/match', { method: 'POST', body: payload });
                const matches = res.data;
                if (!matches.length) {
                    resultsEl.innerHTML = '<div class="alert alert-warning">No matching rides found for that route/time.</div>';
                    return;
                }
                resultsEl.innerHTML = matches.map(m => `
                    <div class="card ride-card mb-2 p-3">
                        <div class="d-flex justify-content-between">
                            <div>
                                <strong>${m.ride.pickup_location}</strong> &rarr; <strong>${m.ride.destination}</strong>
                                <div class="small text-muted">Departure: ${new Date(m.ride.departure_time).toLocaleString()}</div>
                                <div class="small text-muted">Driver: ${m.ride.driver ? m.ride.driver.name : 'N/A'} | Seats left: ${m.ride.available_seats}</div>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-success">Match score: ${m.score}</span>
                                <div class="small text-muted mt-1">Time diff: ${m.time_diff_minutes} min</div>
                                <a href="/rides/${m.ride.id}" class="btn btn-sm btn-vp-primary mt-2">View</a>
                            </div>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                resultsEl.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
            }
        });
    }
});
