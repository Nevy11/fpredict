import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { Trophy, Users, Search, BrainCircuit, PoundSterling, Activity, Star } from 'lucide-react'

export const Route = createFileRoute('/fantasy')({
  component: FantasyPage,
})

const INITIAL_BUDGET = 100.0;

const mockFantasyPlayers = [
  { id: '1', name: 'Erling Haaland', team: 'Manchester City', position: 'FW', price: 14.0, projectedPoints: 195.5, form: 'Excellent' },
  { id: '2', name: 'Bukayo Saka', team: 'Arsenal', position: 'FW', price: 10.0, projectedPoints: 170.2, form: 'Good' },
  { id: '3', name: 'Mohamed Salah', team: 'Liverpool', position: 'FW', price: 12.5, projectedPoints: 185.0, form: 'Excellent' },
  { id: '4', name: 'Martin Ødegaard', team: 'Arsenal', position: 'MF', price: 8.5, projectedPoints: 150.3, form: 'Good' },
  { id: '5', name: 'Rodri', team: 'Manchester City', position: 'MF', price: 6.5, projectedPoints: 120.1, form: 'Excellent' },
  { id: '6', name: 'Trent Alexander-Arnold', team: 'Liverpool', position: 'DEF', price: 7.0, projectedPoints: 145.8, form: 'Average' },
  { id: '7', name: 'Kieran Trippier', team: 'Newcastle', position: 'DEF', price: 6.5, projectedPoints: 130.4, form: 'Good' },
  { id: '8', name: 'Alisson', team: 'Liverpool', position: 'GK', price: 5.5, projectedPoints: 140.0, form: 'Excellent' },
  { id: '9', name: 'Phil Foden', team: 'Manchester City', position: 'MF', price: 8.0, projectedPoints: 160.7, form: 'Excellent' },
  { id: '10', name: 'Ollie Watkins', team: 'Aston Villa', position: 'FW', price: 8.5, projectedPoints: 155.2, form: 'Good' },
  { id: '11', name: 'Cole Palmer', team: 'Chelsea', position: 'MF', price: 9.0, projectedPoints: 165.4, form: 'Excellent' },
  { id: '12', name: 'William Saliba', team: 'Arsenal', position: 'DEF', price: 5.5, projectedPoints: 135.2, form: 'Excellent' },
  { id: '13', name: 'Ederson', team: 'Manchester City', position: 'GK', price: 5.5, projectedPoints: 138.0, form: 'Good' },
]

function FantasyPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPlayers, setSelectedPlayers] = useState<Set<string>>(new Set())
  const [aiAssistantMsg, setAiAssistantMsg] = useState('Welcome to the AI Fantasy Scout. Select players to build your squad, and I will provide dynamic recommendations based on your budget and expected points.')

  const filteredPlayers = mockFantasyPlayers.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.team.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.position.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const squadList = useMemo(() => {
    return mockFantasyPlayers.filter(p => selectedPlayers.has(p.id))
  }, [selectedPlayers])

  const totalCost = squadList.reduce((acc, p) => acc + p.price, 0)
  const remainingBudget = Math.max(0, INITIAL_BUDGET - totalCost)
  const totalProjected = squadList.reduce((acc, p) => acc + p.projectedPoints, 0)

  const togglePlayer = (player: typeof mockFantasyPlayers[0]) => {
    setSelectedPlayers(prev => {
      const newSet = new Set(prev)
      if (newSet.has(player.id)) {
        newSet.delete(player.id)
        generateAiAdvice(newSet, player, false)
      } else {
        if (totalCost + player.price <= INITIAL_BUDGET) {
          if (newSet.size < 15) {
            newSet.add(player.id)
            generateAiAdvice(newSet, player, true)
          } else {
            setAiAssistantMsg("Your squad is full! You can only have 15 players.")
          }
        } else {
          setAiAssistantMsg(`Insufficient funds for ${player.name}. You need £${(player.price - remainingBudget).toFixed(1)}m more.`)
        }
      }
      return newSet
    })
  }

  const generateAiAdvice = (currentSquadIds: Set<string>, lastPlayer: typeof mockFantasyPlayers[0], added: boolean) => {
    const squad = mockFantasyPlayers.filter(p => currentSquadIds.has(p.id))
    const cost = squad.reduce((acc, p) => acc + p.price, 0)
    const budget = INITIAL_BUDGET - cost
    const size = squad.length

    if (added) {
      if (lastPlayer.price >= 10.0) {
        setAiAssistantMsg(`Premium pick! ${lastPlayer.name} has massive upside, but at £${lastPlayer.price}m, you'll need to find budget enablers for the rest of your squad. You have £${budget.toFixed(1)}m left for ${15 - size} players.`)
      } else if (lastPlayer.price <= 6.0 && lastPlayer.position !== 'GK') {
        setAiAssistantMsg(`Smart value pick. ${lastPlayer.name} provides solid projected points without breaking the bank, freeing up funds for premium assets.`)
      } else {
        setAiAssistantMsg(`${lastPlayer.name} added. Your midfield/attack balance is looking solid. Consider checking fixtures for optimal rotation.`)
      }
    } else {
      setAiAssistantMsg(`${lastPlayer.name} removed. You now have £${budget.toFixed(1)}m in the bank. Need a replacement? Consider looking at mid-priced assets to balance the team.`)
    }
  }

  return (
    <div className="container page-stack pb-20">
      <header className="page-header flex flex-col items-center text-center mt-8 mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-emerald-400 text-sm font-semibold tracking-widest uppercase mb-6 backdrop-blur-md">
          <Trophy size={16} />
          <span>Fantasy Engine</span>
        </div>
        <h1 className="heading-primary text-5xl md:text-6xl mb-4">AI Fantasy Scout</h1>
        <p className="subtitle text-lg max-w-2xl text-gray-400 mx-auto">
          Build your ultimate fantasy squad. Leverage machine learning to optimize your budget against dynamic expected points and fixture difficulty.
        </p>
      </header>

      {/* Top Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="glass-card p-6 border-l-4 border-emerald-500 relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-[50px] rounded-full pointer-events-none" />
           <div className="flex items-center gap-4">
             <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
               <PoundSterling size={24} />
             </div>
             <div>
               <div className="text-sm text-gray-400 uppercase tracking-wider font-semibold">Remaining Budget</div>
               <div className="text-3xl font-black text-white">£{remainingBudget.toFixed(1)}m</div>
             </div>
           </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-cyan-500 relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-[50px] rounded-full pointer-events-none" />
           <div className="flex items-center gap-4">
             <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400">
               <Activity size={24} />
             </div>
             <div>
               <div className="text-sm text-gray-400 uppercase tracking-wider font-semibold">Projected Points</div>
               <div className="text-3xl font-black text-white">{totalProjected.toFixed(1)}</div>
             </div>
           </div>
        </div>

        <div className="glass-card p-6 border-l-4 border-purple-500 relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 blur-[50px] rounded-full pointer-events-none" />
           <div className="flex items-center gap-4">
             <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">
               <Users size={24} />
             </div>
             <div>
               <div className="text-sm text-gray-400 uppercase tracking-wider font-semibold">Squad Size</div>
               <div className="text-3xl font-black text-white">{squadList.length} <span className="text-lg text-gray-500">/ 15</span></div>
             </div>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Player Market */}
        <div className="lg:col-span-2 glass-card p-6 flex flex-col h-[700px]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Transfer Market
            </h2>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text" 
                placeholder="Search players, teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>
          
          <div className="overflow-y-auto custom-scrollbar flex-1 pr-2">
            <table className="data-table w-full">
              <thead className="sticky top-0 bg-black/80 backdrop-blur-md z-10">
                <tr>
                  <th>Player</th>
                  <th>Pos</th>
                  <th>Price</th>
                  <th>Proj. Pts</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.map(player => {
                  const isSelected = selectedPlayers.has(player.id);
                  const canAfford = isSelected || (totalCost + player.price <= INITIAL_BUDGET);
                  
                  return (
                  <tr 
                    key={player.id} 
                    className={`hover:bg-white/5 transition-colors ${isSelected ? 'bg-emerald-500/10 border-l-2 border-emerald-500' : ''} ${!canAfford && !isSelected ? 'opacity-50' : ''}`}
                  >
                    <td>
                      <div className="font-semibold text-white">{player.name}</div>
                      <div className="text-xs text-gray-400">{player.team}</div>
                    </td>
                    <td>
                      <span className="px-2 py-1 rounded bg-white/10 text-xs font-bold text-gray-300">
                        {player.position}
                      </span>
                    </td>
                    <td className="text-white font-medium">£{player.price.toFixed(1)}m</td>
                    <td className="text-cyan-400 font-medium">{player.projectedPoints.toFixed(1)}</td>
                    <td>
                      <button 
                        onClick={() => togglePlayer(player)}
                        className={`px-3 py-1 rounded text-xs font-bold transition-colors ${isSelected ? 'bg-red-500/20 text-red-400 hover:bg-red-500/40' : canAfford ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40' : 'bg-gray-500/20 text-gray-500 cursor-not-allowed'}`}
                        disabled={!isSelected && !canAfford}
                      >
                        {isSelected ? 'Remove' : 'Add'}
                      </button>
                    </td>
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: AI Assistant & Selected Squad */}
        <div className="flex flex-col gap-6 h-[700px]">
          {/* AI Guide */}
          <div className="glass-card p-6 flex flex-col border-emerald-500/20 relative overflow-hidden group shrink-0">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 blur-[80px] rounded-full pointer-events-none" />
            
            <div className="flex items-center gap-3 mb-4 border-b border-white/10 pb-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 border border-emerald-500/30">
                <BrainCircuit size={20} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">AI Scout</h2>
                <p className="text-xs text-emerald-400/80 uppercase tracking-wider font-semibold">Live Feedback</p>
              </div>
            </div>
            <div className="bg-emerald-900/20 border border-emerald-500/20 rounded-xl p-4 text-sm text-emerald-100/90 leading-relaxed">
              {aiAssistantMsg}
            </div>
          </div>

          {/* Current Squad */}
          <div className="glass-card p-6 flex flex-col flex-1 overflow-hidden">
             <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Star size={18} className="text-yellow-400" />
                  Your Squad
                </h2>
             </div>
             
             <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-2">
                {squadList.length === 0 ? (
                  <div className="text-center text-gray-500 text-sm mt-10">
                    Your squad is empty. Add players from the transfer market.
                  </div>
                ) : (
                  squadList.map(player => (
                    <div key={player.id} className="bg-black/30 border border-white/5 rounded-lg p-3 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-sm">{player.name}</div>
                        <div className="text-xs text-gray-400">{player.position} • {player.team}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-cyan-400 font-bold text-sm">{player.projectedPoints} pts</div>
                        <div className="text-xs text-gray-500">£{player.price}m</div>
                      </div>
                    </div>
                  ))
                )}
             </div>
          </div>
        </div>

      </div>
    </div>
  )
}
