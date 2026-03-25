// ========== Глобальные переменные ==========
let currentChat = null;
let chats = [];

// ========== DOM элементы ==========
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const uploadBtn = document.getElementById('uploadBtn');
const chatList = document.getElementById('chatList');
const labNameDisplay = document.getElementById('labNameDisplay');
const currentLabDisplay = document.getElementById('currentLabDisplay');

// Модальное окно
const modal = document.getElementById('uploadModal');
const closeBtn = document.querySelector('.close');
const confirmUploadBtn = document.getElementById('confirmUploadBtn');
const cancelUploadBtn = document.getElementById('cancelUploadBtn');
const labNameInput = document.getElementById('labNameInput');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');

// ========== Инициализация ==========
document.addEventListener('DOMContentLoaded', () => {
    loadChats();
    setupEventListeners();
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', createNewChat);
    uploadBtn.addEventListener('click', openUploadModal);
    closeBtn.addEventListener('click', closeUploadModal);
    cancelUploadBtn.addEventListener('click', closeUploadModal);
    confirmUploadBtn.addEventListener('click', uploadFiles);
    fileInput.addEventListener('change', updateFileList);
    
    // Закрытие модального окна при клике вне
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeUploadModal();
        }
    });
}

// ========== Работа с чатами ==========
async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        chats = await response.json();
        renderChatList();
        
        // Если есть чаты, открываем первый
        if (chats.length > 0) {
            await switchChat(chats[0].id);
        }
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
    }
}

function renderChatList() {
    if (chats.length === 0) {
        chatList.innerHTML = '<div class="empty-chats">Нет чатов. Создайте новый</div>';
        return;
    }
    
    chatList.innerHTML = chats.map(chat => `
        <div class="chat-item ${currentChat?.id === chat.id ? 'active' : ''}" onclick="switchChat('${chat.id}')">
            <div class="chat-title">${escapeHtml(chat.title)}</div>
            ${chat.lab_name ? `<div class="chat-lab">🔬 ${escapeHtml(chat.lab_name)}</div>` : ''}
            <div class="chat-date">${formatDate(chat.created_at)}</div>
        </div>
    `).join('');
}

async function switchChat(chatId) {
    currentChat = chats.find(c => c.id === chatId);
    
    // Обновляем отображение лаборатории
    const labName = currentChat.lab_name || 'Общая база';
    labNameDisplay.textContent = labName;
    currentLabDisplay.textContent = labName;
    
    renderChatList();
    renderMessages();
}

async function createNewChat() {
    try {
        const labName = labNameDisplay.textContent !== 'Общая база' ? labNameDisplay.textContent : '';
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lab_name: labName || undefined })
        });
        
        const newChat = await response.json();
        chats.unshift(newChat);
        await switchChat(newChat.id);
        renderChatList();
    } catch (error) {
        console.error('Ошибка создания чата:', error);
        alert('Не удалось создать чат');
    }
}

function renderMessages() {
    if (!currentChat || currentChat.messages.length === 0) {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Добро пожаловать в РЕГМЕД</h2>
                <p>Задайте вопрос по ГОСТам или загрузите свои документы</p>
                <p class="small">💡 Совет: загрузите PDF с ГОСТами вашей лаборатории, и я буду отвечать на их основе</p>
            </div>
        `;
        return;
    }
    
    chatMessages.innerHTML = currentChat.messages.map(msg => `
        <div class="message ${msg.role}">
            <div class="message-content">
                ${escapeHtml(msg.content)}
                ${msg.sources ? `<div class="sources">📚 Источники: ${escapeHtml(msg.sources.join(', '))}</div>` : ''}
            </div>
        </div>
    `).join('');
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ========== Отправка сообщения ==========
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || !currentChat) return;
    
    // Добавляем сообщение пользователя в UI
    const userMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
    };
    currentChat.messages.push(userMessage);
    renderMessages();
    
    // Очищаем поле ввода
    messageInput.value = '';
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    // Показываем индикатор печати
    showTypingIndicator();
    
    try {
        const labName = currentChat.lab_name || '';
        const response = await fetch(`/api/chats/${currentChat.id}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: currentChat.id,
                message: message,
                lab_name: labName
            })
        });
        
        const answer = await response.json();
        
        // Убираем индикатор
        hideTypingIndicator();
        
        // Добавляем ответ ассистента
        const assistantMessage = {
            role: 'assistant',
            content: answer.response,
            sources: answer.sources,
            timestamp: new Date().toISOString()
        };
        currentChat.messages.push(assistantMessage);
        renderMessages();
        
        // Обновляем список чатов (для отображения последнего сообщения)
        renderChatList();
        
    } catch (error) {
        hideTypingIndicator();
        console.error('Ошибка отправки сообщения:', error);
        alert('Ошибка при отправке сообщения');
    } finally {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

// ========== Загрузка файлов ==========
function openUploadModal() {
    labNameInput.value = currentChat?.lab_name || '';
    fileInput.value = '';
    fileList.innerHTML = '';
    modal.style.display = 'block';
}

function closeUploadModal() {
    modal.style.display = 'none';
    labNameInput.value = '';
    fileInput.value = '';
    fileList.innerHTML = '';
}

function updateFileList() {
    const files = Array.from(fileInput.files);
    fileList.innerHTML = files.map(file => `
        <div class="file-item">📄 ${escapeHtml(file.name)} (${formatFileSize(file.size)})</div>
    `).join('');
}

async function uploadFiles() {
    const labName = labNameInput.value.trim();
    const files = fileInput.files;
    
    if (!labName) {
        alert('Введите название лаборатории');
        return;
    }
    
    if (files.length === 0) {
        alert('Выберите файлы для загрузки');
        return;
    }
    
    // Обновляем отображение лаборатории
    labNameDisplay.textContent = labName;
    if (currentChat) {
        currentChat.lab_name = labName;
        renderChatList();
    }
    currentLabDisplay.textContent = labName;
    
    // Загружаем файлы
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('lab_name', labName);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log(`Загружен ${file.name}:`, result);
            
        } catch (error) {
            console.error(`Ошибка загрузки ${file.name}:`, error);
            alert(`Ошибка загрузки ${file.name}`);
        }
    }
    
    alert(`Загружено ${files.length} файлов для лаборатории "${labName}"`);
    closeUploadModal();
}

// ========== Вспомогательные функции ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'только что';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} мин назад`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} ч назад`;
    
    return date.toLocaleDateString('ru-RU');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Б';
    const k = 1024;
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}