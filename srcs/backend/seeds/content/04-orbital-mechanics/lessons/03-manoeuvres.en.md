## Delta-v, the currency of space travel

In space we do not talk about distance but about **delta-v** ($\Delta v$): the sum of the changes in speed a mission needs. Every manoeuvre costs some delta-v, and the Tsiolkovsky equation (module 3) tells how much propellant pays for it. A **delta-v budget** is thus the first calculation of any mission.

To change orbit, the engine fires briefly at a precise point: an **impulse**. Speeding up along the motion **raises the opposite point** of the orbit. Slowing down lowers it.

## The Hohmann transfer

How do you go from a low circular orbit (radius $r_1$) to a high circular orbit (radius $r_2$) with the least delta-v, when $r_2$ is not too large compared with $r_1$? Walter Hohmann gave the answer in 1925:

1. **First impulse** at the start: speed up to move onto a **transfer ellipse** whose perigee lies on the low orbit and apogee on the high one. Its semi-major axis is $a = (r_1 + r_2)/2$.
2. Coast along **half the ellipse**, engine off.
3. **Second impulse** at apogee: speed up again to **circularise** on the high orbit.

The speeds come from vis-viva:

$$
\Delta v_1 = \sqrt{\mu\left(\frac{2}{r_1} - \frac{1}{a}\right)} - \sqrt{\frac{\mu}{r_1}}
\qquad
\Delta v_2 = \sqrt{\frac{\mu}{r_2}} - \sqrt{\mu\left(\frac{2}{r_2} - \frac{1}{a}\right)}
$$

**Example: from 400 km to the geostationary orbit** ($r_1 = 6{,}771$ km, $r_2 = 42{,}164$ km), in the same plane:

- $\Delta v_1 \approx 2.40$ km/s
- $\Delta v_2 \approx 1.46$ km/s
- in total, about **3.86 km/s**
- transfer time, half a period of the ellipse: $\pi\sqrt{a^3/\mu} \approx 5.3$ hours

```simulator hohmann
```

In practice, launchers such as Ariane drop telecommunication satellites straight onto a **geostationary transfer orbit** (GTO), an ellipse with its apogee at 35,786 km. The satellite circularises by itself with its apogee engine.

## Changing plane is expensive

Changing the inclination by $\Delta i$ on a circular orbit at speed $v$ takes:

$$
\Delta v = 2\,v\,\sin\frac{\Delta i}{2}
$$

At 7.67 km/s, a 10° change already costs 1.34 km/s! So it is done where the satellite moves **slowest**: at the apogee of the transfer orbit, combined with circularisation. That is also why a launch site near the equator saves delta-v for the geostationary orbit.
