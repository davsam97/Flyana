import { describe, expect, it } from 'vitest'

import { R_EARTH, circularSpeed, hohmann, tsiolkovsky } from '../app/utils/physics'

// Reference values from the backend's seeds/check_numbers.py
describe('tsiolkovsky', () => {
  it('gives 4.08 km/s for Isp 300 s and a mass ratio of 4', () => {
    expect(tsiolkovsky(300, 400, 100)).toBeCloseTo(4078.47, 1)
  })

  it('gives nothing without propellant, or with impossible masses', () => {
    expect(tsiolkovsky(300, 100, 100)).toBe(0)
    expect(tsiolkovsky(300, 100, 0)).toBe(0)
    expect(tsiolkovsky(300, 50, 100)).toBe(0)
  })
})

describe('orbits', () => {
  it('gives 7.67 km/s on a circular orbit 400 km up', () => {
    expect(circularSpeed(R_EARTH + 400e3)).toBeCloseTo(7672.6, 0)
  })

  it('computes the Hohmann transfer from 400 km to GEO', () => {
    const transfer = hohmann(R_EARTH + 400e3, 42_164.17e3)
    expect(transfer.firstBurn).toBeCloseTo(2399.5, 0)
    expect(transfer.secondBurn).toBeCloseTo(1457.2, 0)
    expect(transfer.total).toBeCloseTo(3856.7, 0)
    expect(transfer.duration / 3600).toBeCloseTo(5.29, 2)
  })

  it('costs the same going down as going up', () => {
    const up = hohmann(7_000e3, 20_000e3)
    const down = hohmann(20_000e3, 7_000e3)
    expect(down.total).toBeCloseTo(up.total, 6)
  })

  it('costs nothing between two equal orbits', () => {
    expect(hohmann(7_000e3, 7_000e3).total).toBeCloseTo(0, 6)
  })
})
