document.addEventListener('DOMContentLoaded', () => {
    // ===== DOM Elements =====
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const fileUpload = document.getElementById('file-upload');
    const filePreview = document.getElementById('file-preview-container');
    const chatHistory = document.getElementById('chat-history');
    const sendBtn = document.getElementById('send-btn');
    const traceContainer = document.getElementById('plan-trace-container');
    const extractedContainer = document.getElementById('extracted-text-container');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const welcomeScreen = document.getElementById('welcome-screen');
    const editBanner = document.getElementById('edit-banner');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const rightSidebar = document.getElementById('right-sidebar');
    const convList = document.getElementById('conversation-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const leftSidebar = document.querySelector('.left-sidebar');

    let selectedFiles = [];
    let editingMessageEl = null;
    let currentConversationId = null;
    let currentAbortController = null;

    // ===== Configure marked =====
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });

    // ===== Initialize =====
    loadConversations();

    // ===== Sidebar Toggle =====
    toggleSidebarBtn.addEventListener('click', () => rightSidebar.classList.toggle('hidden'));
    closeSidebarBtn.addEventListener('click', () => rightSidebar.classList.add('hidden'));

    // ===== Mobile Menu Toggle =====
    mobileMenuBtn.addEventListener('click', () => {
        leftSidebar.classList.toggle('mobile-open');
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 900 && 
            !leftSidebar.contains(e.target) && 
            !mobileMenuBtn.contains(e.target)) {
            leftSidebar.classList.remove('mobile-open');
        }
    });

    // ===== Tabs =====
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // ===== Textarea Auto-Resize =====
    queryInput.addEventListener('input', autoResize);
    function autoResize() {
        queryInput.style.height = 'auto';
        queryInput.style.height = Math.min(queryInput.scrollHeight, 200) + 'px';
    }

    // ===== Shift+Enter = new line, Enter = submit =====
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // ===== File Selection =====
    fileUpload.addEventListener('change', (e) => {
        selectedFiles = [...selectedFiles, ...Array.from(e.target.files)];
        renderFilePreview();
        fileUpload.value = '';
    });

    function renderFilePreview() {
        filePreview.innerHTML = '';
        selectedFiles.forEach((file, i) => {
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `${getFileIcon(file.name)} ${file.name} <span class="remove-file" data-i="${i}">×</span>`;
            chip.querySelector('.remove-file').addEventListener('click', () => {
                selectedFiles.splice(i, 1);
                renderFilePreview();
            });
            filePreview.appendChild(chip);
        });
    }

    function getFileIcon(name) {
        const ext = name.split('.').pop().toLowerCase();
        return { pdf:'📄', png:'🖼️', jpg:'🖼️', jpeg:'🖼️', mp3:'🎵', wav:'🎵', m4a:'🎵', py:'🐍', js:'📜', txt:'📝' }[ext] || '📎';
    }

    // ==========================================
    //  CONVERSATION MANAGEMENT
    // ==========================================

    async function loadConversations() {
        try {
            const res = await fetch('/api/conversations');
            const convs = await res.json();
            renderConversationList(convs);
        } catch (e) {
            console.error('Failed to load conversations:', e);
        }
    }

    function renderConversationList(convs) {
        convList.innerHTML = '';
        if (convs.length === 0) {
            convList.innerHTML = '<p class="conv-empty">No conversations yet</p>';
            return;
        }
        convs.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conv-item' + (conv.id === currentConversationId ? ' active' : '');
            item.dataset.id = conv.id;

            item.innerHTML = `
                <span class="conv-title">${escapeHtml(conv.title)}</span>
                <div class="conv-actions">
                    <button class="conv-action-btn rename-btn" title="Rename">✏️</button>
                    <button class="conv-action-btn delete-btn" title="Delete">🗑️</button>
                </div>
            `;

            // Click to load conversation
            item.addEventListener('click', (e) => {
                if (e.target.closest('.conv-action-btn')) return;
                loadConversation(conv.id);
                if (window.innerWidth <= 900) {
                    leftSidebar.classList.remove('mobile-open');
                }
            });

            // Rename
            item.querySelector('.rename-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                const newTitle = prompt('Rename conversation:', conv.title);
                if (newTitle && newTitle.trim()) {
                    renameConversation(conv.id, newTitle.trim());
                }
            });

            // Delete
            item.querySelector('.delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('Delete this conversation?')) {
                    deleteConversation(conv.id);
                }
            });

            convList.appendChild(item);
        });
    }

    async function loadConversation(convId) {
        currentConversationId = convId;

        // Clear chat area
        chatHistory.innerHTML = '';
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        traceContainer.innerHTML = '<p class="empty-state">Agent activity will appear here.</p>';
        extractedContainer.innerHTML = '<p class="empty-state">Extracted file contents will appear here.</p>';

        // Highlight active conversation in sidebar
        document.querySelectorAll('.conv-item').forEach(el => el.classList.remove('active'));
        const active = document.querySelector(`.conv-item[data-id="${convId}"]`);
        if (active) active.classList.add('active');

        // Load messages
        try {
            const res = await fetch(`/api/conversations/${convId}/messages`);
            const msgs = await res.json();
            msgs.forEach(msg => {
                addMessage(msg.content, msg.role === 'user' ? 'user' : 'assistant', false);
            });
        } catch (e) {
            console.error('Failed to load messages:', e);
        }
    }

    async function createNewConversation() {
        try {
            const res = await fetch('/api/conversations', { method: 'POST' });
            const conv = await res.json();
            currentConversationId = conv.id;

            // Reset UI
            chatHistory.innerHTML = '';
            if (welcomeScreen) {
                welcomeScreen.style.display = '';
                chatHistory.appendChild(welcomeScreen);
            }
            traceContainer.innerHTML = '<p class="empty-state">Agent activity will appear here.</p>';
            extractedContainer.innerHTML = '<p class="empty-state">Extracted file contents will appear here.</p>';

            await loadConversations();
            return conv.id;
        } catch (e) {
            console.error('Failed to create conversation:', e);
        }
    }

    async function deleteConversation(convId) {
        try {
            await fetch(`/api/conversations/${convId}`, { method: 'DELETE' });
            if (currentConversationId === convId) {
                currentConversationId = null;
                chatHistory.innerHTML = '';
                if (welcomeScreen) {
                    welcomeScreen.style.display = '';
                    chatHistory.appendChild(welcomeScreen);
                }
            }
            await loadConversations();
        } catch (e) {
            console.error('Failed to delete conversation:', e);
        }
    }

    async function renameConversation(convId, title) {
        try {
            const formData = new FormData();
            formData.append('title', title);
            await fetch(`/api/conversations/${convId}/rename`, { method: 'PUT', body: formData });
            await loadConversations();
        } catch (e) {
            console.error('Failed to rename conversation:', e);
        }
    }

    newChatBtn.addEventListener('click', () => createNewConversation());

    // ==========================================
    //  MESSAGES
    // ==========================================

    function addMessage(text, sender, scroll = true) {
        if (welcomeScreen) welcomeScreen.style.display = 'none';

        const row = document.createElement('div');
        row.className = `message-row ${sender}`;

        const header = document.createElement('div');
        header.className = 'msg-header';
        const avatar = document.createElement('div');
        avatar.className = `msg-avatar ${sender === 'user' ? 'user-avatar' : 'bot-avatar'}`;
        avatar.textContent = sender === 'user' ? '👤' : '✦';
        const senderName = document.createElement('span');
        senderName.className = 'msg-sender';
        senderName.textContent = sender === 'user' ? 'You' : 'Agentic AI';
        header.appendChild(avatar);
        header.appendChild(senderName);
        row.appendChild(header);

        const content = document.createElement('div');
        content.className = 'msg-content';
        if (sender === 'assistant') {
            content.innerHTML = renderMarkdown(text);
        } else {
            content.classList.add('user-text');
            content.textContent = text;
        }
        row.appendChild(content);

        // Actions
        const actions = document.createElement('div');
        actions.className = 'msg-actions';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.innerHTML = '✅ Copied!';
                copyBtn.classList.add('copied');
                setTimeout(() => { copyBtn.innerHTML = '📋 Copy'; copyBtn.classList.remove('copied'); }, 2000);
            });
        });
        actions.appendChild(copyBtn);

        if (sender === 'user') {
            const editBtn = document.createElement('button');
            editBtn.className = 'action-btn';
            editBtn.innerHTML = '✏️ Edit';
            editBtn.addEventListener('click', () => startEdit(row, text));
            actions.appendChild(editBtn);
        }

        row.appendChild(actions);
        chatHistory.appendChild(row);
        if (scroll) chatHistory.scrollTop = chatHistory.scrollHeight;
        return row;
    }

    function renderMarkdown(text) {
        let html = marked.parse(text);
        html = html.replace(/<pre><code(.*?)>([\s\S]*?)<\/code><\/pre>/g, (match, attrs, code) => {
            const id = 'code-' + Math.random().toString(36).substring(2, 9);
            return `<div class="code-block-wrapper">
                        <button class="code-copy-btn" onclick="copyCodeBlock('${id}')">Copy</button>
                        <pre><code${attrs} id="${id}">${code}</code></pre>
                    </div>`;
        });
        return html;
    }

    window.copyCodeBlock = (id) => {
        const el = document.getElementById(id);
        if (el) {
            navigator.clipboard.writeText(el.textContent).then(() => {
                const btn = el.closest('.code-block-wrapper').querySelector('.code-copy-btn');
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            });
        }
    };

    function startEdit(messageEl, originalText) {
        editingMessageEl = messageEl;
        queryInput.value = originalText;
        autoResize();
        editBanner.style.display = 'flex';
        queryInput.focus();
    }

    window.cancelEdit = () => {
        editingMessageEl = null;
        queryInput.value = '';
        autoResize();
        editBanner.style.display = 'none';
    };

    function showTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'message-row assistant';
        row.id = 'typing-indicator';
        const header = document.createElement('div');
        header.className = 'msg-header';
        const avatar = document.createElement('div');
        avatar.className = 'msg-avatar bot-avatar';
        avatar.textContent = '✦';
        const name = document.createElement('span');
        name.className = 'msg-sender';
        name.textContent = 'Agentic AI';
        header.appendChild(avatar);
        header.appendChild(name);
        row.appendChild(header);
        
        const typingContainer = document.createElement('div');
        typingContainer.style.display = 'flex';
        typingContainer.style.alignItems = 'center';
        typingContainer.style.gap = '16px';
        
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.innerHTML = '<span></span><span></span><span></span>';
        typingContainer.appendChild(typing);

        const stopBtn = document.createElement('button');
        stopBtn.className = 'action-btn';
        stopBtn.innerHTML = '⏹️ Stop Generating';
        stopBtn.style.color = 'var(--text-primary)';
        stopBtn.addEventListener('click', () => {
            if (currentAbortController) {
                currentAbortController.abort();
            }
        });
        typingContainer.appendChild(stopBtn);
        
        row.appendChild(typingContainer);
        chatHistory.appendChild(row);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function removeTypingIndicator() {
        const el = document.getElementById('typing-indicator');
        if (el) el.remove();
    }

    function renderTrace(traceArr) {
        if (!traceArr || traceArr.length === 0) return;
        traceContainer.innerHTML = '';
        traceArr.forEach(step => {
            const div = document.createElement('div');
            div.className = 'trace-step';
            div.innerHTML = `<div class="trace-label"><span class="status-dot ${step.status}"></span>${step.step}</div><div class="trace-details">${step.details || ''}</div>`;
            traceContainer.appendChild(div);
        });
        rightSidebar.classList.remove('hidden');
    }

    function renderExtracted(obj) {
        if (!obj || Object.keys(obj).length === 0) return;
        extractedContainer.innerHTML = '';
        for (const [name, text] of Object.entries(obj)) {
            if (!text) continue;
            const div = document.createElement('div');
            div.className = 'extracted-file';
            div.innerHTML = `<h4>${name}</h4><pre>${escapeHtml(text)}</pre>`;
            extractedContainer.appendChild(div);
        }
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    // ==========================================
    //  FORM SUBMIT
    // ==========================================

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query && selectedFiles.length === 0) return;

        // If no active conversation, create one first
        if (!currentConversationId) {
            await createNewConversation();
        }

        // If editing, remove old messages from the edited one
        if (editingMessageEl) {
            let sibling = editingMessageEl;
            while (sibling) {
                const next = sibling.nextElementSibling;
                sibling.remove();
                sibling = next;
            }
            editingMessageEl = null;
            editBanner.style.display = 'none';
        }

        addMessage(query || '(Uploaded files only)', 'user');

        const formData = new FormData();
        formData.append('query', query);
        formData.append('conversation_id', currentConversationId);
        selectedFiles.forEach(file => formData.append('files', file));

        // Reset
        queryInput.value = '';
        queryInput.style.height = 'auto';
        selectedFiles = [];
        renderFilePreview();
        sendBtn.disabled = true;
        traceContainer.innerHTML = '<p class="empty-state">Planning...</p>';
        showTypingIndicator();

        // Create AbortController for this request
        currentAbortController = new AbortController();

        try {
            const response = await fetch('/api/chat', { 
                method: 'POST', 
                body: formData,
                signal: currentAbortController.signal
            });
            const data = await response.json();
            removeTypingIndicator();

            if (!response.ok) {
                const err = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
                throw new Error(err || 'Server error');
            }

            if (data.follow_up_question) {
                addMessage(data.follow_up_question, 'assistant');
            } else if (data.answer) {
                addMessage(data.answer, 'assistant');
            } else {
                addMessage('I processed your request but received no output. Please try again.', 'assistant');
            }

            renderTrace(data.plan_trace);
            renderExtracted(data.extracted_texts);

            // Refresh sidebar to show updated title / order
            await loadConversations();
            
            // The AI title generator runs in the background for new chats.
            // Refresh the sidebar again after 3 seconds to grab the smart title.
            setTimeout(loadConversations, 3000);

        } catch (error) {
            removeTypingIndicator();
            if (error.name === 'AbortError') {
                addMessage('⚠️ Request stopped by user.', 'assistant');
            } else {
                addMessage(`⚠️ Error: ${error.message}`, 'assistant');
            }
        } finally {
            sendBtn.disabled = false;
            currentAbortController = null;
        }
    });
});
