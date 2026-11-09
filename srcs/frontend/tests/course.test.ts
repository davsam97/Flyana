import { describe, expect, it } from 'vitest'

import { parseNumber, percent } from '../app/utils/course'

describe('parseNumber', () => {
  it.each([
    ['7,67', '7.67'],
    ['7.67', '7.67'],
    [' 42 164 ', '42164'],
    ['3,986e14', '3.986e14'],
    ['-0,5', '-0.5'],
    ['.5', '.5'],
    ['1\u202f000', '1000'],
  ])('reads %j as %s', (input, expected) => {
    expect(parseNumber(input)).toBe(expected)
  })

  it.each(['', 'abc', '7,6,7', '1e', '--1', '7 km/s'])('refuses %j', (input) => {
    expect(parseNumber(input)).toBeNull()
  })
})

describe('percent', () => {
  it('rounds a ratio to a whole percentage', () => {
    expect(percent('0.8')).toBe(80)
    expect(percent('0.667')).toBe(67)
    expect(percent(1)).toBe(100)
  })
})
