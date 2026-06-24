const views = document.querySelectorAll('.view');
const menuItems = document.querySelectorAll('.menu-item');

menuItems.forEach(item => {
    item.addEventListener('click', () => {
        menuItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        views.forEach(v => v.classList.remove('active'));
        document.getElementById(item.dataset.target).classList.add('active');
        if(item.dataset.target === 'dashboard') loadStats();
        if(item.dataset.target === 'tasks') loadTasks();
        if(item.dataset.target === 'assistant') loadChat();
        if(item.dataset.target === 'reports') loadReports();
    });
});

const showLoader = () => document.getElementById('loader-modal').classList.add('active');
const hideLoader = () => document.getElementById('loader-modal').classList.remove('active');

async function loadStats() {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-total').innerText = data.total;
    document.getElementById('stat-completed').innerText = data.concluidas;
    document.getElementById('stat-doing').innerText = data.em_andamento;
    document.getElementById('stat-pending').innerText = data.pendentes;
}

async function loadTasks() {
    const res = await fetch('/api/tasks');
    const tasks = await res.json();
    const list = document.getElementById('task-list');
    list.innerHTML = '';
    
    if (tasks.length === 0) {
        list.innerHTML = '<p style="color: var(--text-muted);">No tasks found.</p>';
        return;
    }
    
    tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.innerHTML = `
            <div class="task-header">
                <div>
                    <div class="task-title">${t.title}</div>
                    ${t.description ? `<div class="task-desc">${t.description}</div>` : ''}
                </div>
                <div class="badge">${t.status.replace('_', ' ')}</div>
            </div>
            <div class="task-meta">
                <span>Priority: <strong style="text-transform:capitalize;">${t.priority}</strong></span>
                ${t.due_date ? `<span>Due: <strong>${new Date(t.due_date).toLocaleDateString()}</strong></span>` : ''}
                ${t.estimated_minutes ? `<span>Est: <strong>${t.estimated_minutes} min</strong></span>` : ''}
                ${t.ai_priority_score ? `<span>Score: <strong>${t.ai_priority_score}</strong></span>` : ''}
            </div>
            ${t.ai_reasoning ? `<p style="font-size:12px;color:var(--text-muted);margin-bottom:12px;"><strong>AI:</strong> ${t.ai_reasoning}</p>` : ''}
            ${t.subtasks && t.subtasks.length > 0 ? `
                <div style="margin: 16px 0; font-size: 13px;">
                    <strong>Subtasks:</strong>
                    <ul style="padding-left: 20px; color: var(--text-muted); margin-top: 8px;">
                        ${t.subtasks.map(s => `<li>${s.done ? '<del>' : ''}${s.title}${s.done ? '</del>' : ''}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            <div class="task-actions">
                <select class="input-field" style="width: auto; margin:0;" onchange="updateStatus(${t.id}, this.value)">
                    <option value="pendente" ${t.status === 'pendente'?'selected':''}>Pending</option>
                    <option value="em_andamento" ${t.status === 'em_andamento'?'selected':''}>In Progress</option>
                    <option value="concluida" ${t.status === 'concluida'?'selected':''}>Completed</option>
                </select>
                <button class="btn secondary" onclick="decompose(${t.id})">Decompose</button>
                <button class="btn secondary" onclick="estimate(${t.id})">Estimate</button>
                <button class="btn secondary" style="color:var(--primary);" onclick="deleteTask(${t.id})">Delete</button>
            </div>
        `;
        list.appendChild(card);
    });
}

async function updateStatus(id, status) {
    await fetch(`/api/tasks/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status})
    });
    loadTasks();
    loadStats();
}

async function deleteTask(id) {
    if(!confirm('Are you sure you want to delete this task?')) return;
    await fetch(`/api/tasks/${id}`, {method: 'DELETE'});
    loadTasks();
    loadStats();
}

async function decompose(id) {
    showLoader();
    try {
        await fetch(`/api/tasks/${id}/decompose`, {method: 'POST'});
    } catch(e) {
        alert('Error decomposing task');
    }
    hideLoader();
    loadTasks();
}

async function estimate(id) {
    showLoader();
    try {
        await fetch(`/api/tasks/${id}/estimate`, {method: 'POST'});
    } catch(e) {
        alert('Error estimating task');
    }
    hideLoader();
    loadTasks();
}

// Modal handling
const modal = document.getElementById('task-modal');
document.getElementById('btn-new-task').onclick = () => modal.classList.add('active');
document.getElementById('btn-cancel-task').onclick = () => modal.classList.remove('active');

document.getElementById('btn-save-task').onclick = async () => {
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-desc').value;
    const priority = document.getElementById('task-priority').value;
    const due_date = document.getElementById('task-due').value;
    
    if(!title) return alert('Title is required');
    
    await fetch('/api/tasks', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, description, priority, due_date: due_date || null})
    });
    
    modal.classList.remove('active');
    document.getElementById('task-title').value = '';
    document.getElementById('task-desc').value = '';
    document.getElementById('task-due').value = '';
    loadTasks();
    loadStats();
};

// Chat
async function loadChat() {
    const res = await fetch('/api/chat');
    const history = await res.json();
    const container = document.getElementById('chat-history');
    container.innerHTML = history.map(m => `
        <div class="chat-message ${m.role}">
            ${marked.parse(m.content)}
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

document.getElementById('btn-send').onclick = async () => {
    const input = document.getElementById('chat-input');
    const msg = input.value;
    if(!msg) return;
    
    input.value = '';
    const container = document.getElementById('chat-history');
    container.innerHTML += `<div class="chat-message user">${msg}</div>`;
    container.scrollTop = container.scrollHeight;
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: msg})
        });
        const data = await res.json();
        container.innerHTML += `<div class="chat-message assistant">${marked.parse(data.reply)}</div>`;
    } catch(e) {
        container.innerHTML += `<div class="chat-message assistant">Error sending message.</div>`;
    }
    container.scrollTop = container.scrollHeight;
};

// Reports
async function loadReports() {
    const res = await fetch('/api/reports');
    const reports = await res.json();
    const list = document.getElementById('reports-list');
    list.innerHTML = '';
    
    if (reports.length === 0) {
        list.innerHTML = '<p style="color: var(--text-muted);">No reports found.</p>';
        return;
    }
    
    reports.forEach(r => {
        const card = document.createElement('div');
        card.className = 'report-card';
        card.innerHTML = `
            <h3 style="margin-bottom:12px;font-size:16px;">Report from ${new Date(r.date).toLocaleString()}</h3>
            <div style="font-size:14px;line-height:1.6;color:var(--text-muted);">${marked.parse(r.content)}</div>
        `;
        list.appendChild(card);
    });
}

document.getElementById('btn-generate-report').onclick = async () => {
    showLoader();
    try {
        await fetch('/api/reports', {method: 'POST'});
        await loadReports();
    } catch(e) {
        alert('Error generating report');
    }
    hideLoader();
};

// Initial load
loadStats();
