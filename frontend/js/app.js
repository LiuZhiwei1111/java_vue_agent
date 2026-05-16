// API 配置
const API_BASE_URL = 'http://localhost:8000';
let currentSessionId = null;
let isLoading = false;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadSessions();
    checkApiHealth();

    // 创建新会话（如果没有会话）
    setTimeout(() => {
        if (!currentSessionId) {
            createNewSession();
        }
    }, 500);
});

// 事件监听
function initEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    const newChatBtn = document.getElementById('newChatBtn');

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', createNewSession);

    // 示例问题按钮
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            messageInput.value = btn.textContent;
            sendMessage();
        });
    });
}

// 检查 API 健康状态
async function checkApiHealth() {
    const statusDot = document.getElementById('apiStatus');
    const statusText = document.getElementById('apiStatusText');

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            statusDot.className = 'status-dot online';
            statusText.textContent = '服务在线';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = '服务离线，请确保后端已启动';
        console.error('API health check failed:', error);
    }
}

// 加载所有会话
async function loadSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/sessions`);
        if (!response.ok) throw new Error('Failed to load sessions');

        const data = await response.json();
        const sessionList = document.getElementById('sessionList');

        // 获取所有会话ID（从会话管理器中获取）
        // 注意：后端需要实现获取所有会话的接口，这里我们通过前端存储来管理
        const sessions = getLocalSessions();

        if (sessions.length === 0) {
            sessionList.innerHTML = '<div style="text-align: center; color: #9ca3af; padding: 20px;">暂无会话<br>点击上方按钮创建</div>';
            return;
        }

        sessionList.innerHTML = sessions.map(session => `
            <div class="session-item ${currentSessionId === session.id ? 'active' : ''}" data-session-id="${session.id}">
                <div class="session-title">${escapeHtml(session.title || '新对话')}</div>
                <div class="session-preview">${escapeHtml(session.preview || '点击继续对话')}</div>
                <div class="session-time">${formatTime(session.lastTime)}</div>
                <span class="delete-session" data-id="${session.id}">删除</span>
            </div>
        `).join('');

        // 绑定会话点击事件
        document.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('delete-session')) {
                    e.stopPropagation();
                    deleteSession(e.target.dataset.id);
                } else {
                    switchSession(item.dataset.sessionId);
                }
            });
        });

        // 如果有当前会话，加载其历史
        if (currentSessionId) {
            await loadSessionHistory(currentSessionId);
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

// 获取本地存储的会话
function getLocalSessions() {
    const sessions = localStorage.getItem('chat_sessions');
    return sessions ? JSON.parse(sessions) : [];
}

// 保存会话到本地存储
function saveLocalSessions(sessions) {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
}

// 保存消息到本地
function saveMessage(sessionId, role, content, sources = null) {
    const sessions = getLocalSessions();
    let session = sessions.find(s => s.id === sessionId);

    if (!session) {
        session = {
            id: sessionId,
            title: '',
            messages: [],
            lastTime: Date.now()
        };
        sessions.push(session);
    }

    session.messages.push({
        role,
        content,
        sources,
        timestamp: Date.now()
    });

    session.lastTime = Date.now();

    // 更新标题（使用第一条用户消息）
    if (session.title === '' && role === 'user') {
        session.title = content.slice(0, 30) + (content.length > 30 ? '...' : '');
    }

    // 更新预览
    if (role === 'assistant') {
        session.preview = content.slice(0, 40) + (content.length > 40 ? '...' : '');
    }

    saveLocalSessions(sessions);
    loadSessions(); // 刷新会话列表
}

// 加载会话历史
async function loadSessionHistory(sessionId) {
    const sessions = getLocalSessions();
    const session = sessions.find(s => s.id === sessionId);

    if (!session || !session.messages) {
        // 如果没有本地消息，尝试从后端加载
        await loadSessionFromBackend(sessionId);
        return;
    }

    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    session.messages.forEach(msg => {
        if (msg.role === 'user') {
            addMessageToUI('user', msg.content);
        } else if (msg.role === 'assistant') {
            addMessageToUI('assistant', msg.content, msg.sources);
        }
    });

    if (session.messages.length === 0) {
        showWelcomeMessage();
    }

    scrollToBottom();
}

// 从后端加载会话历史
async function loadSessionFromBackend(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
        if (!response.ok) throw new Error('Failed to load session');

        const data = await response.json();
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';

        if (data.history && data.history.length > 0) {
            data.history.forEach(msg => {
                addMessageToUI(msg.role, msg.content);
            });
        } else {
            showWelcomeMessage();
        }
    } catch (error) {
        console.error('Failed to load session from backend:', error);
        showWelcomeMessage();
    }
}

// 创建新会话
function createNewSession() {
    currentSessionId = generateUUID();
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    showWelcomeMessage();

    // 保存空会话
    saveMessage(currentSessionId, 'system', '会话开始');
    loadSessions();
}

// 切换会话
async function switchSession(sessionId) {
    currentSessionId = sessionId;
    await loadSessionHistory(sessionId);
    loadSessions(); // 更新高亮
}

// 删除会话
function deleteSession(sessionId) {
    if (confirm('确定要删除这个会话吗？')) {
        let sessions = getLocalSessions();
        sessions = sessions.filter(s => s.id !== sessionId);
        saveLocalSessions(sessions);

        if (currentSessionId === sessionId) {
            if (sessions.length > 0) {
                switchSession(sessions[0].id);
            } else {
                createNewSession();
            }
        }

        loadSessions();
    }
}

// 发送消息
// 发送消息（流式版本）
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const question = input.value.trim();

    if (!question || isLoading) return;

    if (!currentSessionId) {
        currentSessionId = generateUUID();
    }

    // 清除欢迎消息
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // 添加用户消息到UI
    addMessageToUI('user', question);
    saveMessage(currentSessionId, 'user', question);

    // 清空输入框
    input.value = '';

    // 显示加载动画
    isLoading = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    // 创建一个空的AI消息容器
    const aiMessageId = addEmptyAssistantMessage();

    try {
        // 使用流式接口
        const response = await fetch(`${API_BASE_URL}/query/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                session_id: currentSessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullAnswer = '';
        let sources = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'meta') {
                            // 更新会话ID和来源
                            currentSessionId = data.session_id;
                            sources = data.sources;
                        } else if (data.type === 'content') {
                            // 累积并更新AI回复
                            fullAnswer += data.content;
                            updateAssistantMessage(aiMessageId, fullAnswer, sources);
                        } else if (data.type === 'error') {
                            updateAssistantMessage(aiMessageId, `❌ 错误: ${data.error}`, null);
                        } else if (data.type === 'end') {
                            // 流结束，保存完整回复
                            if (fullAnswer) {
                                saveMessage(currentSessionId, 'assistant', fullAnswer, sources);
                            }
                        }
                    } catch (e) {
                        console.error('解析JSON失败:', e, line);
                    }
                }
            }
        }

        // 加载会话列表
        loadSessions();

    } catch (error) {
        console.error('请求失败:', error);
        updateAssistantMessage(aiMessageId, `❌ 请求失败: ${error.message}\n\n请确保后端服务已启动（运行 python main.py）`, null);
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        input.focus();
    }
}
// 添加空的AI消息容器
function addEmptyAssistantMessage() {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now();
    messageDiv.className = 'message assistant';
    messageDiv.id = messageId;

    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="streaming-content"></div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageId;
}
// 合并会话
function mergeSessions(oldId, newId) {
    const sessions = getLocalSessions();
    const oldSession = sessions.find(s => s.id === oldId);
    const newSession = sessions.find(s => s.id === newId);

    if (oldSession && newSession) {
        newSession.messages = [...oldSession.messages, ...newSession.messages];
        sessions.splice(sessions.indexOf(oldSession), 1);
        saveLocalSessions(sessions);
    }
}
// 更新AI消息内容（流式）
function updateAssistantMessage(messageId, content, sources) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;

    const contentDiv = messageDiv.querySelector('.streaming-content');
    if (contentDiv) {
        // 使用 marked 渲染 Markdown
        let renderedContent = marked.parse(content);

        // 添加来源信息
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = '<div class="sources-info">📚 参考代码片段：';
            sources.forEach(source => {
                const fileName = source.source.split(/[\\/]/).pop();
                sourcesHtml += `<span class="source-item" title="${escapeHtml(source.source)}">📄 ${escapeHtml(fileName)}</span>`;
            });
            sourcesHtml += '</div>';
        }

        contentDiv.innerHTML = renderedContent + sourcesHtml;
        scrollToBottom();
    }
}
// 显示加载指示器
function showLoadingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const template = document.getElementById('loadingTemplate');
    const loadingDiv = template.content.cloneNode(true);
    const loadingElement = loadingDiv.firstElementChild;
    const id = 'loading-' + Date.now();
    loadingElement.id = id;
    chatMessages.appendChild(loadingElement);
    scrollToBottom();
    return id;
}

