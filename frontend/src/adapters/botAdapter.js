/**
 * Адаптер для общения с Flask API
 * Все запросы к бэкенду — через этот файл
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

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
    return await apiFetch('/api/game/check_answer', {
      method: 'POST',
      body: JSON.stringify({
        user_id: data.user_id?.toString(),
        answer: data.answer?.toString(),
        task_id: data.task_id?.toString(),
        expected_answer: data.expected_answer?.toString(),
        island_id: data.island_id,
        operation_type: data.operation_type,
        is_transfer: data.is_transfer || false,
      }),
    });
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

  // 🔹 Каталог миров / островов
  async getWorlds(userId) {
    return await apiFetch(`/api/game/worlds/${encodeURIComponent(userId)}`);
  },

  async getBosses(userId) {
    return await apiFetch(`/api/game/bosses/${encodeURIComponent(userId)}`);
  },

  // 🔹 Старт забега по острову (10 задач)
  async startLevel(userId, world) {
    return await apiFetch('/api/game/level/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, world }),
    });
  },

  async startBoss(userId, bossId) {
    return await apiFetch('/api/game/boss/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, boss_id: bossId }),
    });
  },

  async exitBoss(userId) {
    return await apiFetch('/api/game/boss/exit', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  async trueLordHint(userId) {
    return await apiFetch('/api/game/true-lord/hint', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
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
      return { success: false, message: '⚠️ API недоступен. Запусти web/api_server.py' };
    }
  },

  async withdrawFromBank(userId) {
    try {
      return await apiFetch(`/api/bank/${encodeURIComponent(userId)}/withdraw`, { method: 'POST' });
    } catch (error) {
      console.warn('⚠️ Using mock withdraw');
      return { success: false, message: '⚠️ API недоступен. Запусти web/api_server.py', total: 0 };
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
      return { success: false, message: '⚠️ API недоступен. Запусти web/api_server.py' };
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
      return { success: false, message: '⚠️ API недоступен. Запусти web/api_server.py' };
    }
  },

  /** @deprecated используй upgradeDecoration */
  upgradeCastleDecoration(userId, decorationId) {
    return this.upgradeDecoration(userId, decorationId);
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
      return { success: false, message: '⚠️ API недоступен. Запусти web/api_server.py' };
    }
  },

  async craftAlchemy(userId, itemId) {
    return await apiFetch(`/api/alchemy/${encodeURIComponent(userId)}/craft`, {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId }),
    });
  },

  async getInventory(userId) {
    try {
      return await apiFetch(`/api/inventory/${encodeURIComponent(userId)}`);
    } catch (error) {
      console.warn('⚠️ Using mock inventory');
      return { consumables: [], trophies: [], artifacts: [], secret_items: [], total_count: 0, is_empty: true };
    }
  },

  async getSecretRoom(userId) {
    try {
      return await apiFetch(`/api/secret_room/${encodeURIComponent(userId)}`);
    } catch (error) {
      console.warn('⚠️ Using mock secret room');
      return { unlocked: false, available: false, attempts_left: 0 };
    }
  },

  async exploreSecretRoom(userId) {
    return await apiFetch(`/api/secret_room/${encodeURIComponent(userId)}/explore`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },

  async answerSecretPuzzle(userId, puzzleId, optionIndex) {
    return await apiFetch(`/api/secret_room/${encodeURIComponent(userId)}/answer`, {
      method: 'POST',
      body: JSON.stringify({ puzzle_id: puzzleId, option_index: optionIndex }),
    });
  },
};