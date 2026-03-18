const form = document.getElementById('chat-form');
const messageInput = document.getElementById('message');
const chat = document.getElementById('chat');
const contextBox = document.getElementById('context');

const history = [];

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage('user', message);
  history.push({ role: 'user', content: message });
  messageInput.value = '';

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: history.slice(0, -1) })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error desconocido');
    }

    addMessage('assistant', data.answer);
    history.push({ role: 'assistant', content: data.answer });
    contextBox.textContent = JSON.stringify(data.context, null, 2);
  } catch (error) {
    addMessage('assistant', `Error: ${error.message}`);
  }
});
