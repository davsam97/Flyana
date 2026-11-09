/* The physics behind the course simulators, pure so it can be tested.
 * SI units throughout: metres, seconds, kilograms. Same constants as the
 * backend's seeds/check_numbers.py */

export const G0 = 9.80665 // m/s², standard gravity
export const MU_EARTH = 3.986004418e14 // m³/s², Earth's gravitational parameter
export const R_EARTH = 6_371e3 // m, mean radius

/* Delta-v of a rocket stage by the Tsiolkovsky equation */
export function tsiolkovsky(isp: number, initialMass: number, finalMass: number): number {
  if (finalMass <= 0 || initialMass < finalMass) return 0
  return isp * G0 * Math.log(initialMass / finalMass)
}

export function circularSpeed(radius: number, mu = MU_EARTH): number {
  return Math.sqrt(mu / radius)
}

export interface HohmannTransfer {
  semiMajorAxis: number // m
  firstBurn: number // m/s, at the inner orbit
  secondBurn: number // m/s, at the outer orbit
  total: number // m/s
  duration: number // s, half a transfer orbit
}

/* A Hohmann transfer between two coplanar circular orbits, radii from the
 * centre. Going down costs the same as going up, so the burns are given as
 * magnitudes */
export function hohmann(r1: number, r2: number, mu = MU_EARTH): HohmannTransfer {
  const inner = Math.min(r1, r2)
  const outer = Math.max(r1, r2)
  const a = (inner + outer) / 2
  const perigeeSpeed = Math.sqrt(mu * (2 / inner - 1 / a))
  const apogeeSpeed = Math.sqrt(mu * (2 / outer - 1 / a))
  const firstBurn = perigeeSpeed - circularSpeed(inner, mu)
  const secondBurn = circularSpeed(outer, mu) - apogeeSpeed
  return {
    semiMajorAxis: a,
    firstBurn,
    secondBurn,
    total: firstBurn + secondBurn,
    duration: Math.PI * Math.sqrt(a ** 3 / mu),
  }
}
