/**
 * 🔹 WebAdapter: React Frontend ↔ Flask API ↔ ChislyandiaEngine
 * 
 * Автоматический fallback на мок-данные если API недоступен.
 * Единый интерфейс для всех экранов.
 * 
 * Контракт: api_server.py (Flask)
 * • Порт: 5000
 * • Эндпоинты: /api/game/answer, /api/game/task, etc.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

let useMockData = false;

// 🔹 Мок-данные (структура ОТВЕТА ЯДРА)
const MOCK = {
  profile: {
    user_id: "331113480",
    level: 3,
    xp: 150,
    total_score: 1250,
    score_balance: 850,
    tasks_solved: 42,
    tasks_correct: 38,
    unlocked_zones: ["addition", "measure"],
    inventory: ["potion_luck", "ring_power"],
    artifact_upgrades: { "crown_mathmage": 2 },
    chaos_energy: 20,
    rift_stage: 1,
    artifact_chaos_state: 'awakened',
    consecutive_errors: 0
  },
  
  tasks: [
    { id: "t_add_001", world: "addition", question: "Сколько будет 5 + 3?", options: ["6", "7", "8", "9"], correct_answer: "8", score: 10, type: "math", island: "addition", operation_type: "2digit_add" },
    { id: "t_meas_001", world: "measure", question: "Сколько см в 1 метре?", options: ["10", "100", "1000", "10000"], correct_answer: "100", score: 15, type: "measure", island: "measure", operation_type: "unit_convert" },
    { id: "t_mult_001", world: "multiply", question: "Сколько будет 7 × 6?", options: ["36", "42", "48", "54"], correct_answer: "42", score: 20, type: "math", island: "multiplication", operation_type: "1digit_mult" }
  ],
  
  bank: { balance: 850, bank_balance: 500, interest_earned: 25, bank_interest: 0.10, days_passed: 3 },
  castle: { decorations: [], upkeep_paid_until: null, level: 1 },
  artifacts: { "crown_mathmage": { level: 2, bonus: "+5% к очкам" } }
};

// 🔹 Вспомогательная функция для запросов
async function apiFetch(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
    }
    return await response.json();
  } catch (error) {
    console.warn(`🔹 API error (${endpoint}): ${error.message}. Using mock data.`);
    useMockData = true;
    return null;
  }
}

// 🔹 Хелпер: безопасное преобразование в строку
function safeStr(val) {
  return val !== undefined && val !== null ? String(val).trim().replace(',', '.') : '';
}

export const botApi = {
  
  async isApiAvailable() {
    try {
      const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
      return res.ok;
    } catch {
      return false;
    }
  },
  
  async getPlayerProfile(userId) {
    if (useMockData) return { ...MOCK.profile, user_id: String(userId) };
    const data = await apiFetch(`/api/player/${userId}/profile`);
    return data || { ...MOCK.profile, user_id: String(userId) };
  },
  
  async getTask(userId, world = null) {
    if (useMockData) {
      const tasks = world ? MOCK.tasks.filter(t => t.world === world || t.island === world) : MOCK.tasks;
      return tasks[Math.floor(Math.random() * tasks.length)];
    }
    
    const url = new URL(`/api/game/task`, API_BASE);
    url.searchParams.set('user_id', String(userId));
    if (world) url.searchParams.set('world', world);
    
    const data = await apiFetch(url.pathname + url.search);
    return data || MOCK.tasks[0];
  },
  
  // 🔹 ПРОВЕРКА ОТВЕТА — ПРИНИМАЕТ ОДИН ОБЪЕКТ (как в TaskScreen.jsx)
  async checkAnswer(data) {
    // 🔹 Деструктуризация с дефолтами
    const {
      user_id,
      task_id,
      answer,
      expected_answer,
      island_id = 'addition',
      operation_type = 'unknown',
      is_transfer = false,
      currentBalance = 100
    } = data || {};
    
    // 🔹 Подготовка безопасных значений
    const payload = {
      user_id: String(user_id || 'unknown'),
      task_id: String(task_id || 'mock'),
      answer: safeStr(answer),
      expected_answer: safeStr(expected_answer),
      island_id,
      operation_type,
      is_transfer: !!is_transfer
    };
    
    if (useMockData) {
      // 🔹 Мок возвращает ПОЛНУЮ структуру как ядро
      const isCorrect = payload.answer && payload.expected_answer && payload.answer === payload.expected_answer;
      const baseScore = 10;
      const reward = isCorrect ? baseScore : -5;
      const newBalance = Math.max(0, currentBalance + reward);
      
      // 🔹 Простая логика хаоса для мока
      const consecutive_errors = isCorrect ? 0 : 1;
      const chaos_energy = Math.max(0, Math.min(100, 20 + (isCorrect ? -10 : 15)));
      const rift_stage = chaos_energy >= 90 ? 3 : chaos_energy >= 75 ? 2 : chaos_energy >= 30 ? 1 : 0;
      const artifact_state = chaos_energy >= 90 ? 'overload' : chaos_energy >= 75 ? 'active' : chaos_energy >= 20 ? 'awakened' : 'dormant';
      
      return {
        correct: isCorrect,
        reward: reward,
        message: isCorrect ? '✅ Правильно! +10 🪙' : '❌ Ошибка! -5 🪙',
        level_up: false,
        chaos_state: {
          rift_stage,
          chaos_energy,
          artifact_state,
          consecutive_errors
        },
        transfer_task: null,
        next_task: true,
        new_balance: newBalance,
        new_total_score: 1250 + reward
      };
    }
    
    // 🔹 Реальный запрос к Flask (используем алиас /api/game/answer)
    const result = await apiFetch('/api/game/answer', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    
    // 🔹 Если ответ пришёл — возвращаем как есть
    if (result) return result;
    
    // 🔹 Фоллбэк при сетевой ошибке
    return {
      correct: false,
      reward: 0,
      message: '⚠️ Ошибка сети',
      chaos_state: { rift_stage: 0, chaos_energy: 0, artifact_state: 'dormant', consecutive_errors: 0 },
      transfer_task: null,
      next_task: true,
      new_balance: currentBalance,
      new_total_score: 0
    };
  },
  
  async getBankInfo(userId) {
    if (useMockData) return MOCK.bank;
    return await apiFetch(`/api/bank/${userId}`) || MOCK.bank;
  },
  
  async depositToBank(userId, amount) {
    if (useMockData) return { success: true, message: `✅ (mock) Положено ${amount} золотых` };
    return await apiFetch(`/api/bank/${userId}/deposit`, {
      method: 'POST',
      body: JSON.stringify({ user_id: String(userId), amount })
    }) || { success: true, message: '✅ (mock)' };
  },
  
  async withdrawFromBank(userId) {
    if (useMockData) return { success: true, message: '✅ (mock) Забрано 100 очков', total: 100 };
    return await apiFetch(`/api/bank/${userId}/withdraw`, { 
      method: 'POST',
      body: JSON.stringify({ user_id: String(userId) })
    }) || { success: true, message: '✅ (mock)', total: 0 };
  },
  
  async getCastleInfo(userId) {
    if (useMockData) return MOCK.castle;
    return await apiFetch(`/api/castle/${userId}`) || MOCK.castle;
  },
  
  async payCastleUpkeep(userId, days = 1) {
    if (useMockData) return { success: true, message: `✅ (mock) Оплачено ${days} дней` };
    return await apiFetch(`/api/castle/${userId}/upkeep`, {
      method: 'POST',
      body: JSON.stringify({ user_id: String(userId), days })
    }) || { success: true, message: '✅ (mock)' };
  },
  
  async getArtifacts(userId) {
    if (useMockData) return MOCK.artifacts;
    return await apiFetch(`/api/artifacts/${userId}`) || MOCK.artifacts;
  },
  
  async upgradeArtifact(userId, artifactId) {
    if (useMockData) return { success: true, message: `✅ (mock) Артефакт ${artifactId} улучшен` };
    return await apiFetch(`/api/artifacts/${userId}/upgrade`, {
      method: 'POST',
      body: JSON.stringify({ user_id: String(userId), artifact_id: artifactId })
    }) || { success: true, message: '✅ (mock)' };
  },
  
  resetMockFlag() {
    useMockData = false;
    console.log('🔹 Mock flag reset');
  }
};