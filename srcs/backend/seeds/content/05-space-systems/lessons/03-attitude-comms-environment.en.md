## Knowing where you point: attitude control

**Attitude** is the satellite's orientation in space. A camera must aim at the Earth, an antenna at the ground station, the arrays at the Sun. The attitude control system measures this orientation and corrects it.

**Sensors:**

- **sun sensors**: simple and robust, they give the Sun's direction;
- **star trackers**: small cameras that recognise constellations and give the attitude to within a few arcseconds;
- **magnetometers**: they measure the Earth's magnetic field, useful in low orbit;
- **gyroscopes**: they measure rotation rates between two absolute measurements.

**Actuators:**

- **reaction wheels**: flywheels driven by a motor. Spinning the wheel up one way turns the satellite the other way (conservation of angular momentum), without using propellant. But a steady disturbance, such as solar radiation pressure, makes the wheel spin faster and faster until it **saturates**. It must then be "unloaded" with another actuator;
- **magnetorquers**: coils that push against the Earth's magnetic field. They only work well in low orbit;
- **thrusters**: they work anywhere, but use propellant.

## Talking to the ground

The satellite exchanges radio waves with ground stations, in regulated frequency bands: **S band** (around 2 GHz) often carries commands and telemetry, **X band** (around 8 GHz) observation data, **Ka band** (around 20 to 30 GHz) very high data rates.

The **link budget** checks that enough power reaches the receiver. The dominant factor is distance: received power falls as $1/d^2$. **Doubling the distance divides the received power by four.** Distance also brings a delay: at 35,786 km, the ground-satellite-ground round trip takes light about 0.24 s.

## A hostile environment

- **Vacuum**: materials outgas and can contaminate optics; ordinary lubricants evaporate.
- **Radiation**:
  - the **Van Allen belts**, charged particles (protons, electrons) trapped by the Earth's magnetic field;
  - the **South Atlantic Anomaly**, where the inner belt dips down to low orbits;
  - solar flares and cosmic rays.

  They cause **bit flips** (single event upsets) in memories, **cumulative degradation** of electronics (the dose) and wear of solar cells. The answers are **radiation-hardened** parts, error-correcting codes and shielding.
- **Atomic oxygen**, in low orbit, erodes some materials such as polymers.
- **Residual drag** from the upper atmosphere slows low satellites: the ISS must be reboosted regularly.
- **Micrometeoroids and space debris**: millions of fragments, tens of thousands of them larger than 10 cm tracked from the ground. At several km/s, even a fleck of paint is dangerous.
