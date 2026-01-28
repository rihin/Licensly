const token = localStorage.getItem('token');
const role = localStorage.getItem('role');


if (!token || !role) {
    window.location.href = '/';
}

document.getElementById('user-role').innerText = role;

// role specific visibility
if (role === 'support') {
    document.getElementById('support-actions').classList.remove('hidden');
    document.getElementById('th-finalize').classList.remove('hidden');
} else if (role === 'accounts' || role === 'license') {
    document.getElementById('th-accounts').classList.remove('hidden');
}

// License column visible for everyone to see status/comments
document.getElementById('th-license').classList.remove('hidden');

// WebSocket
const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);

ws.onmessage = (event) => {
    console.log('Update received:', event.data);
    fetchRequests();
};

async function fetchRequests() {
    try {
        const res = await fetch('/requests', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) window.location.href = '/';
        const requests = await res.json();
        renderTable(requests);
    } catch (err) {
        console.error(err);
    }
}

function updateStats(requests) {
    const total = requests.length;
    const pending = requests.filter(r => !r.license_given && !r.license_rejected).length;
    const ready = requests.filter(r => r.accounts_verified && !r.sent_to_client).length;
    const completed = requests.filter(r => r.sent_to_client).length;

    document.getElementById('stat-total').innerText = total;
    document.getElementById('stat-pending').innerText = pending;
    document.getElementById('stat-ready').innerText = ready;
    document.getElementById('stat-completed').innerText = completed;

    // Update trend labels
    const trendTotal = document.querySelector('.stat-card:nth-child(1) .stat-trend');
    if (trendTotal) trendTotal.innerHTML = `<i class="fas fa-arrow-right"></i> Live Pipeline`;
}

function renderTable(requests) {
    const tbody = document.getElementById('requests-body');
    tbody.innerHTML = '';

    updateStats(requests);

    requests.forEach(req => {
        const tr = document.createElement('tr');

        let status = 'Pending';
        let statusClass = 'status-pending';
        let statusIcon = 'fa-clock';

        if (req.sent_to_client) {
            status = 'Completed';
            statusClass = 'status-completed';
            statusIcon = 'fa-check-double';
        } else if (req.accounts_verified) {
            status = 'Ready for Delivery';
            statusClass = 'status-completed';
            statusIcon = 'fa-truck-fast';
        } else if (req.license_given) {
            status = 'License Given';
            statusClass = 'status-licensed';
            statusIcon = 'fa-key';
        } else if (req.license_rejected) {
            status = 'Rejected';
            statusClass = 'status-rejected';
            statusIcon = 'fa-circle-xmark';
        } else if (req.license_verified) {
            status = 'License Verified';
            statusClass = 'status-verified';
            statusIcon = 'fa-circle-check';
        }

        let html = `
            <td>
                <span class="badge ${statusClass}">
                    <i class="fas ${statusIcon} me-1"></i> ${status}
                </span>
            </td>

            <td class="fw-semibold text-dark">${req.server_name}</td>

            <td class="text-muted" style="font-size: 0.8rem;">
                <i class="far fa-calendar-alt me-1"></i>
                ${new Date(req.created_at + 'Z').toLocaleString()}
            </td>

            <td>
                <div onclick="openPreview('${req.screenshot_url}')" style="cursor: pointer;">
                    <img src="${req.screenshot_url}" class="preview-img" alt="Screenshot Preview">
                </div>
            </td>

            <td class="text-muted" style="font-size: 0.85rem;">
                ${req.support_comment || '<span class="opacity-50">No notes</span>'}
            </td>
        `;

        // Role Specific Columns

        // ACCOUNTS COLUMN (Now checks AFTER license)
        // ACCOUNTS COLUMN (Now checks AFTER license)
        if (role === 'accounts' || role === 'license') {
            if (req.accounts_verified) {
                html += `<td><span class="badge status-completed">Updated</span> <br><small>${new Date(req.accounts_verified_at + 'Z').toLocaleString()}</small></td>`;
            } else if (role === 'accounts' && req.license_given) {
                // Actions only for Accounts team
                html += `
                    <td>
                        <button onclick="checkAccounts('${req.id}', true)" class="btn btn-primary">Update in Billing</button>
                    </td>`;
            } else {
                html += `<td><small>Waiting for License</small></td>`;
            }
        }

        // LICENSE COLUMN (Verify First, Then Grant)
        // LICENSE COLUMN (Visible to ALL)
        // License Team: sees Actions (or result)
        // Others: sees Status + Comment
        {
            let actionHtml = '';

            if (req.license_given) {
                // Modified: Show 'Granted' badge instead of key + Timestamp + Comment
                actionHtml = `<span class="badge status-licensed">Granted</span> <br><small>${new Date(req.license_given_at + 'Z').toLocaleString()}</small> <br><small>Ref: ${req.license_comment || '-'}</small>`;
            } else if (req.license_rejected) {
                actionHtml = `<span class="badge status-rejected">Rejected</span> <br><small>${new Date(req.license_rejected_at + 'Z').toLocaleString()}</small> <br><small>Reason: ${req.license_comment || '-'}</small>`;
            } else {
                // Pending
                if (role === 'license') {
                    // Show Actions for License Team
                    actionHtml = `
                        <div style="display:flex; flex-direction:column; gap:5px;">
                            <input type="text" id="comment-${req.id}" placeholder="Comment (Optional)" style="padding:4px;">
                            <div style="display:flex; gap:5px;">
                                <button onclick="grantLicense('${req.id}')" class="btn btn-primary" style="flex:1;">Grant</button>
                                <button onclick="rejectLicense('${req.id}')" class="btn btn-danger" style="flex:1;">Reject</button>
                            </div>
                        </div>
                    `;
                } else {
                    // Others: Show Waiting status
                    actionHtml = `<span class="badge status-pending">Waiting for License</span>`;
                }
            }
            html += `<td>${actionHtml}</td>`;
        }

        // SUPPORT FINALIZE COLUMN
        if (role === 'support') {
            if (req.sent_to_client) {
                // Modified: Show Delivered with Timestamp instead of link
                html += `<td><span class="badge status-completed">Delivered</span> <br><small>${new Date(req.updated_at + 'Z').toLocaleString()}</small></td>`;
            } else if (req.accounts_verified) { // Only finalize if accounts updated
                html += `
                    <td>
                        <button onclick="finalizeRequest(event, '${req.id}')" class="btn btn-primary" style="width:100%;">Deliver to Client</button>
                    </td>
                 `;
            } else {
                html += `<td>-</td>`;
            }
        }


        tr.innerHTML = html;
        tbody.appendChild(tr);
    });
}



