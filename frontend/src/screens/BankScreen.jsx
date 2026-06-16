import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FloatingNav } from '../components/FloatingNav';
import { botApi } from '../adapters/botAdapter';
import './BankScreen.css';

export function BankScreen({ userId = "331113480", onBack }) {
  const navigate = useNavigate();
  
  // 🔹 Состояния
  const [bankInfo, setBankInfo] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);
  const [vladimirPhrase, setVladimirPhrase] = useState('');

  // 🔹 Загрузка данных
  useEffect(() => {
    const loadData = async () => {
      try {
        const [bank, profile] = await Promise.all([
          botApi.getBankInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        
        setBankInfo(bank);
        setPlayerStats(profile);

        if (bank?.error || profile?.error) {
          setMessage({ type: 'error', text: bank?.error || profile?.error || '⚠️ Игрок не найден' });
        }
        
        // 🔹 Фраза Владимира
        setVladimirPhrase(getVladimirPhrase(bank, profile));
        
      } catch (error) {
        console.error('❌ Error loading bank data:', error);
        setMessage({ type: 'error', text: '⚠️ Ошибка загрузки данных' });
      } finally {
        setLoading(false);
      }
    };
    
    if (userId) {
      loadData();
    }
  }, [userId]);

  // 🔹 Фразы Владимира (синхронизируй с phrase_manager в боте!)
  const getVladimirPhrase = (bank, profile) => {
    const castleUnlocked = profile?.defeated_bosses?.includes('final_boss') || profile?.completed_normal_game;
    
    if (!castleUnlocked) {
      return "🎩 «Златочёт надёжно хранит Ваши сокровища, сударыня. Но истинная мудрость — в балансе риска и покоя.»";
    }
    
    if (bank?.bank_balance > 0) {
      return "🎩 «Ваши золотые приносят плоды, сударыня. Терпение — добродетель инвестора.»";
    }
    
    return "🎩 «Пустой вклад — как пустая чашка чая. Наполните её, и она согреет Вас процентами.»";
  };

  // 🔹 Депозит
  const handleDeposit = async (amount) => {
    if (processing) return;
    
    const depositAmount = amount === 'custom' ? parseInt(customAmount) : amount;
    
    if (!depositAmount || depositAmount < 100) {
      setMessage({ type: 'error', text: '❌ Минимальный вклад: 100 золотых' });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    if ((playerStats?.score_balance || 0) < depositAmount) {
      setMessage({ type: 'error', text: `❌ Недостаточно золота! Нужно ${depositAmount.toLocaleString()}, есть ${(playerStats?.score_balance || 0).toLocaleString()}` });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    setProcessing(true);
    setMessage(null);
    
    try {
      const result = await botApi.depositToBank(userId, depositAmount);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        // Обновляем данные
        const [bank, profile] = await Promise.all([
          botApi.getBankInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        setBankInfo(bank);
        setPlayerStats(profile);
        setVladimirPhrase(getVladimirPhrase(bank, profile));
        setCustomAmount('');
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (error) {
      console.error('❌ Error depositing:', error);
      setMessage({ type: 'error', text: '⚠️ Ошибка соединения' });
    }
    
    setProcessing(false);
    setTimeout(() => setMessage(null), 4000);
  };

  // 🔹 Снятие
  const handleWithdraw = async () => {
    if (processing) return;
    
    if ((bankInfo?.bank_balance || 0) <= 0) {
      setMessage({ type: 'error', text: '❌ У вас нет вклада в Златочёте' });
      setTimeout(() => setMessage(null), 3000);
      return;
    }
    
    setProcessing(true);
    setMessage(null);
    
    try {
      const result = await botApi.withdrawFromBank(userId);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        // Обновляем данные
        const [bank, profile] = await Promise.all([
          botApi.getBankInfo(userId),
          botApi.getPlayerProfile(userId)
        ]);
        setBankInfo(bank);
        setPlayerStats(profile);
        setVladimirPhrase(getVladimirPhrase(bank, profile));
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (error) {
      console.error('❌ Error withdrawing:', error);
      setMessage({ type: 'error', text: '⚠️ Ошибка соединения' });
    }
    
    setProcessing(false);
    setTimeout(() => setMessage(null), 4000);
  };

  // 🔹 Навигация
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/game/menu/' + userId);
    }
  };

  // 🔹 Форматирование чисел
  const formatNumber = (num) => {
    return (num || 0).toLocaleString('ru-RU');
  };

  // 🔹 Скелетон загрузки
  if (loading) {
    return (
      <div className="bank-screen">
        <div className="bank-screen__loading">
          <div className="loading-spinner">🏦</div>
          <p>Загрузка Златочёта...</p>
        </div>
        <FloatingNav 
          userId={userId}
          showBack={true}
          showMenu={true}
          showSettings={false}
          onBack={handleBack}
          theme="game"
        />
      </div>
    );
  }

  // 🔹 Рассчитываем суммы
  const balanceOnHand = playerStats?.score_balance || 0;
  const bankBalance = bankInfo?.bank_balance || 0;
  const interestEarned = bankInfo?.interest_earned || 0;
  const interestRate = bankInfo?.bank_interest || 0.10;
  const daysPassed = bankInfo?.days_passed || 0;
  const totalWithdrawable = bankBalance + interestEarned;

  return (
    <div className="bank-screen">
      
      {/* 🔹 HEADER */}
      <div className="bank-screen__header">
        <button className="back-btn" onClick={handleBack}>← Назад</button>
        <h1>🏦 ЗЛАТОЧЁТ</h1>
      </div>

      {/* 🔹 ВЛАДИМИР — СООБЩЕНИЕ */}
      <div className="vladimir-message">
        <div className="vladimir-avatar">🎩</div>
        <p dangerouslySetInnerHTML={{ __html: vladimirPhrase }} />
      </div>

      {/* 🔹 БАЛАНСЫ */}
      <div className="balances-grid">
        <div className="balance-card balance-card--hand">
          <div className="balance-icon">💰</div>
          <div className="balance-info">
            <span className="balance-label">На руках</span>
            <span className="balance-value">{formatNumber(balanceOnHand)} 🪙</span>
          </div>
        </div>
        
        <div className="balance-card balance-card--bank">
          <div className="balance-icon">🏦</div>
          <div className="balance-info">
            <span className="balance-label">В банке</span>
            <span className="balance-value">{formatNumber(bankBalance)} 🪙</span>
          </div>
        </div>
      </div>

      {/* 🔹 ПРОЦЕНТЫ */}
      <div className="interest-card">
        <h3>📈 Проценты</h3>
        <div className="interest-row">
          <span>Ставка:</span>
          <strong>{Math.round(interestRate * 100)}% в день</strong>
        </div>
        <div className="interest-row">
          <span>Дней в банке:</span>
          <strong>{daysPassed}</strong>
        </div>
        <div className="interest-row">
          <span>Накоплено:</span>
          <strong className="interest-value">+{formatNumber(interestEarned)} 🪙</strong>
        </div>
        <div className="interest-total">
          <span>Можно забрать:</span>
          <strong>{formatNumber(totalWithdrawable)} 🪙</strong>
        </div>
      </div>

      {/* 🔹 ВКЛАД */}
      <div className="deposit-section">
        <h3>💰 Положить в банк</h3>
        <p className="section-desc">Минимальный вклад: 100 золотых</p>
        
        <div className="quick-deposits">
          {[100, 500, 1000].map(amount => (
            <button
              key={amount}
              className="deposit-btn"
              onClick={() => handleDeposit(amount)}
              disabled={processing || balanceOnHand < amount}
            >
              +{amount.toLocaleString()} 🪙
            </button>
          ))}
        </div>
        
        <div className="custom-deposit">
          <input
            type="number"
            className="custom-amount-input"
            placeholder="Другая сумма"
            value={customAmount}
            onChange={(e) => setCustomAmount(e.target.value)}
            min="100"
            disabled={processing}
          />
          <button
            className="deposit-btn deposit-btn--custom"
            onClick={() => handleDeposit('custom')}
            disabled={processing || !customAmount || parseInt(customAmount) < 100 || balanceOnHand < parseInt(customAmount)}
          >
            💰 Вложить
          </button>
        </div>
      </div>

      {/* 🔹 СНЯТИЕ */}
      <div className="withdraw-section">
        <h3>💸 Забрать вклад</h3>
        <p className="section-desc">
          Забрать весь вклад с накопленными процентами
        </p>
        
        <button
          className="withdraw-btn"
          onClick={handleWithdraw}
          disabled={processing || bankBalance <= 0}
        >
          {processing ? '⏳ Обработка...' : `💸 Забрать ${formatNumber(totalWithdrawable)} 🪙`}
        </button>
        
        {bankBalance <= 0 && (
          <p className="withdraw-hint">❌ Нет вклада для снятия</p>
        )}
      </div>

      {/* 🔹 СООБЩЕНИЯ */}
      {message && (
        <div className={`message message--${message.type}`} dangerouslySetInnerHTML={{ __html: message.text }} />
      )}

      {/* 🔹 ПОДСКАЗКА */}
      <div className="bank-tip">
        💡 <i>«Златочёт начисляет проценты каждый день. Чем дольше вклад — тем больше доход!»</i>
      </div>

      {/* 🔹 FLOATING NAV */}
      <FloatingNav 
        userId={userId}
        showBack={true}
        showMenu={true}
        showSettings={false}
        onBack={handleBack}
        theme="game"
      />
      
    </div>
  );
}