// 移除加载指示器
function removeLoadingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// 添加消息到UI
// 原有的 addMessageToUI 函数保持不变，但可以优化一下
function addMessageToUI(role, content, sources = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

    let contentHtml = '';
    if (role === 'assistant') {
        contentHtml = marked.parse(content);
    } else {
        contentHtml = `<p>${escapeHtml(content)}</p>`;
    }

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = '<div class="sources-info">📚 参考代码片段：';
        sources.forEach(source => {
            const fileName = source.source.split(/[\\/]/).pop();
            sourcesHtml += `<span class="source-item" title="${escapeHtml(source.source)}">📄 ${escapeHtml(fileName)}</span>`;
        });
        sourcesHtml += '</div>';
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${contentHtml}
            ${sourcesHtml}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示欢迎消息
function showWelcomeMessage() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages.children.length === 0) {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🚀</div>
                <h3>欢迎使用项目知识库智能体</h3>
                <p>我可以帮你解答关于这个 Java + Vue 项目的任何问题，例如：</p>
                <div class="example-questions">
                    <button class="example-btn">登录功能是怎么实现的？</button>
                    <button class="example-btn">用户管理的接口有哪些？</button>
                    <button class="example-btn">解释一下项目的整体架构</button>
                    <button class="example-btn">数据库连接是怎么配置的？</button>
                </div>
            </div>
        `;

        // 重新绑定示例按钮
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('messageInput').value = btn.textContent;
                sendMessage();
            });
        });
    }
}

// 滚动到底部
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 3600000) {
        return '刚刚';
    } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
    } else {
        return `${date.getMonth() + 1}/${date.getDate()}`;
    }
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}