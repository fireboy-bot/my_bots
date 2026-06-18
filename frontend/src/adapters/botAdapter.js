/**
 * Адаптер для общения с Flask API
 * Все запросы к бэкенду — через этот файл
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

function parseApiErrorBody(data, status) {
  return data?.error || data?.message || `HTTP ${status}`;
}

async function apiFetch(endpoint, options = {}) {
  const { softError = false, ...fetchOptions } = options;
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const payload = {
        ok: false,
        error: parseApiErrorBody(data, response.status),
        status: response.status,
        ...data,
      };
      console.warn(`🔹 API error (${endpoint}): HTTP ${response.status}:`, data);
      if (softError) return payload;
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(data)}`);
    }

    if (data.error && data.ok === false) {
      return { ok: false, ...data };
    }

    return { ok: data.ok !== false, ...data };
  } catch (error) {
    console.warn(`🔹 API fetch error (${endpoint}):`, error.message);
    if (softError) {
      return { ok: false, error: error.message };
    }
    throw error;
  }
}

/** Нормализует ответ checkAnswer: battle.* + level_up */
export function normalizeAnswerResponse(data) {
  if (!data) return data;

  const battle = data.battle || {};
  return {
    ...data,
    level_up: data.level_up ?? Boolean(data.player_level_up),
    boss_health: data.boss_health ?? battle.boss_health,
    boss_max_health: data.boss_max_health ?? battle.boss_max_health,
    task_index: data.task_index ?? battle.task_index,
    total_tasks: data.total_tasks ?? battle.total_tasks,
    next_task: data.next_task ?? battle.next_task,
    retry_same_task: data.retry_same_task ?? battle.retry_same_task,
    boss_defeated: data.boss_defeated ?? battle.boss_defeated,
    boss_failed: data.boss_failed ?? battle.boss_failed,
    ability_triggered: data.ability_triggered ?? battle.ability_triggered,
    phase: data.phase ?? battle.phase,
    phase_name: data.phase_name ?? battle.phase_name,
    avatar_url: data.avatar_url ?? battle.avatar_url,
    phase_changed: data.phase_changed ?? battle.phase_changed,
    dialogues: data.dialogues ?? battle.dialogues,
    absolute_victory: data.absolute_victory ?? battle.absolute_victory,
    finale_text: data.finale_text ?? battle.finale_text,
    secret_text: data.secret_text ?? battle.secret_text,
    battle,
  };
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

export const botApi = {
  async getTask(userId, world = 'addition') {
    try {
      return await apiFetch(`/api/game/task?user_id=${encodeURIComponent(userId)}&world=${encodeURIComponent(world)}`);
    } catch (error) {
      console.warn('⚠️ Using mock task');
      const tasks = MOCK_TASKS[world] || MOCK_TASKS.addition;
      return tasks[Math.floor(Math.random() * tasks.length)];
    }
  },

  async checkAnswer(data) {
    const result = await apiFetch('/api/game/check_answer', {
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
    return normalizeAnswerResponse(result);
  },

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

  async getWorlds(userId) {
    return await apiFetch(`/api/game/worlds/${encodeURIComponent(userId)}`, { softError: true });
  },

  async getBosses(userId) {
    return await apiFetch(`/api/game/bosses/${encodeURIComponent(userId)}`, { softError: true });
  },

  async startLevel(userId, world) {
    return await apiFetch('/api/game/level/start', {
      method: 'POST',
      softError: true,
      body: JSON.stringify({ user_id: userId, world }),
    });
  },

  async startBoss(userId, bossId) {
    return await apiFetch('/api/game/boss/start', {
      method: 'POST',
      softError: true,
      body: JSON.stringify({ user_id: userId, boss_id: bossId }),
    });
  },

  async getBossState(userId) {
    return await apiFetch(`/api/game/boss/state/${encodeURIComponent(userId)}`, { softError: true });
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
      softError: true,
      body: JSON.stringify({ user_id: userId }),
    });
  },

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

  upgradeCastleDecoration(userId, decorationId) {
    return this.upgradeDecoration(userId, decorationId);
  },

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
