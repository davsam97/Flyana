# Content review

What a human reviewer should check in the Flyana course before it goes in
front of students. The content was drafted with care, but it has not been
proofread by a subject-matter expert yet.

## How the numbers were checked

Every number in a question or a lesson is recomputed by
[`seeds/check_numbers.py`](srcs/backend/seeds/check_numbers.py)
(`cd srcs/backend && uv run python -m seeds.check_numbers`). It uses ISO 2533
for the standard atmosphere, μ⊕ = 3.986004418 × 10¹⁴ m³/s², R⊕ = 6 371 km
(mean) or 6 378.137 km (equatorial), g₀ = 9.80665 m/s², c and σ from CODATA.
Numeric answers accept ±2 to ±3 % so that rounding of intermediate values
(R = 287 or 287.05, R⊕ = 6 371 or 6 378 km) is never punished.

## Sources

[`seeds/check_links.py`](srcs/backend/seeds/check_links.py)
(`uv run python -m seeds.check_links`) checks every cited URL: it must
answer, and must not be one of the "This page has moved" notices NASA Glenn
leaves at its old addresses with a 200 status. All links passed on
2026-11-09. FAA handbooks are cited without a link: faa.gov refuses
automated requests, so their links could not be checked from here.

## Points to confirm, module by module

### 1. Atmosphere and aerodynamics

- Lift-to-drag ratio "15 to 20" for an airliner and "more than 50" for a
  competition glider: orders of magnitude, not values for a given type.
- Maximum lift coefficient "about 1.5 clean, nearly 3 with flaps and slats":
  typical, varies a lot between designs.
- Concorde cruise at Mach 2.02: the figure usually quoted; its maximum
  operating Mach number was 2.04.
- Question `aero-critical-mach` cites Anderson, *Introduction to Flight*,
  ch. 5: chapter numbering differs between editions.

### 2. Flight mechanics

- Phugoid period "one to two minutes for an airliner in cruise": from the
  classic approximation T ≈ π√2·V/g (≈ 100 s at 230 m/s).
- Anderson chapter numbers (6: performance, 7: stability) differ between
  editions; check against the edition the school library holds.
- "Since the Airbus A320, airliners often have fly-by-wire controls": the
  A320 was the first airliner with digital fly-by-wire throughout;
  Concorde had analogue fly-by-wire before it.

### 3. Propulsion

- Typical specific impulses (solid 250–290 s, kerosene/LOX 300–350 s,
  hypergolic 300–320 s, LH2/LOX 430–460 s, electric 1,500–4,000 s): vacuum
  ranges from textbooks, individual engines fall outside them.
- "Compressor pressure ratio 30 to 60 on recent engines", "turbine inlet
  above 1,500 °C", "bypass ratio above 10 on recent airliner engines",
  "ramjet around Mach 2 to 5": orders of magnitude.
- "About 9.4 km/s of delta-v to low orbit, losses included": the usual
  textbook figure; real launches range from about 9.3 to 10 km/s.
- Liquid hydrogen density "about 71 kg/m³": at its boiling point (20 K).
- Tsiolkovsky published the rocket equation in 1903 (he had derived it in
  1897).

### 4. Orbital mechanics

- Altitudes quoted with "~": ISS ~400 km (it varies between about 370 and
  420 km with reboosts), Hubble "a little over 500 km" (it has been
  decaying since 1990), GPS ~20,200 km, Galileo ~23,200 km.
- LEO "about 160 to 2,000 km" and MEO "about 2,000 to 35,000 km": the usual
  conventions, boundaries vary between sources.
- Sun-synchronous orbits "inclined at about 98°": typical for 600–800 km;
  the exact value depends on altitude.
- Questions use a mean Earth radius of 6,371 km for low orbits and the
  equatorial radius for the geostationary altitude (35,786 km); tolerances
  of ±2–3 % absorb the difference.
- Curtis chapter numbers (2: two-body problem, 6: orbital manoeuvres) are
  those of the 3rd/4th editions.

### 5. Space systems

- Solar constant 1,361 W/m² (Kopp & Lean 2011 give 1,360.8 ± 0.5 W/m²).
- Cell efficiencies "about 30 %" (triple-junction GaAs) and "15 to 20 %"
  (silicon): beginning-of-life values, varying with the product.
- Temperature ranges (sunlit side above +100 °C, shaded side below
  −100 °C, batteries 0–30 °C, electronics about −20 to +50 °C): orders of
  magnitude, not specifications.
- GEO eclipses "at most about 72 minutes a day": usual textbook value.
- Debris "tens of thousands of objects larger than 10 cm tracked from the
  ground": ESA's statistics are updated yearly; check the current figure.
- Frequency bands (S ~2 GHz, X ~8 GHz, Ka ~20–30 GHz): typical space
  allocations, simplified.
- Eclipse duration question assumes a cylindrical shadow and an orbit
  plane containing the Sun (worst case); tolerance ±5 %.

### 6. Avionics and embedded systems

- INS drift "about one nautical mile per hour": the classic figure for
  aircraft-grade (navigation-grade) inertial systems.
- ARINC 429 "up to 20 receivers", MIL-STD-1553 "up to 31 remote
  terminals", CAN "up to 1 Mbit/s classic": from the standards as usually
  summarised; check against the specifications if quoted in detail.
- DO-178C test coverage per level (A: MC/DC, B: decision, C: statement)
  is a simplification: each level carries many more objectives.
- Ariane 501 destroyed "about 40 seconds after lift-off": the inquiry
  report gives about 37 s after main engine ignition; the backup SRI failed
  72 ms before the active one.
- AFDX on the A380 and A350: confirmed widely; the 787 uses a similar
  ARINC 664-based network.
- None of the standards (ARINC 429, MIL-STD-1553, ISO 11898, DO-178C) is
  freely available online: sources are cited without links.

### 7. History and players

- Dates were checked from memory against well-known references; worth a
  second look: CNES founded 19 December 1961; ESA convention signed 30 May
  1975; Ariane 1 first flight 24 December 1979; Jean-Loup Chrétien flew in
  June 1982 (Soyuz T-6); Ariane 5's last flight in July 2023; Ariane 6
  maiden flight on 9 July 2024.
- "More than twenty ESA member states": the exact count changes as states
  join; check the current figure before quoting it.
- Ariane 62 / Ariane 64 boosters and the Vinci re-ignition capability are
  as presented by CNES and ESA; payload capacities were left out on
  purpose, figures vary between sources.
- Wright Flyer, first flight: 12 seconds and 37 m (120 ft), Orville at the
  controls.
