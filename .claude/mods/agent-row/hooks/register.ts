import type { Register } from 'claude-code'

type Agent = { type: string; description: string; tokenCount: number; label: string }

const formatTokens = (n: number) => (n >= 1000 ? `${Math.floor(n / 100) / 10}k` : String(n))

export const rowBody = (agent: Agent, columns: number) => {
  const row = [
    agent.type !== 'general-purpose' ? agent.type : undefined,
    agent.description,
    `${formatTokens(agent.tokenCount)} tok`,
    agent.label !== agent.description ? agent.label : undefined,
  ]
    .filter(part => part !== undefined)
    .join(' · ')

  return row.length > columns ? `${row.slice(0, columns - 1)}…` : row
}

export const register: Register = on => {
  on('ui.render', { component: 'AgentRow' }, ($, e, next) =>
    next({ ...e, props: { ...e.props, body: rowBody(e.props, e.props.columns ?? 80) } }),
  )
}
