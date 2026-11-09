A satellite splits into two main parts:

- the **payload**: what it exists for. A camera on an observation satellite, transponders on a telecommunication satellite, a telescope on a science mission;
- the **platform**, or **bus**: everything that lets the payload work. It supplies power, keeps the right temperature, points the satellite, talks to the ground.

The same platform can carry very different payloads: manufacturers offer ranges of "off-the-shelf" platforms.

## The platform's subsystems

| Subsystem | Role | Example equipment |
|---|---|---|
| **Structure** | withstand launch loads (several g, vibration, shocks) | aluminium honeycomb panels, carbon fibre |
| **Power** (EPS, Electrical Power System) | produce, store, distribute electricity | solar arrays, batteries, regulators |
| **Thermal control** (TCS) | keep each unit within its temperature range | multilayer insulation, radiators, heaters |
| **Attitude and orbit control** (ADCS or AOCS) | know and steer the satellite's orientation | star trackers, reaction wheels, magnetorquers |
| **Propulsion** | correct the orbit, keep it, deorbit at end of life | chemical or electric thrusters |
| **Communications** (TT&C, Telemetry, Tracking and Command) | receive commands, send health data and mission data | antennas, transceivers |
| **On-board computer** (OBC, data handling) | run the whole spacecraft, store data | radiation-hardened processor, mass memory |

## Designing without repair

Once launched, a satellite cannot be repaired, with rare exceptions such as Hubble. Its design therefore relies on:

- **budgets** kept end to end: mass, power, delta-v, data rate, each with margins;
- **redundancy**: critical units are duplicated, and the satellite can switch to the backup;
- a **safe mode**: when something goes wrong, the satellite switches off everything not vital, points its arrays at the Sun and waits for orders from the ground.