// 2. License Grant (Auto Key)
async function grantLicense(id) {
    const comment = document.getElementById(`comment-${id}`).value;

    // Direct action, no confirmation
    const formData = new FormData();
    formData.append('license_comment', comment || 'Granted');

    await fetch(`/requests/${id}/license`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
}

// 2.5 License Reject
async function rejectLicense(id) {
    // Direct action, no confirmation
    await fetch(`/requests/${id}/reject`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
    });
}

// 3. Accounts Check
async function checkAccounts(id, approved) {
    // Direct action
    const formData = new FormData();
    formData.append('approved', approved);

    await fetch(`/requests/${id}/accounts-check`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
}

// 4. Support Finalize
async function finalizeRequest(e, id) {
    if (e) e.preventDefault();
    // Direct action

    await fetch(`/requests/${id}/finalize`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
        // No body needed as we removed file requirement
    });
}

// Helper
async function fetchRequest(url, method) {
    try {
        await fetch(url, {
            method: method,
            headers: { 'Authorization': `Bearer ${token}` }
        });
    } catch (e) {
        console.error(e);
    }
}

// Support Create Request
document.getElementById('createRequestForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const screenshot = formData.get('screenshot');

    console.log('Submitting request...', {
        server_name: formData.get('server_name'),
        screenshot_size: screenshot ? screenshot.size : 'N/A',
        comment: formData.get('support_comment')
    });

    // 🔒 SAFETY CHECK
    if (!screenshot || (screenshot instanceof File && screenshot.size === 0)) {
        alert('Please paste or select a screenshot');
        return;
    }

    try {
        const res = await fetch('/requests/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (res.ok) {
            e.target.reset();
            document.getElementById('paste-preview')?.classList.add('hidden');
            fetchRequests(); // Force immediate update
        } else {
            const err = await res.text();
            console.error(err);
            alert('Error creating request');
        }
    } catch (err) {
        console.error(err);
    }
});


// Initial Load
fetchRequests();
// ===============================
// PASTE SCREENSHOT SUPPORT
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    const pasteArea = document.getElementById("paste-area");
    const fileInput = document.getElementById("screenshot-input");
    const previewImg = document.getElementById("paste-preview");

    // If user is not support or page doesn't have paste UI
    if (!pasteArea || !fileInput || !previewImg) return;

    // Click paste area → open file picker
    pasteArea.addEventListener("click", () => {
        fileInput.click();
    });

    // File selected manually
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            showPreview(fileInput.files[0]);
        }
    });

    // Paste from clipboard (Ctrl + V)
    window.addEventListener("paste", (event) => {
        const items = event.clipboardData?.items;
        if (!items) return;

        for (const item of items) {
            if (item.type.startsWith("image")) {
                const file = item.getAsFile();

                // Attach pasted image to file input
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;

                showPreview(file);
                break;
            }
        }
    });

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = () => {
            previewImg.src = reader.result;
            previewImg.classList.remove("hidden");
            pasteArea.querySelector("p").textContent = "Screenshot attached";
        };
        reader.readAsDataURL(file);
    }
});

// ===============================
// INTERACTIVE PREVIEW MODAL
// ===============================
function openPreview(url) {
    const modal = document.getElementById('image-preview-modal');
    const modalImg = document.getElementById('modal-img');
    if (modal && modalImg) {
        modalImg.src = url;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Disable scroll
    }
}

function closePreview() {
    const modal = document.getElementById('image-preview-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto'; // Re-enable scroll
    }
}

// ESC Key Listener
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePreview();
    }
});
