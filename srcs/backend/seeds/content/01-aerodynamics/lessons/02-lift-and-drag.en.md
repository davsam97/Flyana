A wing moving through the air feels an aerodynamic force. We split it in two:

- **lift**, perpendicular to the airflow coming at the wing (the relative wind), which holds the aircraft up;
- **drag**, parallel to that flow and opposed to the motion, which slows it down.

## Where does lift come from?

A tilted, cambered wing **deflects the air downward**. By Newton's third law, if the wing pushes the air down, the air pushes the wing up. Seen another way, the air speeds up over the top of the wing (the upper surface), where pressure drops, while pressure stays higher underneath (the lower surface). That pressure difference, summed over the whole surface, gives the same force. Newton and Bernoulli describe **the same phenomenon**; they are not rival theories.

> A wrong explanation still goes around: "equal transit time". It claims that air over the upper surface, having further to go, must travel faster to meet the lower-surface air again at the trailing edge. Nothing forces that meeting. In fact the upper-surface air reaches the trailing edge **before** the lower-surface air.

## The lift equation

$$
L = \tfrac{1}{2}\,\rho\,V^2\,S\,C_L
$$

- $\rho$: air density (kg/m³)
- $V$: the aircraft's speed relative to the air (m/s)
- $S$: wing area (m²)
- $C_L$: lift coefficient, without unit, which depends on the wing's shape and its **angle of attack**

The term $q = \tfrac{1}{2}\rho V^2$ is called **dynamic pressure**. Speed appears squared: **doubling the speed multiplies lift by four**.

**Example.** A light aircraft flies at sea level ($\rho = 1.225$ kg/m³) at 70 m/s. Its wing is 16 m² and works at $C_L = 0.5$:

$$
L = 0.5 \times 1.225 \times 70^2 \times 16 \times 0.5 \approx 24{,}000 \text{ N}
$$

Enough to hold up about 2.4 tonnes.

## Angle of attack and stall

The **angle of attack** is the angle between the wing's chord and the relative wind. Do not confuse it with pitch attitude, the angle between the aircraft and the horizon. As the angle of attack grows, $C_L$ grows almost proportionally, up to a **critical angle**, often around 15°. Beyond it, the flow separates from the upper surface and lift collapses: that is the **stall**. It depends on angle of attack, not directly on speed: an aircraft can stall at any speed if the critical angle is exceeded.

## Drag

$$
D = \tfrac{1}{2}\,\rho\,V^2\,S\,C_D
$$

It comes in two main families:

- **Parasite drag**: air friction on the aircraft's skin and form resistance. It grows with speed.
- **Induced drag**: the price of lift. At the wingtips, air curls from the lower to the upper surface and forms wingtip vortices. It is all the stronger as $C_L$ is large, so at low speed, and all the weaker as the wing is **slender**. Aspect ratio is the span squared divided by the area. **Winglets** reduce it too.

The ratio $L/D$, the **lift-to-drag ratio**, measures aerodynamic efficiency: around 15 to 20 for an airliner, more than 50 for a competition glider.
