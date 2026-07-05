import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'

export const Route = createFileRoute('/settings')({
  ssr: false,
  component: Settings,
})

function Settings() {
  const [kellyFraction, setKellyFraction] = useState(0.5)
  const [riskAversion, setRiskAversion] = useState(1.2)
  const [baseBankroll, setBaseBankroll] = useState(1000)
  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    const savedKelly = localStorage.getItem('fpredict_kelly_fraction')
    const savedRisk = localStorage.getItem('fpredict_risk_aversion')
    const savedBankroll = localStorage.getItem('fpredict_base_bankroll')
    
    if (savedKelly) setKellyFraction(parseFloat(savedKelly))
    if (savedRisk) setRiskAversion(parseFloat(savedRisk))
    if (savedBankroll) setBaseBankroll(parseFloat(savedBankroll))
  }, [])

  const handleSave = () => {
    localStorage.setItem('fpredict_kelly_fraction', kellyFraction.toString())
    localStorage.setItem('fpredict_risk_aversion', riskAversion.toString())
    localStorage.setItem('fpredict_base_bankroll', baseBankroll.toString())
    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2000)
  }

  return (
    <div className="container" style={{ width: '100%', maxWidth: '800px' }}>
      <h1 className="heading-primary">Global Settings</h1>
      <p className="subtitle">Configure hyper-parameters and risk management strategies for the trading engine.</p>

      <div className="glass-card">
        <h2 className="heading-secondary" style={{ marginBottom: '2rem' }}>Risk Configuration</h2>
        
        <div className="input-group" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <label className="input-label" style={{ color: '#00f0ff' }}>Fractional Kelly Multiplier</label>
            <span style={{ color: '#fff', fontWeight: 'bold' }}>{kellyFraction}x</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#8b949e', marginBottom: '0.5rem' }}>
            Adjusts the aggressiveness of bankroll allocation. 1.0 is full Kelly (aggressive). 0.25 to 0.5 is recommended.
          </p>
          <input 
            type="range" 
            min="0.1" max="1.0" step="0.1" 
            value={kellyFraction} 
            onChange={(e) => setKellyFraction(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: '#00f0ff' }}
          />
        </div>

        <div className="input-group" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <label className="input-label" style={{ color: '#8a2be2' }}>Risk Aversion Index</label>
            <span style={{ color: '#fff', fontWeight: 'bold' }}>{riskAversion}</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#8b949e', marginBottom: '0.5rem' }}>
            Penalizes teams with high variance in their Squad Degradation Index.
          </p>
          <input 
            type="range" 
            min="0.5" max="3.0" step="0.1" 
            value={riskAversion} 
            onChange={(e) => setRiskAversion(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: '#8a2be2' }}
          />
        </div>

        <div className="input-group" style={{ marginBottom: '2rem' }}>
          <label className="input-label">Base Bankroll ($)</label>
          <input 
            type="number" 
            className="glass-input" 
            value={baseBankroll} 
            onChange={(e) => setBaseBankroll(parseFloat(e.target.value))}
          />
        </div>

        <button 
          className="btn-primary" 
          onClick={handleSave} 
          style={{ 
            background: isSaved ? 'linear-gradient(90deg, #00ff80, #00d4ff)' : undefined 
          }}
        >
          {isSaved ? 'Settings Saved ✓' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}
