## Power: the Sun and batteries

Near the Earth, the Sun delivers about **1,361 W/m²**: the **solar constant**, measured outside the atmosphere. **Photovoltaic cells** turn it into electricity. The triple-junction gallium arsenide cells used on satellites reach about 30 % efficiency, against 15 to 20 % for silicon.

**Example.** A 10 m² array at 30 % efficiency, facing the Sun, produces at beginning of life:

$$
P = 10 \times 0.30 \times 1{,}361 \approx 4{,}080 \text{ W}
$$

In practice, you must account for:

- the **angle of incidence**: power is multiplied by $\cos\theta$ when the Sun is not square to the panel;
- cell **degradation** by radiation, a few percent of power lost over the years;
- **eclipses**: when the satellite passes into the Earth's shadow, it lives on its **batteries** (lithium-ion today), recharged in sunlight.

In low orbit at 400 km, the shadow can last up to **36 minutes** of a 92-minute lap: the batteries charge and discharge about 16 times a day, tens of thousands of times over the satellite's life. In geostationary orbit, eclipses only happen around the **equinoxes**, when the Sun crosses the equatorial plane, and last at most about 72 minutes a day.

## Thermal control: living between −150 °C and +150 °C

In a vacuum there is **no convection and no conduction to the outside**: a satellite exchanges heat with its surroundings only by **radiation**. It receives sunlight, light reflected by the Earth (albedo) and the Earth's infrared, and it radiates to cold space. The sunlit side can exceed +100 °C while the shaded side drops below −100 °C. Yet batteries want to stay around 0 to 30 °C, and electronics roughly between −20 and +50 °C.

The power radiated by a surface follows the **Stefan-Boltzmann law**:

$$
P = \varepsilon\,\sigma\,A\,T^4
$$

with $\sigma = 5.67 \times 10^{-8}$ W/(m²·K⁴) and $\varepsilon$ the surface's emissivity (0 to 1). A 1 m² radiator with emissivity 0.85 at 300 K (27 °C) gets rid of about 390 W.

The thermal engineer's tools:

- **multilayer insulation** (MLI): dozens of very thin aluminised sheets, the "golden blankets" of satellites, which block radiation;
- **radiators**: surfaces that emit strongly and absorb little sunlight (white paint, mirrors), facing cold space;
- electric **heaters**, thermostat-controlled, for units at risk of freezing;
- **heat pipes**, which carry heat from the units to the radiators.
