import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type EquityPoint = {
  date: string
  bankroll: number
}

type EquityChartProps = {
  data: EquityPoint[]
}

export function EquityChart({ data }: EquityChartProps) {
  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00ff80" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#00ff80" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey="date"
            stroke="#8b949e"
            tickFormatter={(value: string) => value.slice(5)}
          />
          <YAxis stroke="#00ff80" domain={['auto', 'auto']} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(10, 12, 16, 0.9)',
              borderColor: 'rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
            itemStyle={{ color: '#fff' }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Bankroll']}
          />
          <Area
            type="monotone"
            dataKey="bankroll"
            name="Bankroll"
            stroke="#00ff80"
            fillOpacity={1}
            fill="url(#colorEquity)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
