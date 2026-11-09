**Avionics** (aviation electronics) covers every electronic system on board: sensors, computers, displays, radios, autopilot. On a modern airliner it is a major share of the cost. On a launcher or a satellite, the same role is played by **on-board electronics**, on the same principles.

## Measuring the air: the air data chain

- **The static port**, on the side of the fuselage, measures the ambient air pressure $p_s$. Compared with the standard atmosphere, it gives the **pressure altitude**.
- **The pitot tube**, facing the wind, measures the **total pressure** $p_t$, that of air brought to a stop. The difference $p_t - p_s$ is the dynamic pressure $\tfrac{1}{2}\rho V^2$, from which the **airspeed** is derived.
- **Angle-of-attack sensors** measure the angle of attack, essential for stall protection.

A pitot blocked by ice corrupts the displayed speed: a known cause of accidents, hence heated, triplicated probes.

## Finding your way blind: the inertial unit

An **inertial navigation system** (INS) contains an **IMU** (Inertial Measurement Unit):

- three **accelerometers**, measuring accelerations along three axes;
- three **gyroscopes**, measuring rotation rates.

The computer **integrates** these measurements: once for velocity, twice for position. The INS is self-contained (no outside signal, impossible to jam) and delivers measurements at a high rate. But every small error accumulates through the integration: the position **drifts** over time. A good aircraft INS drifts by about one nautical mile per hour (1.852 km/h): after 3 h, the error can reach about 5.6 km.

## Signals from the sky: GNSS

Satellite navigation systems (**GNSS**: the American GPS, the European Galileo, GLONASS, BeiDou) give a position whose error **does not grow** with time, to within a few metres. But the rate is lower, and the signal, very weak at ground level, can be masked or jammed.

## The best of both: hybridisation

INS and GNSS are combined in a **Kalman filter**, an algorithm that weights each source by how much it can be trusted. The INS provides continuity and responsiveness, GNSS regularly corrects the drift. If GNSS is lost, the INS takes over, with an error that slowly starts growing again.

Other common sensors: the **radio altimeter** (height above the ground by radar echo, useful for landing), the **magnetometer**, **star trackers** on spacecraft.
