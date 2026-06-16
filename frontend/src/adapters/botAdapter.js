/**
 * Адаптер для общения с Flask API
 * Все запросы к бэкенду — через этот файл
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001';

// 🔹 Вспомогательная функция для запросов
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.warn(`🔹 API error (${endpoint}): HTTP ${response.status}:`, errorData);
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn(`🔹 API fetch error (${endpoint}):`, error.message);
    throw error;
  }
}

// 🔹 Mock-данные для оффлайн-режима
const MOCK_TASKS = {
  addition: [
    { id: 'mock_add_1', world: 'addition', question: '5 + 3 = ?', options: ['6', '7', '8', '9'], correct_answer: '8', score: 10, island: 'addition', operation_type: '2digit_add' },
    { id: 'mock_add_2', world: 'addition', question: '12 + 7 = ?', options: ['15', '18', '19', '21'], correct_answer: '19', score: 10, island: 'addition', operation_type: '2digit_add' },
  ],
  multiplication: [
    { id: 'mock_mult_1', world: 'multiplication', question: '7 × 6 = ?', options: ['36', '42', '48', '54'], correct_answer: '42', score: 15, island: 'multiplication', operation_type: '1digit_mult' },
  ],
  division: [
    { id: 'mock_div_1', world: 'division', question: '56 ÷ 8 = ?', options: ['6', '7', '8', '9'], correct_answer: '7', score: 15, island: 'division', operation_type: '2digit_div' },
  ],
};

const MOCK_ANSWERS = {
  success: {
    correct: true,
    reward: 10,
    message: '✅ Правильно! +10 очков',
    level_up: false,
    chaos_state: { rift_stage: 0, chaos_energy: 0, artifact_state: 'dormant', consecutive_errors: 0 },
    transfer_task: null,
    new_balance: 100,
    new_total_score: 100,
  },
  error: {
    correct: false,
    reward: -5,
    message: '❌ Ошибка! -5 очков',
    level_up: false,
    chaos_state: { rift_stage: 1, chaos_energy: 20, artifact_state: 'awakened', consecutive_errors: 1 },
    transfer_task: null,
    new_balance: 95,
    new_total_score: 95,
  },
};

export const botApi = {
  // 🔹 Получить задачу
  async getTask(userId, world = 'addition') {
    try {
      return await apiFetch(`/api/game/task?user_id=${encodeURIComponent(userId)}&world=${encodeURIComponent(world)}`);
    } catch (error) {
      console.warn('⚠️ Using mock task');
      const tasks = MOCK_TASKS[world] || MOCK_TASKS.addition;
      return tasks[Math.floor(Math.random() * tasks.length)];
    }
  },

  // 🔹 Проверить ответ — ИСПРАВЛЕНО: возвращаем объект, не строку!
  async checkAnswer(data) {
    try {
      return await apiFetch('/api/game/check_answer', {
        method: 'POST',
        body: JSON.stringify({
          user_id: data.user_id?.toString(),      // 🔹 Гарантируем строку
          answer: data.answer?.toString(),         // 🔹 Гарантируем строку
          task_id: data.task_id?.toString(),       // 🔹 Гарантируем строку
          expected_answer: data.expected_answer?.toString(), // 🔹 Гарантируем строку
          island_id: data.island_id,
          operation_type: data.operation_type,
          is_transfer: data.is_transfer || false,
        }),
      });
    } catch (error) {
      console.warn('⚠️ Using mock answer check');
      // 🔹 Возвращаем ОБЪЕКТ, не строку!
      return data.answer?.toString() === data.expected_answer?.toString()
        ? { ...MOCK_ANSWERS.success, new_balance: (data.currentBalance || 0) + 10 }
        : { ...MOCK_ANSWERS.error, new_balance: Math.max(0, (data.currentBalance || 100) - 5) };
    }
  },

  // 🔹 Профиль игрока
  async getPlayerProfile(userId) {
    try {
      return await apiFetch(`/api/player/${encodeURIComponent(userId)}/profile`);
    } catch (error) {
      console.warn('⚠️ Using mock profile');
      return {
        user_id: userId,
        level: 1,
        xp: 0,
        total_score: 100,
        score_balance: 100,
        tasks_solved: 0,
        tasks_correct: 0,
        inventory: [],
        artifact_upgrades: {},
        chaos_energy: 0,
        rift_stage: 0,
        artifact_chaos_state: 'dormant',
        consecutive_errors: 0,
      };
    }
  },

  // 🔹 Банк
  async getBankInfo(userId) {
    try {
      return await apiFetch(`/api/bank/${encodeURIComponent(userId)}`);
    } catch (error) {
      console.warn('⚠️ Using mock bank info');
      return { balance: 100, bank_balance: 0, interest_earned: 0, bank_interest: 0.1, days_passed: 0 };
    }
  },

  async depositToBank(userId, amount) {
    try {
      return await apiFetch(`/api/bank/${encodeURIComponent(userId)}/deposit`, {
        method: 'POST',
        body: JSON.stringify({ amount }),
      });
    } catch (error) {
      console.warn('⚠️ Using mock deposit');
      return { success: true, message: `✅ Mock: положено ${amount}` };
    }
  },

  async withdrawFromBank(userId) {
    try {
      return await apiFetch(`/api/bank/${encodeURIComponent(userId)}/withdraw`, { method: 'POST' });
    } catch (error) {
      console.warn('⚠️ Using mock withdraw');
      return { success: true, message: '✅ Mock: забрано 100', total: 100 };
    }
  },

  // 🔹 Замок
  async getCastleInfo(userId) {
    try {
      return await apiFetch(`/api/castle/${encodeURIComponent(userId)}`);
    } catch (error) {
      console.warn('⚠️ Using mock castle info');
      return { decorations: [], upkeep_paid_until: null, bonuses_active: false, decoration_upgrades: {} };
    }
  },

  async payCastleUpkeep(userId, days = 1) {
    try {
      return await apiFetch(`/api/castle/${encodeURIComponent(userId)}/upkeep`, {
        method: 'POST',
        body: JSON.stringify({ days }),
      });
    } catch (error) {
      console.warn('⚠️ Using mock upkeep');
      return { success: true, message: `✅ Mock: upkeep оплачен на ${days} дн.` };
    }
  },

  async upgradeDecoration(userId, decorationId) {
    try {
      return await apiFetch(`/api/castle/${encodeURIComponent(userId)}/upgrade_decoration`, {
        method: 'POST',
        body: JSON.stringify({ decoration_id: decorationId }),
      });
    } catch (error) {
      console.warn('⚠️ Using mock upgrade');
      return { success: true, message: '✅ Mock: декорация улучшена', new_level: 1, new_bonus: 0.02 };
    }
  },

  // 🔹 Артефакты
  async getArtifacts(userId) {
    try {
      return await apiFetch(`/api/artifacts/${encodeURIComponent(userId)}`);
    } catch (error) {
      console.warn('⚠️ Using mock artifacts');
      return { artifacts: [], upgrades: {} };
    }
  },

  async upgradeArtifact(userId, artifactId) {
    try {
      return await apiFetch(`/api/artifacts/${encodeURIComponent(userId)}/upgrade`, {
        method: 'POST',
        body: JSON.stringify({ artifact_id: artifactId }),
      });
    } catch (error) {
      console.warn('⚠️ Using mock upgrade');
      return { success: true, message: '✅ Mock: артефакт улучшен' };
    }
  },
};