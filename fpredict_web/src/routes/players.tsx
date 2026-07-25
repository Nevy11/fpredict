import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Users, Search, BrainCircuit, Activity, Target } from 'lucide-react'

export const Route = createFileRoute('/players')({
  component: PlayersPage,
})

function PlayersPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [aiQuery, setAiQuery] = useState('')
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null)
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', text: 'Initialize player sub-agent. Who would you like to analyze or train me on today?' }
  ])

  // Mock data for players (since full DB might not be exposed via API yet)
  const mockPlayers = [
    { id: '1', name: 'Erling Haaland', team: 'Manchester City', position: 'FW', xg: 0.95, form: 'Excellent', impact: 8.4 },
    { id: '2', name: 'Bukayo Saka', team: 'Arsenal', position: 'FW', xg: 0.65, form: 'Good', impact: 7.9 },
    { id: '3', name: 'Mohamed Salah', team: 'Liverpool', position: 'FW', xg: 0.72, form: 'Excellent', impact: 8.1 },
    { id: '4', name: 'Martin Ødegaard', team: 'Arsenal', position: 'MF', xg: 0.25, form: 'Good', impact: 7.6 },
    { id: '5', name: 'Rodri', team: 'Manchester City', position: 'MF', xg: 0.15, form: 'Excellent', impact: 8.5 },
  ]

  const filteredPlayers = mockPlayers.filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()) || p.team.toLowerCase().includes(searchTerm.toLowerCase()))

  const handleAiSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!aiQuery.trim()) return
    
    setChatHistory(prev => [...prev, { role: 'user', text: aiQuery }])
    
    // Simulate AI response
    setTimeout(() => {
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        text: `Based on the latest vectors, the tactical blueprint suggests this player has a high expected goal (xG) variance against low-block defenses. I've updated my internal weights.`
      }])
    }, 1000)
    
    setAiQuery('')
  }

  return (
    <div className="container page-stack pb-20">
      <header className="page-header flex flex-col items-center text-center mt-8 mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-cyan-400 text-sm font-semibold tracking-widest uppercase mb-6 backdrop-blur-md">
          <Users size={16} />
          <span>Player Database & AI</span>
        </div>
        <h1 className="heading-primary text-5xl md:text-6xl mb-4">Player Intelligence</h1>
        <p className="subtitle text-lg max-w-2xl text-gray-400 mx-auto">
          Teach the AI about specific players, analyze expected goals against specific opponents, and explore individual performance vectors.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Player Directory */}
        <div className="lg:col-span-2 glass-card p-6 flex flex-col h-[700px]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Active Roster
            </h2>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text" 
                placeholder="Search players..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
          </div>
          
          <div className="overflow-y-auto custom-scrollbar flex-1 pr-2">
            <table className="data-table w-full">
              <thead className="sticky top-0 bg-black/80 backdrop-blur-md z-10">
                <tr>
                  <th>Player</th>
                  <th>Team</th>
                  <th>Pos</th>
                  <th>xG/90</th>
                  <th>Impact</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.map(player => (
                  <tr 
                    key={player.id} 
                    className={`cursor-pointer hover:bg-white/5 transition-colors ${selectedPlayer?.id === player.id ? 'bg-cyan-500/10 border-l-2 border-cyan-500' : ''}`}
                    onClick={() => setSelectedPlayer(player)}
                  >
                    <td className="font-semibold text-white">{player.name}</td>
                    <td>{player.team}</td>
                    <td>
                      <span className="px-2 py-1 rounded bg-white/10 text-xs font-bold text-gray-300">
                        {player.position}
                      </span>
                    </td>
                    <td className="text-cyan-400 font-medium">{player.xg.toFixed(2)}</td>
                    <td className="text-purple-400 font-medium">{player.impact.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: AI Training & Analysis */}
        <div className="glass-card p-6 flex flex-col h-[700px] border-cyan-500/20 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 blur-[80px] rounded-full pointer-events-none" />
          
          <div className="flex items-center gap-3 mb-6 border-b border-white/10 pb-4">
            <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 border border-cyan-500/30">
              <BrainCircuit size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Player AI Model</h2>
              <p className="text-xs text-cyan-400/80 uppercase tracking-wider font-semibold">Training Module</p>
            </div>
          </div>

          {selectedPlayer ? (
            <div className="mb-4 bg-black/40 border border-white/5 rounded-xl p-4 flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-400">Target</div>
                <div className="font-bold text-white">{selectedPlayer.name}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400">Impact Score</div>
                <div className="font-black text-cyan-400 text-lg">{selectedPlayer.impact}</div>
              </div>
            </div>
          ) : (
            <div className="mb-4 bg-black/20 border border-white/5 rounded-xl p-4 text-center text-sm text-gray-500">
              Select a player to focus the AI context.
            </div>
          )}

          <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 pr-2 mb-4">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user' 
                    ? 'bg-cyan-600/30 text-white border border-cyan-500/30' 
                    : 'bg-white/5 text-gray-300 border border-white/10'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleAiSubmit} className="relative mt-auto">
            <input 
              type="text"
              value={aiQuery}
              onChange={e => setAiQuery(e.target.value)}
              placeholder="Teach the AI about this player..."
              className="w-full bg-black/40 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-sm text-white focus:outline-none focus:border-cyan-500 transition-colors"
            />
            <button 
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center hover:bg-cyan-500/40 transition-colors"
            >
              <Target size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
