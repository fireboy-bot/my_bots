import './CoinIcon.css';

export function CoinIcon({ size = 20, className = '' }) {
  return (
    <svg
      className={`coin-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      role="img"
      aria-label="монеты"
    >
      <circle cx="12" cy="12" r="10" fill="#fbbf24" stroke="#d97706" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="7" fill="none" stroke="#f59e0b" strokeWidth="1" opacity="0.55" />
      <text x="12" y="16" textAnchor="middle" fontSize="10" fontWeight="700" fill="#92400e">
        G
      </text>
    </svg>
  );
}

export function CoinsLabel({ amount, className = '' }) {
  const text = typeof amount === 'number' ? amount.toLocaleString('ru-RU') : amount;
  return (
    <span className={`coins-label ${className}`.trim()}>
      <CoinIcon size={16} />
      <span>{text}</span>
    </span>
  );
}
