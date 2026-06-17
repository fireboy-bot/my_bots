import { Component } from 'react';

export class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          background: 'linear-gradient(135deg, #1e1b4b, #312e81)',
          color: '#f8fafc',
          fontFamily: 'system-ui, sans-serif',
        }}>
          <div style={{ maxWidth: 480, textAlign: 'center' }}>
            <h1 style={{ marginBottom: 12 }}>⚠️ Ошибка загрузки</h1>
            <p style={{ marginBottom: 16, opacity: 0.9 }}>
              Попробуй Ctrl+Shift+R. Если не поможет — скинь текст ниже:
            </p>
            <pre style={{
              textAlign: 'left',
              background: 'rgba(0,0,0,0.35)',
              padding: 12,
              borderRadius: 8,
              fontSize: 12,
              overflow: 'auto',
            }}>
              {String(this.state.error?.message || this.state.error)}
            </pre>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
