An aircraft does not fly in a vacuum: it leans on the air. Before talking about wings, we need to know this fluid, and above all that it **changes with altitude**.

## A shared model: the standard atmosphere

Air temperature, pressure and density vary every day and everywhere. So that engineers, pilots and instruments talk about the same thing, we use a reference model: the **International Standard Atmosphere** (ISA, ISO 2533).

At sea level it sets:

| Quantity | ISA value |
|---|---|
| Temperature $T_0$ | 15 °C, i.e. 288.15 K |
| Pressure $p_0$ | 1013.25 hPa (101,325 Pa) |
| Density $\rho_0$ | 1.225 kg/m³ |

## What happens as you climb

- **In the troposphere** (0 to 11 km), temperature falls by 6.5 K per kilometre: it is −56.5 °C (216.65 K) at 11 km.
- **At the tropopause** (11 km), the fall stops. In the lower **stratosphere**, from 11 to 20 km, temperature stays constant in the ISA model.
- **Pressure drops much faster than temperature**: it is already halved around 5,500 m. It does not fall linearly but roughly exponentially.

Density follows the ideal gas law:

$$
\rho = \frac{p}{R\,T}
$$

with $R = 287.05$ J/(kg·K) for dry air. At 11 km, $\rho \approx 0.364$ kg/m³, less than a third of its sea-level value.

> Why it matters: the lift of a wing and the thrust of an engine depend directly on air density. A hot, high-altitude airfield (*hot and high*) calls for longer take-off runs.

## The speed of sound and the Mach number

Sound is a small pressure disturbance travelling through the air. Its speed depends only on temperature:

$$
a = \sqrt{\gamma\,R\,T}
$$

with $\gamma = 1.4$ for air. That gives 340 m/s at sea level, but only 295 m/s at 11 km, where it is colder.

The **Mach number** compares the aircraft's speed with that local speed of sound:

$$
M = \frac{V}{a}
$$

It describes how the air behaves around the aircraft far better than a speed in km/h. We distinguish:

| Regime | Mach number |
|---|---|
| Subsonic | $M <$ about 0.8 |
| Transonic | about 0.8 to 1.2 |
| Supersonic | 1.2 to 5 |
| Hypersonic | above 5 |

An airliner cruising at 250 m/s (900 km/h) at 11 km flies at $M = 250 / 295 \approx 0.85$.
