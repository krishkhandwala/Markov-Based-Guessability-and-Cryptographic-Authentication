import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldAlert, Cpu, Lock, KeyRound, Terminal, 
  Activity, Database, Sparkles, RefreshCw, CheckCircle2, 
  AlertTriangle, XCircle, Info, ChevronRight, Zap, Eye, EyeOff, Radio
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('evaluator'); // 'evaluator' | 'auth' | 'telemetry' | 'architecture'
  
  // Real-time Evaluator State
  const [candidatePassword, setCandidatePassword] = useState('P@ssw0rd123');
  const [candidateUsername, setCandidateUsername] = useState('crypto_admin');
  const [evalResult, setEvalResult] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Authentication State
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [authResponse, setAuthResponse] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);

  // System Telemetry State
  const [telemetry, setTelemetry] = useState(null);
  const [telemetryLoading, setTelemetryLoading] = useState(false);

  // Real-time guessability analysis with debounce
  useEffect(() => {
    if (!candidatePassword) {
      setEvalResult(null);
      return;
    }
    const timer = setTimeout(() => {
      fetchEvaluation(candidatePassword, candidateUsername);
    }, 180);
    return () => clearTimeout(timer);
  }, [candidatePassword, candidateUsername]);

  // Periodic Telemetry polling
  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 6000);
    return () => clearInterval(interval);
  }, []);

  const fetchEvaluation = async (pwd, usr) => {
    setEvalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd, username: usr })
      });
      if (res.ok) {
        const data = await res.json();
        setEvalResult(data);
      }
    } catch (err) {
      console.error('Score request failed:', err);
    } finally {
      setEvalLoading(false);
    }
  };

  const fetchTelemetry = async () => {
    setTelemetryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/telemetry`);
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error('Telemetry fetch failed:', err);
    } finally {
      setTelemetryLoading(false);
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    if (!authUsername || !authPassword) return;

    setAuthLoading(true);
    setAuthResponse(null);
    const endpoint = authMode === 'register' ? '/register' : '/login';

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername, password: authPassword })
      });

      const data = await res.json();
      if (res.ok) {
        setAuthResponse({ success: true, data });
        if (authMode === 'register') {
          confetti({
            particleCount: 80,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#e2b253', '#00f2a1', '#00e5ff']
          });
        }
        fetchTelemetry();
      } else {
        const detailMsg = Array.isArray(data.detail) ? data.detail : [data.detail || 'Authentication failed'];
        setAuthResponse({ success: false, errors: detailMsg });
      }
    } catch (err) {
      setAuthResponse({ success: false, errors: ['Network unreachable or server offline.'] });
    } finally {
      setAuthLoading(false);
    }
  };

  const getTierBadge = (tier) => {
    switch (tier) {
      case 'STRONG':
        return { color: 'var(--accent-emerald)', bg: 'rgba(0, 242, 161, 0.12)', label: 'STRONG (10¹² - ∞ Guesses)' };
      case 'ACCEPT':
        return { color: 'var(--accent-gold)', bg: 'rgba(226, 178, 83, 0.12)', label: 'ACCEPTABLE (10⁸ - 10¹² Guesses)' };
      case 'WEAK':
        return { color: 'var(--accent-amber)', bg: 'rgba(255, 153, 0, 0.12)', label: 'WEAK (10⁶ - 10⁸ Guesses)' };
      default:
        return { color: 'var(--accent-crimson)', bg: 'rgba(255, 51, 102, 0.12)', label: 'REJECT (< 10⁶ Guesses)' };
    }
  };

  const samplePresets = [
    { label: 'Common Breached', pwd: 'password', desc: 'Top rockyou blocklist candidate' },
    { label: 'Sequential Run', pwd: 'Admin123456!', desc: 'Sequential numbers & simple run' },
    { label: 'Subtle Leaked', pwd: 'superman2026', desc: 'Predictable word + year pattern' },
    { label: 'Diceware Passphrase', pwd: 'correct-horse-battery-staple-77', desc: 'Long multi-token low n-gram rank' },
    { label: 'High-Entropy Cryptographic', pwd: 'zK9#mQ2$vL90!wPq', desc: 'Complex character set distribution' },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* ================= REFINED TOP NAVIGATION BAR ================= */}
      <header style={{
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(7, 9, 14, 0.88)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '14px 40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.4)'
      }}>
        
        {/* Brand / Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(226, 178, 83, 0.18) 0%, rgba(0, 242, 161, 0.12) 100%)',
            border: '1px solid rgba(226, 178, 83, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 24px rgba(226, 178, 83, 0.25)',
            flexShrink: 0
          }}>
            <ShieldCheck size={24} color="var(--accent-gold)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <h1 style={{ 
                fontFamily: 'var(--font-display)', 
                fontSize: '18px', 
                fontWeight: 800, 
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                background: 'linear-gradient(90deg, #ffffff 0%, #e2b253 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                AETHER // CRYPTOGRAPHIC GUESSABILITY
              </h1>
              <span style={{
                background: 'rgba(0, 242, 161, 0.08)',
                border: '1px solid rgba(0, 242, 161, 0.4)',
                color: 'var(--accent-emerald)',
                fontSize: '10px',
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: '6px',
                letterSpacing: '0.08em',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-emerald)', display: 'inline-block', boxShadow: '0 0 8px var(--accent-emerald)' }}></span>
                MARKOV ORDER 4 + ARGON2ID
              </span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px', letterSpacing: '0.02em' }}>
              Witten-Bell Smoothed Monte Carlo Estimator (Dell'Amico &amp; Filippone, 2015)
            </p>
          </div>
        </div>

        {/* Clean Pill Navigation Segment */}
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: 'rgba(11, 15, 23, 0.8)',
          padding: '5px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          {[
            { id: 'evaluator', label: 'Markov Evaluator', icon: Cpu },
            { id: 'auth', label: 'Argon2id Portal', icon: Lock },
            { id: 'telemetry', label: 'Security Audit & DB', icon: Database },
            { id: 'architecture', label: 'Architecture', icon: Terminal }
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: isActive ? 'linear-gradient(135deg, rgba(226, 178, 83, 0.22) 0%, rgba(226, 178, 83, 0.12) 100%)' : 'transparent',
                  color: isActive ? 'var(--accent-gold)' : 'var(--text-muted)',
                  border: isActive ? '1px solid rgba(226, 178, 83, 0.6)' : '1px solid transparent',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontFamily: 'var(--font-display)',
                  fontWeight: isActive ? 700 : 600,
                  letterSpacing: '0.04em',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: isActive ? '0 2px 14px rgba(226, 178, 83, 0.2)' : 'none',
                  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
                }}
              >
                <Icon size={14} color={isActive ? 'var(--accent-gold)' : 'currentColor'} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </header>

      {/* ================= MAIN CONTENT CONTAINER ================= */}
      <main style={{ flex: 1, padding: '40px', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
        
        {/* ================= TAB 1: MARKOV GUESSABILITY EVALUATOR ================= */}
        {activeTab === 'evaluator' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px', alignItems: 'stretch' }}>
            
            {/* Left Panel: Real-time Interactive Inspector */}
            <div className="glass-panel" style={{ padding: '34px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 700, color: '#fff', margin: 0 }}>
                    Real-Time Guessability Analyzer
                  </h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '5px' }}>
                    Type to stream probabilistic Markov chain scoring &amp; pattern inspection
                  </p>
                </div>
                {evalLoading && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-gold)', fontSize: '12px', fontWeight: 600 }}>
                    <RefreshCw size={14} className="spin-icon" />
                    Calculating...
                  </div>
                )}
              </div>

              {/* Input Form */}
              <div style={{ marginBottom: '22px' }}>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
                  Target Password String
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={candidatePassword}
                    onChange={(e) => setCandidatePassword(e.target.value)}
                    placeholder="Enter password..."
                    style={{
                      width: '100%',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '14px 48px 14px 16px',
                      color: 'var(--text-main)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '15px',
                      outline: 'none',
                      boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.4)',
                      transition: 'border 0.2s, box-shadow 0.2s',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = 'var(--accent-gold)';
                      e.target.style.boxShadow = '0 0 16px rgba(226, 178, 83, 0.2), inset 0 2px 4px rgba(0,0,0,0.4)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = 'var(--border-subtle)';
                      e.target.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.4)';
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '6px'
                    }}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Username Context Check */}
              <div style={{ marginBottom: '28px' }}>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
                  Associated Username (Context Check)
                </label>
                <input
                  type="text"
                  value={candidateUsername}
                  onChange={(e) => setCandidateUsername(e.target.value)}
                  placeholder="e.g. crypto_admin"
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '11px 16px',
                    color: 'var(--text-main)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    outline: 'none',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.4)'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.25)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
                />
              </div>

              {/* Quick Archetype Benchmarks */}
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', display: 'block', marginBottom: '10px', fontWeight: 600 }}>
                  Quick Archetype Benchmarks
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {samplePresets.map((preset, idx) => (
                    <button
                      key={idx}
                      className="btn-outline"
                      onClick={() => setCandidatePassword(preset.pwd)}
                      title={preset.desc}
                    >
                      <Sparkles size={13} color="var(--accent-gold)" />
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Character N-Gram Decomposition */}
              {evalResult && evalResult.transitions && evalResult.transitions.length > 0 && (
                <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <h3 style={{ fontSize: '12px', fontFamily: 'var(--font-display)', color: 'var(--accent-gold)', letterSpacing: '0.08em', margin: 0, textTransform: 'uppercase' }}>
                      CHARACTER N-GRAM TRANSITION PROBABILITIES
                    </h3>
                    <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      Order-4 Markov Window
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {evalResult.transitions.map((t, idx) => {
                      const isHighProb = t.prob > 0.05;
                      const isVeryLow = t.prob < 0.0001;
                      const badgeColor = isVeryLow ? 'var(--accent-emerald)' : isHighProb ? 'var(--accent-crimson)' : 'var(--accent-gold)';
                      return (
                        <div
                          key={idx}
                          style={{
                            background: 'rgba(255, 255, 255, 0.03)',
                            border: `1px solid ${badgeColor}`,
                            borderRadius: '6px',
                            padding: '6px 10px',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            minWidth: '52px',
                            boxShadow: `0 2px 8px ${badgeColor}22`
                          }}
                        >
                          <span style={{ fontWeight: 700, color: '#fff', fontSize: '14px' }}>
                            {t.char === ' ' ? '␣' : t.char}
                          </span>
                          <span style={{ fontSize: '9px', color: badgeColor, marginTop: '2px', fontWeight: 600 }}>
                            10^{t.log10_prob}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '12px', lineHeight: 1.5 }}>
                    Green badges indicate low transition predictability (resistant). Red indicates frequent rockyou n-gram patterns.
                  </p>
                </div>
              )}
            </div>

            {/* Right Panel: Guessability Metrics & Tier Verdict */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', justifyContent: 'space-between' }}>
              {evalResult ? (
                <>
                  {/* Verdict Card */}
                  <div className="glass-panel" style={{ padding: '30px', borderLeft: `5px solid ${getTierBadge(evalResult.tier).color}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 600 }}>
                          Policy Verdict &amp; Admission
                        </span>
                        <h3 style={{ 
                          fontSize: '32px', 
                          fontFamily: 'var(--font-display)', 
                          fontWeight: 800, 
                          color: getTierBadge(evalResult.tier).color,
                          marginTop: '6px',
                          margin: '6px 0 0 0'
                        }}>
                          {evalResult.tier}
                        </h3>
                      </div>
                      <span style={{
                        padding: '6px 14px',
                        borderRadius: '20px',
                        background: evalResult.is_acceptable ? 'rgba(0, 242, 161, 0.14)' : 'rgba(255, 51, 102, 0.14)',
                        color: evalResult.is_acceptable ? 'var(--accent-emerald)' : 'var(--accent-crimson)',
                        border: `1px solid ${evalResult.is_acceptable ? 'var(--accent-emerald)' : 'var(--accent-crimson)'}`,
                        fontSize: '12px',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        {evalResult.is_acceptable ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                        {evalResult.is_acceptable ? 'REGISTRATION PERMITTED' : 'ADMISSION REJECTED'}
                      </span>
                    </div>

                    {/* Guesses Estimate Display */}
                    <div style={{ 
                      marginTop: '24px', 
                      background: 'rgba(0, 0, 0, 0.4)', 
                      borderRadius: '10px', 
                      padding: '18px',
                      border: '1px solid rgba(255, 255, 255, 0.08)'
                    }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
                        Expected Monte Carlo Guesses (Dell'Amico &amp; Filippone Rank)
                      </div>
                      <div style={{ fontSize: '26px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#fff', marginTop: '6px' }}>
                        {evalResult.estimated_guesses >= 1e15
                          ? evalResult.estimated_guesses.toExponential(2)
                          : evalResult.estimated_guesses.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        <span style={{ fontSize: '13px', color: 'var(--text-muted)', marginLeft: '10px', fontWeight: 400 }}>
                          guesses
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '6px' }}>
                        Log₁₀ Probability: <strong style={{ color: 'var(--accent-gold)' }}>{evalResult.log10_prob}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Quantitative Security Metrics */}
                  <div className="glass-panel" style={{ padding: '28px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: '18px', margin: '0 0 18px 0', fontWeight: 600 }}>
                      Cryptographic &amp; Entropy Telemetry
                    </h4>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                      <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Shannon Entropy</div>
                        <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '6px' }}>
                          {evalResult.shannon_entropy_bits} <span style={{ fontSize: '11px', fontWeight: 400, color: 'var(--text-muted)' }}>bits</span>
                        </div>
                      </div>

                      <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Breached Blocklist</div>
                        <div style={{ 
                          fontSize: '18px', 
                          fontWeight: 700, 
                          color: evalResult.in_blocklist ? 'var(--accent-crimson)' : 'var(--accent-emerald)', 
                          marginTop: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}>
                          {evalResult.in_blocklist ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
                          {evalResult.in_blocklist ? 'Breached Hit' : 'Clean'}
                        </div>
                      </div>
                    </div>

                    {/* Policy Violations or Feedback */}
                    {evalResult.feedback && evalResult.feedback.length > 0 && (
                      <div style={{ marginTop: '22px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--accent-amber)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px', fontWeight: 600 }}>
                          Actionable Security Recommendations
                        </div>
                        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px', margin: 0, padding: 0 }}>
                          {evalResult.feedback.map((msg, i) => (
                            <li key={i} style={{ 
                              fontSize: '12px', 
                              color: 'var(--text-main)', 
                              background: 'rgba(255, 153, 0, 0.08)',
                              borderLeft: '3px solid var(--accent-amber)',
                              padding: '10px 14px',
                              borderRadius: '0 6px 6px 0',
                              lineHeight: 1.4
                            }}>
                              {msg}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <ShieldAlert size={44} color="var(--text-dim)" style={{ marginBottom: '14px' }} />
                  <p>Awaiting password input for Markov analysis...</p>
                </div>
              )}
            </div>

          </div>
        )}

        {/* ================= TAB 2: ARGON2ID AUTHENTICATION PORTAL ================= */}
        {activeTab === 'auth' && (
          <div style={{ maxWidth: '640px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '44px' }}>
              <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, rgba(226, 178, 83, 0.18) 0%, rgba(226, 178, 83, 0.05) 100%)',
                  border: '1px solid var(--accent-gold)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 18px auto',
                  boxShadow: '0 0 24px rgba(226, 178, 83, 0.2)'
                }}>
                  <KeyRound size={26} color="var(--accent-gold)" />
                </div>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 800, color: '#fff', margin: 0 }}>
                  {authMode === 'register' ? 'Cryptographic Registration' : 'Constant-Time Authentication'}
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px', lineHeight: 1.5 }}>
                  {authMode === 'register' 
                    ? 'Pre-screened with Markov model & hashed via Argon2id (m=64MiB, t=3, p=1)' 
                    : 'Timing-attack resilient login verification (constant-time dummy fallback)'}
                </p>
              </div>

              {/* Mode Toggle */}
              <div style={{ 
                display: 'flex', 
                background: 'var(--bg-input)', 
                padding: '5px', 
                borderRadius: '10px', 
                marginBottom: '28px',
                border: '1px solid var(--border-subtle)'
              }}>
                <button
                  type="button"
                  onClick={() => { setAuthMode('login'); setAuthResponse(null); }}
                  style={{
                    flex: 1,
                    background: authMode === 'login' ? 'var(--accent-gold)' : 'transparent',
                    color: authMode === 'login' ? '#07090e' : 'var(--text-muted)',
                    border: 'none',
                    padding: '11px',
                    borderRadius: '7px',
                    fontWeight: 700,
                    fontFamily: 'var(--font-display)',
                    fontSize: '12px',
                    letterSpacing: '0.06em',
                    cursor: 'pointer',
                    boxShadow: authMode === 'login' ? '0 2px 10px rgba(226, 178, 83, 0.3)' : 'none',
                    transition: 'all 0.2s'
                  }}
                >
                  SIGN IN
                </button>
                <button
                  type="button"
                  onClick={() => { setAuthMode('register'); setAuthResponse(null); }}
                  style={{
                    flex: 1,
                    background: authMode === 'register' ? 'var(--accent-gold)' : 'transparent',
                    color: authMode === 'register' ? '#07090e' : 'var(--text-muted)',
                    border: 'none',
                    padding: '11px',
                    borderRadius: '7px',
                    fontWeight: 700,
                    fontFamily: 'var(--font-display)',
                    fontSize: '12px',
                    letterSpacing: '0.06em',
                    cursor: 'pointer',
                    boxShadow: authMode === 'register' ? '0 2px 10px rgba(226, 178, 83, 0.3)' : 'none',
                    transition: 'all 0.2s'
                  }}
                >
                  REGISTER WITH POLICY
                </button>
              </div>

              {/* Auth Form */}
              <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
                    Username
                  </label>
                  <input
                    type="text"
                    required
                    value={authUsername}
                    onChange={(e) => setAuthUsername(e.target.value)}
                    placeholder="e.g. tatvik_99"
                    style={{
                      width: '100%',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '13px 16px',
                      color: 'var(--text-main)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '14px',
                      outline: 'none',
                      boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.4)'
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--accent-gold)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
                    Master Password
                  </label>
                  <input
                    type="password"
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••••••"
                    style={{
                      width: '100%',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '13px 16px',
                      color: 'var(--text-main)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '14px',
                      outline: 'none',
                      boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.4)'
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--accent-gold)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
                  />
                </div>

                <button
                  type="submit"
                  disabled={authLoading}
                  className="btn-primary"
                  style={{ width: '100%', marginTop: '12px' }}
                >
                  {authLoading ? (
                    <>
                      <RefreshCw size={16} className="spin-icon" />
                      Computing Memory-Hard Argon2id Hash...
                    </>
                  ) : authMode === 'register' ? (
                    'Verify Policy & Register User'
                  ) : (
                    'Authenticate Session'
                  )}
                </button>
              </form>

              {/* Server Response Feedback */}
              {authResponse && (
                <div style={{
                  marginTop: '28px',
                  padding: '20px',
                  borderRadius: '10px',
                  background: authResponse.success ? 'rgba(0, 242, 161, 0.08)' : 'rgba(255, 51, 102, 0.08)',
                  border: `1px solid ${authResponse.success ? 'var(--accent-emerald)' : 'var(--accent-crimson)'}`
                }}>
                  {authResponse.success ? (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '14px' }}>
                        <CheckCircle2 size={18} />
                        {authResponse.data.message}
                      </div>
                      {authResponse.data.hash_preview && (
                        <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                          <strong>Stored Hash (Argon2id):</strong> {authResponse.data.hash_preview}
                        </div>
                      )}
                      {authResponse.data.hashing_time_ms && (
                        <div style={{ marginTop: '5px', fontSize: '11px', color: 'var(--text-muted)' }}>
                          <strong>Memory-Hard Execution Time:</strong> {authResponse.data.hashing_time_ms} ms
                        </div>
                      )}
                      {authResponse.data.auth_duration_ms && (
                        <div style={{ marginTop: '5px', fontSize: '11px', color: 'var(--text-muted)' }}>
                          <strong>Verification Timing:</strong> {authResponse.data.auth_duration_ms} ms (Constant Time)
                        </div>
                      )}
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-crimson)', fontWeight: 700, fontSize: '14px', marginBottom: '8px' }}>
                        <XCircle size={18} />
                        Registration / Login Denied
                      </div>
                      <ul style={{ paddingLeft: '20px', fontSize: '12px', color: 'var(--text-main)', margin: 0 }}>
                        {authResponse.errors.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= TAB 3: TELEMETRY & SECURITY AUDIT ================= */}
        {activeTab === 'telemetry' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '22px', marginBottom: '32px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Registered Identities</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--accent-gold)', marginTop: '6px' }}>
                  {telemetry ? telemetry.total_users : '—'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>Stored in SQLite auth.db</div>
              </div>

              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Markov Engine Status</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '14px' }}>
                  ACTIVE (ORDER 4)
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>Witten-Bell Smoothing</div>
              </div>

              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Breach Blocklist</div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '6px' }}>
                  {telemetry ? telemetry.blocklist_count.toLocaleString() : '—'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>Preloaded RockYou passwords</div>
              </div>

              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Argon2id Hardness</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '14px' }}>
                  m=64MiB, t=3, p=1
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>OWASP Compliant Hardness</div>
              </div>
            </div>

            {/* Audit Logs Table */}
            <div className="glass-panel" style={{ padding: '30px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '22px' }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '17px', color: '#fff', margin: 0 }}>
                  Live Cryptographic Authentication &amp; Security Event Log
                </h3>
                <button onClick={fetchTelemetry} className="btn-outline">
                  <RefreshCw size={13} /> Refresh Log
                </button>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '14px 18px' }}>EVENT ID</th>
                      <th style={{ padding: '14px 18px' }}>USERNAME</th>
                      <th style={{ padding: '14px 18px' }}>CLIENT HOST IP</th>
                      <th style={{ padding: '14px 18px' }}>OUTCOME</th>
                      <th style={{ padding: '14px 18px' }}>TIMESTAMP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {telemetry && telemetry.recent_events && telemetry.recent_events.length > 0 ? (
                      telemetry.recent_events.map((evt) => (
                        <tr key={evt.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                          <td style={{ padding: '14px 18px', color: 'var(--text-dim)' }}>#{evt.id}</td>
                          <td style={{ padding: '14px 18px', fontWeight: 600, color: '#fff' }}>{evt.username}</td>
                          <td style={{ padding: '14px 18px', color: 'var(--text-muted)' }}>{evt.ip}</td>
                          <td style={{ padding: '14px 18px' }}>
                            <span style={{
                              padding: '3px 10px',
                              borderRadius: '4px',
                              background: evt.success ? 'rgba(0, 242, 161, 0.12)' : 'rgba(255, 51, 102, 0.12)',
                              color: evt.success ? 'var(--accent-emerald)' : 'var(--accent-crimson)',
                              border: `1px solid ${evt.success ? 'rgba(0, 242, 161, 0.3)' : 'rgba(255, 51, 102, 0.3)'}`,
                              fontSize: '11px',
                              fontWeight: 700
                            }}>
                              {evt.success ? 'SUCCESS' : 'FAILED / BLOCKED'}
                            </span>
                          </td>
                          <td style={{ padding: '14px 18px', color: 'var(--text-dim)' }}>
                            {new Date(evt.ts * 1000).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" style={{ padding: '28px', textAlign: 'center', color: 'var(--text-muted)' }}>
                          No audit events recorded yet. Perform a login or registration attempt.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 4: ARCHITECTURE & METHODOLOGY ================= */}
        {activeTab === 'architecture' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
            <div className="glass-panel" style={{ padding: '34px' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', color: 'var(--accent-gold)', marginBottom: '16px', margin: '0 0 16px 0' }}>
                1. Probabilistic Markov Guessability (n=4)
              </h3>
              <p style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Traditional password policies enforce arbitrary regular expressions (e.g. 1 uppercase, 1 symbol) that fail to thwart statistical password crackers (like Hashcat or John the Ripper) because human users predictably capitalize the first letter and append standard punctuation at the end.
              </p>
              <p style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--text-muted)' }}>
                This system trains a 4th-order Markov chain with Witten-Bell interpolated smoothing on empirical breached passwords. Given a string <em>S = c₁c₂...cₘ</em>, the model computes the joint log-probability across sliding character contexts and queries a calibrated Monte Carlo guess rank estimator (Dell'Amico &amp; Filippone, 2015) to predict the exact number of guesses required by an optimal adversary.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '34px' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', color: 'var(--accent-emerald)', marginBottom: '16px', margin: '0 0 16px 0' }}>
                2. Argon2id Cryptographic Defense (RFC 9106)
              </h3>
              <p style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--text-muted)', marginBottom: '14px' }}>
                Passwords admitted by the Markov policy engine are hashed via Argon2id using the parameter configuration:
              </p>
              <ul style={{ fontSize: '13px', color: 'var(--text-main)', paddingLeft: '20px', lineHeight: '1.8', marginBottom: '14px' }}>
                <li><strong>Memory Cost (m):</strong> 64 MiB RAM per hash</li>
                <li><strong>Time Iterations (t):</strong> 3 passes</li>
                <li><strong>Parallelism (p):</strong> 1 thread</li>
                <li><strong>Salt:</strong> 16-byte cryptographically secure OS PRNG</li>
              </ul>
              <p style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--text-muted)' }}>
                Timing attacks and account enumeration are mitigated using constant-time dummy verification routines for non-existent users, maintaining uniform response latency across valid and invalid user lookups.
              </p>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '18px 40px',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '11px',
        color: 'var(--text-dim)',
        background: 'rgba(7, 9, 14, 0.95)'
      }}>
        <div>Markov-Based Guessability &amp; Cryptographic Authentication Engine</div>
        <div>FastAPI &amp; SQLite • React &amp; Vite • Argon2id (RFC 9106)</div>
      </footer>
    </div>
  );
}
