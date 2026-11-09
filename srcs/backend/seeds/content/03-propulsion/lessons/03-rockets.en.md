A rocket carries **both its fuel and its oxidiser**. It does not depend on the air: it is the only engine that works in space.

## Specific impulse

To compare rocket engines, we use **specific impulse**:

$$
I_{sp} = \frac{F}{\dot m\,g_0}
$$

with $g_0 = 9.80665$ m/s². It is measured in **seconds**: the time during which one kilogram of propellant can produce a thrust equal to its own weight on the ground. The larger it is, the more efficient the engine. It is tied directly to the exhaust velocity:

$$
v_e = I_{sp}\,g_0
$$

An $I_{sp}$ of 300 s thus means an exhaust velocity of 2,940 m/s.

| Propulsion type | Typical $I_{sp}$ (vacuum) |
|---|---|
| Solid propellant | 250 to 290 s |
| Kerosene and liquid oxygen | 300 to 350 s |
| Hypergolic propellants (MMH and N₂O₄) | 300 to 320 s |
| Liquid hydrogen and oxygen | 430 to 460 s |
| Electric propulsion (ion, Hall effect) | 1,500 to 4,000 s |

Electric propulsion has a huge specific impulse but a tiny thrust (a few tenths of a newton). It serves satellites, not lift-off.

## The de Laval nozzle

Burnt gases leave the chamber very hot and at high pressure. The **converging-diverging (de Laval) nozzle** accelerates them: the throat, its narrowest point, is reached exactly at Mach 1. In the diverging part, the flow turns supersonic and keeps accelerating as it expands. A longer nozzle expands the gas more, which suits a vacuum. At sea level, too long a nozzle would be over-expanded: the ambient pressure would squeeze the jet.

## The Tsiolkovsky equation

As it throws mass out, the rocket gets lighter and accelerates more and more. Konstantin Tsiolkovsky worked out in 1903 the total gain in speed, the **delta-v** ($\Delta v$), it obtains by burning its propellant:

$$
\Delta v = I_{sp}\,g_0\,\ln\frac{m_0}{m_f}
$$

- $m_0$: initial mass, propellant included
- $m_f$: final mass, tanks empty
- $m_0 / m_f$: the **mass ratio**

**Example.** With $I_{sp} = 300$ s and a mass ratio of 4:

$$
\Delta v = 300 \times 9.81 \times \ln 4 \approx 4{,}080 \text{ m/s}
$$

The logarithm is harsh: doubling the mass ratio only adds $I_{sp}\,g_0 \ln 2$, whereas doubling the specific impulse doubles the delta-v.

```simulator tsiolkovsky
```

## Why stages?

Reaching low orbit takes about 9.4 km/s of delta-v, counting the losses to gravity and drag. Even with hydrogen ($I_{sp} \approx 450$ s), that needs a mass ratio of about 8.4: more than 88 % of the lift-off mass as propellant, and less than 12 % for tanks, engines and payload together. That is at the edge of what can be built. The answer is **staging**: empty tanks and engines that are no longer needed are dropped, so they are not accelerated all the way. Each stage starts afresh with a good mass ratio.
