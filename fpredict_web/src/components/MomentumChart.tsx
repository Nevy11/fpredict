import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FeatureSnapshot } from '../lib/api'

type MomentumChartProps = {
  data: FeatureSnapshot[]
}

export function MomentumChart({ data }: MomentumChartProps) {
  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorElo" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#00f0ff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorSdi" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8a2be2" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8a2be2" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis dataKey="gameweek" stroke="#8b949e" />
          <YAxis yAxisId="left" stroke="#00f0ff" domain={['dataMin - 20', 'dataMax + 20']} />
          <YAxis yAxisId="right" orientation="right" stroke="#8a2be2" domain={[0, 1.2]} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 12, 16, 0.9)',
              borderColor: 'rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
            itemStyle={{ color: '#fff' }}
          />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="elo"
            name="Elo Rating"
            stroke="#00f0ff"
            fillOpacity={1}
            fill="url(#colorElo)"
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="sdi"
            name="SDI Multiplier"
            stroke="#8a2be2"
            fillOpacity={1}
            fill="url(#colorSdi)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
