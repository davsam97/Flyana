## Orbital speed

On a **circular** orbit of radius $r$ (measured from the Earth's centre, mean radius 6,371 km), gravity provides exactly the centripetal force:

$$
v = \sqrt{\frac{\mu}{r}}
$$

**Example: the ISS.** At 400 km altitude, $r = 6{,}771$ km:

$$
v = \sqrt{\frac{3.986 \times 10^{14}}{6.771 \times 10^{6}}} \approx 7{,}670 \text{ m/s}
$$

more than 27,000 km/h. One lap takes $T = 2\pi r / v \approx 92$ minutes.

The higher the orbit, **the lower the speed** and the longer the period.

## The vis-viva equation

For an elliptical orbit with semi-major axis $a$, the speed at distance $r$ is:

$$
v^2 = \mu\left(\frac{2}{r} - \frac{1}{a}\right)
$$

For a circle, $r = a$ and we get back $v = \sqrt{\mu/r}$. When $a$ goes to infinity, we get the **escape velocity**, the speed that frees an object from the Earth:

$$
v_{esc} = \sqrt{\frac{2\mu}{r}} = \sqrt{2}\;v_{circ}
$$

It is 11.2 km/s from the surface.

## The main families of orbits

| Orbit | Altitude | Examples |
|---|---|---|
| **LEO**, Low Earth Orbit | about 160 to 2,000 km | ISS (~400 km), Hubble (a little over 500 km), Earth observation |
| **MEO**, Medium Earth Orbit | about 2,000 to 35,000 km | navigation: GPS (~20,200 km), Galileo (~23,200 km) |
| **GEO**, geostationary orbit | 35,786 km, above the equator | telecommunications, weather (Meteosat) |

**The geostationary orbit** has a period equal to the **sidereal day** (23 h 56 min 4 s), the time the Earth takes to turn once relative to the stars. Circular and in the equatorial plane, it turns in step with the Earth: the satellite seems **fixed** in the sky, and a fixed antenna on the ground can point at it. Its speed is only 3.07 km/s.

**The sun-synchronous orbit** is a near-polar low orbit, inclined at about 98°, whose plane turns once a year thanks to the Earth's flattening. The satellite passes over each place at the same local solar time, which gives images under comparable lighting: it is the orbit of observation satellites.

## Inclination and launch site

**Inclination** is the angle between the orbit's plane and the equator's. A launcher fired from latitude $\varphi$ directly reaches an inclination of at least $\varphi$. Launching **eastward** takes advantage of the Earth's rotation: 465 m/s at the equator, 463 m/s at Kourou (5° N). That is one of the strengths of the Guiana Space Centre, especially for the geostationary orbit, which needs zero inclination.
