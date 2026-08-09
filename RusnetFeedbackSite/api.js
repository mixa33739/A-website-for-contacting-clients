const API_URL = 'http://localhost:5000/api';
function getToken() {
    return localStorage.getItem('token');
}
function setToken(token) {
    localStorage.setItem('token', token);
}
async function fetchAuth(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });
        const data = await response.json();
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = 'login.html';
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }
            throw new Error(data.error || data.msg || 'Ошибка сервера');
        }
        return data;
    } catch (error) {
        console.error('Ошибка запроса:', error);
        throw error;
    }
}
async function handleLogin(email, password) {
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (response.ok) {
            setToken(data.access_token);
            if (data.user.role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.href = 'dashboard.html';
            }
        } else {
            alert('Ошибка входа: ' + (data.error || data.msg));
        }
    } catch (error) {
        alert('Ошибка соединения с сервером. Убедитесь, что сервер запущен.');
        console.error('Login error:', error);
    }
}
function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}
async function loadTickets() {
    try {
        const data = await fetchAuth('/tickets');
        renderTickets(data.tickets);
    } catch (error) {
        console.error('Не удалось загрузить обращения:', error);
        alert('Ошибка загрузки обращений');
    }
}
function renderTickets(tickets) {
    const tbody = document.getElementById('ticketsBody');
    const noTicketsMsg = document.getElementById('noTicketsMessage');
    const tableContainer = document.getElementById('ticketsTableContainer');
    if (!tbody || !noTicketsMsg || !tableContainer) {
        console.warn('Не найдены необходимые элементы');
        return;
    }
    if (tickets.length === 0) {
        noTicketsMsg.style.display = 'block';
        tableContainer.style.display = 'none';
        return;
    }
    noTicketsMsg.style.display = 'none';
    tableContainer.style.display = 'block';
    tbody.innerHTML = '';
    tickets.forEach(ticket => {
        const row = document.createElement('tr');
        let statusColor = '#ccc';
        if (ticket.status.name === 'Новое') statusColor = '#3498db';
        if (ticket.status.name === 'В работе') statusColor = '#f39c12';
        if (ticket.status.name === 'Решено') statusColor = '#27ae60';
        if (ticket.status.name === 'Закрыто') statusColor = '#95a5a6';
        row.innerHTML = `
            <td>${ticket.subject}</td>
            <td>${ticket.site.name}</td>
            <td>${new Date(ticket.created_at).toLocaleString('ru-RU')}</td>
            <td><span style="color:${statusColor}; font-weight:bold;">${ticket.status.name}</span></td>
            <td><button class="btn-small" onclick="alert('ID: ${ticket.id}\\nТема: ${ticket.subject}\\nОписание: ${ticket.description}')">Подробнее</button></td>
        `;
        tbody.appendChild(row);
    });
}
async function createTicket(subject, description, siteId, priority = 'medium') {
    try {
        await fetchAuth('/tickets', {
            method: 'POST',
            body: JSON.stringify({
                subject,
                description,
                site_id: parseInt(siteId),
                priority
            })
        });
        return true;
    } catch (error) {
        console.error('Ошибка создания обращения:', error);
        throw error;
    }
}
async function updateStatus(ticketId, newStatus) {
    try {
        await fetchAuth(`/tickets/${ticketId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status: newStatus })
        });
        console.log(`Статус обращения ${ticketId} обновлен на: ${newStatus}`);
        return true;
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
        alert('Ошибка обновления статуса');
        throw error;
    }
}
async function loadSites() {
    try {
        const data = await fetchAuth('/tickets/sites');
        populateSiteSelect(data.sites);
    } catch (error) {
        console.error('Не удалось загрузить список сайтов:', error);
        const select = document.getElementById('ticketSite');
        if (select) {
            select.innerHTML = '<option value="" disabled selected>-- Ошибка загрузки --</option>';
        }
    }
}
function populateSiteSelect(sites) {
    const select = document.getElementById('ticketSite');
    if (!select) {
        console.warn('Элемент ticketSite не найден');
        return;
    }
    select.innerHTML = '<option value="" disabled selected>-- Выберите сайт --</option>';
    const activeSites = sites.filter(s => s.category === 'active');
    const archiveSites = sites.filter(s => s.category === 'archive');
    const foreignSites = sites.filter(s => s.category === 'foreign');
    if (activeSites.length > 0) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = 'Активные проекты';
        activeSites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = site.name;
            optgroup.appendChild(option);
        });
        select.appendChild(optgroup);
    }
    if (archiveSites.length > 0) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = 'Архивные проекты';
        archiveSites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = site.name + ' (Архив)';
            optgroup.appendChild(option);
        });
        select.appendChild(optgroup);
    }
    if (foreignSites.length > 0) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = 'Зарубежные проекты';
        foreignSites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = site.name;
            optgroup.appendChild(option);
        });
        select.appendChild(optgroup);
    }
    const otherOption = document.createElement('option');
    otherOption.value = 'other';
    otherOption.textContent = 'Другое';
    select.appendChild(otherOption);
}
async function loadAdminTickets() {
    try {
        const data = await fetchAuth('/tickets');
        renderAdminTable(data.tickets);
    } catch (error) {
        console.error('Ошибка загрузки обращений для админа:', error);
        alert('Ошибка загрузки данных');
    }
}
function renderAdminTable(tickets) {
    const tbody = document.getElementById('adminTicketsBody');
    if (!tbody) {
        console.warn('Элемент adminTicketsBody не найден');
        return;
    }
    tbody.innerHTML = '';
    if (tickets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;">Заявок пока нет</td></tr>';
        return;
    }
    tickets.forEach(ticket => {
        const row = document.createElement('tr');
        let statusClass = '';
        if (ticket.status.name === 'Новое') statusClass = 'status-new';
        if (ticket.status.name === 'В работе') statusClass = 'status-progress';
        if (ticket.status.name === 'Решено') statusClass = 'status-resolved';
        if (ticket.status.name === 'Закрыто') statusClass = 'status-closed';
        row.innerHTML = `
            <td>${ticket.id}</td>
            <td>${new Date(ticket.created_at).toLocaleString('ru-RU')}</td>
            <td>${ticket.site.name}</td>
            <td>${ticket.subject}</td>
            <td>
                <select onchange="handleStatusChange(${ticket.id}, this.value)"
                        class="status-select ${statusClass}">
                    <option value="Новое" ${ticket.status.name === 'Новое' ? 'selected' : ''}>Новое</option>
                    <option value="В работе" ${ticket.status.name === 'В работе' ? 'selected' : ''}>В работе</option>
                    <option value="Решено" ${ticket.status.name === 'Решено' ? 'selected' : ''}>Решено</option>
                    <option value="Закрыто" ${ticket.status.name === 'Закрыто' ? 'selected' : ''}>Закрыто</option>
                </select>
            </td>
            <td><button class="btn-save" onclick="saveStatus(${ticket.id})">Сохранить</button></td>
        `;

        tbody.appendChild(row);
    });
}
function handleStatusChange(ticketId, newStatus) {
    const select = event.target;
    select.dataset.ticketId = ticketId;
    select.dataset.newStatus = newStatus;
}
async function saveStatus(ticketId) {
    try {
        const select = document.querySelector(`select[dataset-ticket-id="${ticketId}"]`) ||
                      event.target.previousElementSibling;
        const newStatus = select.value;
        await updateStatus(ticketId, newStatus);
        alert('Статус успешно обновлен!');
        select.className = 'status-select';
        if (newStatus === 'Новое') select.classList.add('status-new');
        if (newStatus === 'В работе') select.classList.add('status-progress');
        if (newStatus === 'Решено') select.classList.add('status-resolved');
        if (newStatus === 'Закрыто') select.classList.add('status-closed');
    } catch (error) {
        console.error('Ошибка сохранения статуса:', error);
    }
}
async function handleLogin(email, password) {
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (response.ok) {
            setToken(data.access_token);
            localStorage.setItem('userName', data.user.name);
            if (data.user.role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.href = 'dashboard.html';
            }
        } else {
            alert('Ошибка: ' + (data.error || data.msg));
        }
    } catch (error) {
        alert('Ошибка соединения с сервером');
    }
}
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    window.location.href = 'login.html';
}
window.handleLogin = handleLogin;
window.logout = logout;
window.loadTickets = loadTickets;
window.renderTickets = renderTickets;
window.createTicket = createTicket;
window.updateStatus = updateStatus;
window.loadSites = loadSites;
window.populateSiteSelect = populateSiteSelect;
window.loadAdminTickets = loadAdminTickets;
window.renderAdminTable = renderAdminTable;
window.handleStatusChange = handleStatusChange;
window.saveStatus = saveStatus;
window.fetchAuth = fetchAuth;