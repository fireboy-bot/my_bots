// Базовый URL твоего Flask API
// Для локальной разработки:
const API_BASE = 'http://localhost:5000/api';

// Когда задеплоишь на VPS + Vercel, замени на:
// const API_BASE = 'https://твой-vps-ip:5000/api';

export const api = {
  // Получить прогресс игрока
  getProgress: async (userId) => {
    const response = await fetch(`${API_BASE}/game/progress/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch progress');
    return response.json();
  },

  // Отправить ответ на задачу
  submitAnswer: async (userId, answer, taskId, expectedAnswer) => {
    const response = await fetch(`${API_BASE}/game/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: String(userId),
        answer: parseInt(answer),
        task_id: taskId,
        expected_answer: expectedAnswer
      })
    });
    if (!response.ok) throw new Error('Failed to submit answer');
    return response.json();
  },

  // Получить информацию о замке
  getCastle: async (userId) => {
    const response = await fetch(`${API_BASE}/castle/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch castle');
    return response.json();
  },

  // Оплатить замок
  payCastle: async (userId, days) => {
    const response = await fetch(`${API_BASE}/castle/pay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: String(userId), days })
    });
    if (!response.ok) throw new Error('Failed to pay castle');
    return response.json();
  },

  // Получить информацию о банке
  getBank: async (userId) => {
    const response = await fetch(`${API_BASE}/bank/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch bank');
    return response.json();
  },

  // Вклад в банк
  depositToBank: async (userId, amount) => {
    const response = await fetch(`${API_BASE}/bank/deposit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: String(userId), amount })
    });
    if (!response.ok) throw new Error('Failed to deposit');
    return response.json();
  },

  // Снятие из банка
  withdrawFromBank: async (userId) => {
    const response = await fetch(`${API_BASE}/bank/withdraw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: String(userId) })
    });
    if (!response.ok) throw new Error('Failed to withdraw');
    return response.json();
  },
};