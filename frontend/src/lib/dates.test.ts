import { describe, expect, it } from 'vitest'
import { addDays, daysBetween, eachDay, goalActiveOn, phaseOf, todayIn } from './dates'

describe('todayIn', () => {
  it("follows the user's timezone, not the browser's", () => {
    // 23:30 UTC on 1 Nov is already 2 Nov in Kolkata, still 1 Nov in New York
    const now = new Date('2026-11-01T23:30:00Z')
    expect(todayIn('UTC', now)).toBe('2026-11-01')
    expect(todayIn('Asia/Kolkata', now)).toBe('2026-11-02')
    expect(todayIn('America/New_York', now)).toBe('2026-11-01')
  })
  it('falls back gracefully for an unknown zone', () => {
    expect(todayIn('Nope/Nowhere', new Date('2026-11-01T12:00:00Z'))).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('day maths', () => {
  it('adds and subtracts days across month and year ends', () => {
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01')
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28')
    expect(addDays('2028-02-28', 1)).toBe('2028-02-29') // leap year
  })
  it('counts the days between two dates (DST-safe)', () => {
    expect(daysBetween('2026-10-06', '2026-12-31')).toBe(86) // 87 days inclusive
    expect(daysBetween('2026-03-28', '2026-03-30')).toBe(2) // across a DST change in many zones
  })
  it('lists every day inclusive', () => {
    expect(eachDay('2026-10-30', '2026-11-02')).toEqual(['2026-10-30', '2026-10-31', '2026-11-01', '2026-11-02'])
  })
})

describe('goal window', () => {
  const goal = { active_from: '2026-10-06', active_to: '2026-10-20' }
  it('is inclusive on both ends', () => {
    expect(goalActiveOn(goal, '2026-10-06')).toBe(true)
    expect(goalActiveOn(goal, '2026-10-20')).toBe(true)
    expect(goalActiveOn(goal, '2026-10-05')).toBe(false)
    expect(goalActiveOn(goal, '2026-10-21')).toBe(false)
  })
  it('never ends when not retired', () => {
    expect(goalActiveOn({ active_from: '2026-10-06', active_to: null }, '2030-01-01')).toBe(true)
  })
})

describe('phaseOf', () => {
  const c = { start_date: '2026-10-06', end_date: '2026-12-31' }
  it('classifies a challenge relative to today', () => {
    expect(phaseOf(c, '2026-10-05')).toBe('upcoming')
    expect(phaseOf(c, '2026-10-06')).toBe('running')
    expect(phaseOf(c, '2026-12-31')).toBe('running')
    expect(phaseOf(c, '2027-01-01')).toBe('finished')
  })
})
