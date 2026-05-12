/* ══════════════════════════════════════
   THREAD — AI Thrift Advisor
   Frontend Logic
══════════════════════════════════════ */

const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearChat');
const themeToggle = document.getElementById('themeToggle');
const quickTags = document.querySelectorAll('.qtag');

let conversationHistory = [];
let isLoading = false;

// ── Theme Toggle ──
const savedTheme = localStorage.getItem('thread-theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('thread-theme', next);
});

// ── Auto-resize textarea ──
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
});

// ── Send on Enter (Shift+Enter for newline) ──
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener('click', handleSend);

// ── Quick tags ──
quickTags.forEach(tag => {
  tag.addEventListener('click', () => {
    const prompt = tag.getAttribute('data-prompt');
    userInput.value = prompt;
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    handleSend();
  });
});

// ── Clear chat ──
clearBtn.addEventListener('click', () => {
  conversationHistory = [];
  chatMessages.innerHTML = '';
  appendIntroMessage();
});

// ── Core: handle send ──
async function handleSend() {
  const text = userInput.value.trim();
  if (!text || isLoading) return;

  appendUserMessage(text);
  userInput.value = '';
  userInput.style.height = 'auto';

  conversationHistory.push({ role: 'user', content: text });

  const typingId = appendTypingIndicator();
  setLoading(true);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: conversationHistory }),
    });

    const data = await res.json();
    removeTypingIndicator(typingId);

    const reply = data.reply || data.error || 'Something went wrong.';

    appendAIMessage(reply, data.products || []);

    conversationHistory.push({
      role: 'assistant',
      content: reply
    });

  } catch (err) {
    removeTypingIndicator(typingId);
    appendAIMessage('Connection error. Please check your server and try again.');
  } finally {
    setLoading(false);
  }
}

// ── Append user message ──
function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'message user-message';
  div.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">
      <div class="message-bubble">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
}

// ── Append AI message ──
function appendAIMessage(text, products = []) {

  const div = document.createElement('div');
  div.className = 'message ai-message';

  const rendered = renderStructuredResponse(text);

  let productsHTML = '';

  if (products.length > 0) {

    productsHTML = `
      <div class="product-carousel">
        ${products.map(product => `
          
          <a 
            class="product-card"
            href="${product.link}"
            target="_blank"
          >
            
            <img 
              src="${product.thumbnail}" 
              alt="${product.title}"
              loadings="lazy"
            >

            <div class="product-info">

              <h4>${product.title}</h4>

              <p class="product-price">
                ${product.price}
              </p>

              <span class="product-source">
                ${product.source}
              </span>

            </div>

          </a>

        `).join('')}
      </div>
    `;
  }

  div.innerHTML = `
    <div class="message-avatar">T</div>

    <div class="message-content">

      <div class="message-bubble">

        ${rendered}

        ${productsHTML}

      </div>

    </div>
  `;

  chatMessages.appendChild(div);

  scrollToBottom();
}

// ── Append intro ──
function appendIntroMessage() {
  const div = document.createElement('div');
  div.className = 'message ai-message intro-message';
  div.innerHTML = `
    <div class="message-avatar">T</div>
    <div class="message-content">
      <div class="message-bubble">
        <p class="intro-greeting">Namaste. I'm <strong>THREAD</strong> — your personal Indian thrift advisor.</p>
        <p>Tell me your <strong>budget</strong>, <strong>style</strong>, and <strong>occasion</strong>. I'll point you to the right platforms, build an outfit, and keep it sustainable.</p>
        <p class="intro-hint">Try: <em>"₹800 budget, need something aesthetic for a date"</em></p>
      </div>
    </div>
  `;
  chatMessages.appendChild(div);
}

// ── Typing indicator ──
function appendTypingIndicator() {
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.className = 'message ai-message';
  div.id = id;
  div.innerHTML = `
    <div class="message-avatar">T</div>
    <div class="message-content">
      <div class="message-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Render structured response ──
function renderStructuredResponse(text) {
  // Section patterns
  const sections = [
    { icon: '🔍', label: 'Understanding', key: '🔍 **Understanding**' },
    { icon: '🛍️', label: 'Recommendations', key: '🛍️ **Recommendations**' },
    { icon: '🧥', label: 'Outfit Idea', key: '🧥 **Outfit Idea**' },
    { icon: '🌱', label: 'Sustainability Insight', key: '🌱 **Sustainability Insight**' },
  ];

  let hasStructure = sections.some(s => text.includes(s.key));

  if (!hasStructure) {
    // Plain text — still format basic markdown
    return formatMarkdown(text);
  }

  // Parse structured sections
  let result = '';
  let remaining = text;

  for (let i = 0; i < sections.length; i++) {
    const current = sections[i];
    const next = sections[i + 1];

    const startIdx = remaining.indexOf(current.key);
    if (startIdx === -1) continue;

    // Text before first section
    if (i === 0 && startIdx > 0) {
      const before = remaining.slice(0, startIdx).trim();
      if (before) result += `<p>${formatMarkdown(before)}</p>`;
    }

    const contentStart = startIdx + current.key.length;
    const endIdx = next ? remaining.indexOf(next.key, contentStart) : remaining.length;
    const content = remaining.slice(contentStart, endIdx !== -1 ? endIdx : undefined).trim();

    result += `
      <div class="ai-section">
        <div class="ai-section-title">${current.icon} ${current.label}</div>
        <div class="ai-section-body">${formatMarkdown(content)}</div>
      </div>
    `;
  }

  return result || formatMarkdown(text);
}

// ── Format markdown-like syntax ──
function formatMarkdown(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
}

// ── Escape HTML ──
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br>');
}

// ── Scroll to bottom ──
function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

// ── Set loading state ──
function setLoading(state) {
  isLoading = state;
  sendBtn.disabled = state;
  userInput.disabled = state;
}
