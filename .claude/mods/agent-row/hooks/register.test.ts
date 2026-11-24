import { expect, test } from 'claude-code/testing'
import { rowBody } from './register'

const agent = { type: 'general-purpose', description: 'PR#123', tokenCount: 12345, label: 'Reading the diff' }

test('general-purpose leads with the label, then tokens, then progress', () => {
  expect(rowBody(agent, 80)).toBe('PR#123 · 12.3k tok · Reading the diff')
})

test('any other type leads the row', () => {
  expect(rowBody({ ...agent, type: 'adversary' }, 80)).toBe('adversary · PR#123 · 12.3k tok · Reading the diff')
})

test('progress equal to the description is not repeated', () => {
  expect(rowBody({ ...agent, label: 'PR#123', tokenCount: 999 }, 80)).toBe('PR#123 · 999 tok')
})

test('a narrow row truncates the tail', () => {
  expect(rowBody(agent, 20)).toBe('PR#123 · 12.3k tok …')
})
