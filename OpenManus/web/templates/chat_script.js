    &lt;script&gt;
        let isDark = false;
        let currentFeature = 'chat';
        let websocket = null;
        let isWebSocketConnected = false;
        
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const themeToggle = document.getElementById('theme-toggle');
        const inputBox = document.getElementById('input-box');
        const sendBtn = document.getElementById('send-btn');
        const currentFeatureEl = document.getElementById('current-feature');
        const chatArea = document.getElementById('chat-area');
        
        // 初始化WebSocket
        function initWebSocket() {
            if (websocket) {
                websocket.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function() {
                console.log('WebSocket connected');
                isWebSocketConnected = true;
            };
            
            websocket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            websocket.onclose = function() {
                console.log('WebSocket disconnected');
                isWebSocketConnected = false;
                setTimeout(initWebSocket, 3000); // 3秒后重连
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        // 处理WebSocket消息
        function handleWebSocketMessage(data) {
            const chatArea = document.getElementById('chat-area');
            
            if (data.type === 'thinking') {
                const thinkingDiv = document.createElement('div');
                thinkingDiv.id = 'thinking';
                thinkingDiv.className = 'message assistant';
                thinkingDiv.innerHTML = `
                    &lt;div class="message-avatar"&gt;🤖&lt;/div&gt;
                    &lt;div class="message-content"&gt;
                        &lt;div class="message-text"&gt;${data.content || '思考中...'}&lt;/div&gt;
                    &lt;/div&gt;
                `;
                chatArea.appendChild(thinkingDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            } else if (data.type === 'stream_start') {
                const thinkingDiv = document.getElementById('thinking');
                if (thinkingDiv) thinkingDiv.remove();
                
                const msgDiv = document.createElement('div');
                msgDiv.id = 'streaming-message';
                msgDiv.className = 'message assistant';
                msgDiv.innerHTML = `
                    &lt;div class="message-avatar"&gt;🤖&lt;/div&gt;
                    &lt;div class="message-content"&gt;
                        &lt;div class="message-text"&gt;&lt;/div&gt;
                    &lt;/div&gt;
                `;
                chatArea.appendChild(msgDiv);
            } else if (data.type === 'stream_data') {
                const msgDiv = document.getElementById('streaming-message');
                if (msgDiv) {
                    const textDiv = msgDiv.querySelector('.message-text');
                    textDiv.textContent += data.content;
                    chatArea.scrollTop = chatArea.scrollHeight;
                }
            } else if (data.type === 'stream_end') {
                const msgDiv = document.getElementById('streaming-message');
                if (msgDiv) {
                    msgDiv.id = '';
                }
            } else if (data.type === 'response') {
                const thinkingDiv = document.getElementById('thinking');
                if (thinkingDiv) thinkingDiv.remove();
                
                addMessage('assistant', data.content);
            } else if (data.type === 'error') {
                const thinkingDiv = document.getElementById('thinking');
                if (thinkingDiv) thinkingDiv.remove();
                
                addMessage('assistant', '❌ ' + data.content);
            }
        }
        
        const featureNames = {
            chat: { icon: '💬', name: '智能对话' },
            image_gen: { icon: '🎨', name: 'AI 画图' },
            code: { icon: '💻', name: '代码助手' },
            document: { icon: '📄', name: '文档分析' },
            search: { icon: '🔍', name: '网页搜索' },
            pathology: { icon: '🔬', name: '病理分析' }
        };
        
        function selectFeature(feature) {
            currentFeature = feature;
            const f = featureNames[feature] || featureNames.chat;
            currentFeatureEl.innerHTML = `&lt;span&gt;${f.icon}&lt;/span&gt;&lt;span&gt;${f.name}&lt;/span&gt;`;
            
            document.querySelectorAll('.feature-item').forEach(item =&gt; {
                item.classList.toggle('active', item.dataset.feature === feature);
            });
            
            document.querySelectorAll('.feature-btn').forEach(btn =&gt; {
                btn.classList.toggle('active', btn.dataset.feature === feature);
            });
            
            const welcomeScreen = document.getElementById('welcome-screen');
            if (welcomeScreen) welcomeScreen.style.display = 'none';
            
            if (window.innerWidth &lt;= 768) closeSidebar();
        }
        
        function newChat() {
            location.reload();
        }
        
        function openSidebar() {
            sidebar.classList.add('show');
            sidebarOverlay.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
        
        function closeSidebar() {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
            document.body.style.overflow = '';
        }
        
        mobileMenuBtn.addEventListener('click', (e) =&gt; {
            e.stopPropagation();
            sidebar.classList.contains('show') ? closeSidebar() : openSidebar();
        });
        
        sidebarOverlay.addEventListener('click', closeSidebar);
        sidebar.addEventListener('click', (e) =&gt; e.stopPropagation());
        document.querySelector('.main-content').addEventListener('click', () =&gt; {
            if (sidebar.classList.contains('show')) closeSidebar();
        });
        
        document.querySelectorAll('.feature-item').forEach(item =&gt; {
            item.addEventListener('click', () =&gt; {
                if (item.dataset.feature) selectFeature(item.dataset.feature);
            });
        });
        
        themeToggle.addEventListener('click', () =&gt; {
            isDark = !isDark;
            document.body.classList.toggle('dark', isDark);
            themeToggle.textContent = isDark ? '☀️' : '🌙';
        });
        
        function addMessage(role, content) {
            const welcomeScreen = document.getElementById('welcome-screen');
            if (welcomeScreen) welcomeScreen.style.display = 'none';
            
            const msg = document.createElement('div');
            msg.className = `message ${role}`;
            msg.innerHTML = `
                &lt;div class="message-avatar ${role === 'user' ? 'user' : ''}"&gt;${role === 'user' ? '👤' : '🤖'}&lt;/div&gt;
                &lt;div class="message-content"&gt;
                    &lt;div class="message-text"&gt;${content}&lt;/div&gt;
                &lt;/div&gt;
            `;
            chatArea.appendChild(msg);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function sendMessage() {
            const text = inputBox.value.trim();
            if (!text) return;
            
            addMessage('user', text);
            inputBox.value = '';
            inputBox.style.height = 'auto';
            
            // 尝试用WebSocket发送
            if (isWebSocketConnected &amp;&amp; websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ content: text, feature: currentFeature }));
            } else {
                // 降级到HTTP请求
                fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: text, feature: currentFeature })
                }).then(res =&gt; res.json()).then(data =&gt; {
                    setTimeout(() =&gt; addMessage('assistant', data.response), 500);
                }).catch(() =&gt; {
                    setTimeout(() =&gt; {
                        addMessage('assistant', `已收到：${text}\n\n这是模拟回复，实际功能正在开发中...`);
                    }, 500);
                });
            }
        }
        
        sendBtn.addEventListener('click', sendMessage);
        inputBox.addEventListener('keydown', (e) =&gt; {
            if (e.key === 'Enter' &amp;&amp; !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        inputBox.addEventListener('input', () =&gt; {
            inputBox.style.height = 'auto';
            inputBox.style.height = Math.min(inputBox.scrollHeight, 200) + 'px';
        });
        
        function renameChat(chatId) {
            const chatItem = document.querySelector(`[data-chat="${chatId}"]`);
            const span = chatItem.querySelector('span:nth-child(2)');
            const newName = prompt('请输入新的对话名称:', span.textContent);
            if (newName &amp;&amp; newName.trim()) span.textContent = newName.trim();
        }
        
        function deleteChat(chatId) {
            if (confirm('确定要删除这个对话吗？')) {
                const chatItem = document.querySelector(`[data-chat="${chatId}"]`);
                if (chatItem) {
                    chatItem.style.opacity = '0';
                    chatItem.style.transition = 'opacity 0.3s';
                    setTimeout(() =&gt; chatItem.remove(), 300);
                }
            }
        }
        
        document.querySelectorAll('.chat-item').forEach(item =&gt; {
            item.addEventListener('click', (e) =&gt; {
                if (e.target.tagName === 'BUTTON') return;
                document.querySelectorAll('.chat-item').forEach(i =&gt; i.classList.remove('active'));
                item.classList.add('active');
                document.getElementById('welcome-screen').style.display = 'none';
            });
        });
        
        // 页面加载时初始化WebSocket
        window.addEventListener('load', initWebSocket);
    &lt;/script&gt;
