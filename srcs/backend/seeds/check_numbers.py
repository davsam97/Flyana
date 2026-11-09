"""Recomputes every number the course states, so a reviewer can rerun them

Run: python -m seeds.check_numbers. Constants from ISO 2533 (standard
atmosphere), IERS/IAU (Earth), CODATA (c, sigma).
"""

from __future__ import annotations

import math

G0 = 9.80665  # m/s², standard gravity
MU_EARTH = 3.986004418e14  # m³/s², Earth's gravitational parameter
R_EARTH = 6_371e3  # m, mean radius
R_EQUATOR = 6_378.137e3  # m
SIDEREAL_DAY = 86_164.0905  # s
C = 299_792_458  # m/s
SIGMA = 5.670374419e-8  # W/(m²·K⁴)
SOLAR_CONSTANT = 1361  # W/m² at 1 AU
R_AIR = 287.05287  # J/(kg·K)
GAMMA = 1.4


def isa(h: float) -> tuple[float, float, float]:
    """Temperature (K), pressure (Pa), density (kg/m³) of the ISA troposphere and lower stratosphere"""
    if h <= 11_000:
        t = 288.15 - 0.0065 * h
        p = 101_325 * (t / 288.15) ** (G0 / (0.0065 * R_AIR))
    else:
        t = 216.65
        p11 = 101_325 * (216.65 / 288.15) ** (G0 / (0.0065 * R_AIR))
        p = p11 * math.exp(-G0 * (h - 11_000) / (R_AIR * t))
    return t, p, p / (R_AIR * t)


def sound(t: float) -> float:
    return math.sqrt(GAMMA * R_AIR * t)


def circular(r: float) -> float:
    return math.sqrt(MU_EARTH / r)


def show(label: str, value: float, unit: str = "") -> None:
    print(f"{label:<62} {value:>14.6g} {unit}")


def main() -> None:
    print("— Module 1: atmosphere and aerodynamics")
    t0, p0, rho0 = isa(0)
    show("ISA sea level temperature", t0, "K")
    show("ISA sea level density", rho0, "kg/m³")
    show("speed of sound at sea level", sound(t0), "m/s")
    t11, p11, rho11 = isa(11_000)
    show("ISA 11 km temperature", t11, "K")
    show("ISA 11 km density", rho11, "kg/m³")
    show("speed of sound at 11 km", sound(t11), "m/s")
    show("pressure at 5 500 m / sea level", isa(5_500)[1] / p0)
    show("lift, rho0, V=70 m/s, S=16 m², CL=0.5", 0.5 * rho0 * 70**2 * 16 * 0.5, "N")
    show("Mach of 250 m/s at 11 km", 250 / sound(t11))
    show("dynamic pressure, 250 m/s at 11 km", 0.5 * rho11 * 250**2, "Pa")
    show("Reynolds, rho0, 50 m/s, chord 1.5 m, mu=1.789e-5", rho0 * 50 * 1.5 / 1.789e-5)

    print("— Module 2: flight mechanics")
    show("load factor, level turn at 60° bank", 1 / math.cos(math.radians(60)))
    show("stall speed factor at 60° bank", math.sqrt(1 / math.cos(math.radians(60))))
    show("stall speed, W=10 kN, S=16 m², CLmax=1.6, rho0",
         math.sqrt(2 * 10_000 / (rho0 * 16 * 1.6)), "m/s")
    show("glide distance from 1 000 m at L/D=15", 1_000 * 15, "m")
    show("lift, A320-like 70 t in level flight", 70_000 * G0, "N")

    print("— Module 3: propulsion")
    show("exhaust velocity for Isp 300 s", 300 * G0, "m/s")
    show("delta-v, Isp 300 s, mass ratio 4", 300 * G0 * math.log(4), "m/s")
    show("mass ratio for 9.4 km/s at Isp 450 s", math.exp(9_400 / (450 * G0)))
    show("delta-v, Isp 450 s, mass ratio 3", 450 * G0 * math.log(3), "m/s")
    show("thrust, mdot 250 kg/s, ve 3 000 m/s, matched nozzle", 250 * 3_000, "N")
    show("Isp of that engine", 3_000 / G0, "s")

    print("— Module 4: orbital mechanics")
    r_leo = R_EARTH + 400e3
    show("circular speed at 400 km", circular(r_leo), "m/s")
    show("period at 400 km", 2 * math.pi * math.sqrt(r_leo**3 / MU_EARTH) / 60, "min")
    r_geo = (MU_EARTH * (SIDEREAL_DAY / (2 * math.pi)) ** 2) ** (1 / 3)
    show("GEO radius", r_geo / 1e3, "km")
    show("GEO altitude above the equator", (r_geo - R_EQUATOR) / 1e3, "km")
    show("GEO speed", circular(r_geo), "m/s")
    show("escape speed at the surface", math.sqrt(2 * MU_EARTH / R_EARTH), "m/s")
    show("escape speed at 400 km", math.sqrt(2) * circular(r_leo), "m/s")
    a = (r_leo + r_geo) / 2
    v_peri = math.sqrt(MU_EARTH * (2 / r_leo - 1 / a))
    v_apo = math.sqrt(MU_EARTH * (2 / r_geo - 1 / a))
    dv1, dv2 = v_peri - circular(r_leo), circular(r_geo) - v_apo
    show("Hohmann 400 km -> GEO, first burn", dv1, "m/s")
    show("Hohmann 400 km -> GEO, second burn (no plane change)", dv2, "m/s")
    show("Hohmann 400 km -> GEO, total", dv1 + dv2, "m/s")
    show("Hohmann transfer time", math.pi * math.sqrt(a**3 / MU_EARTH) / 3600, "h")
    show("equator rotation speed", 2 * math.pi * R_EQUATOR / SIDEREAL_DAY, "m/s")
    show("rotation speed at Kourou, 5.2° N",
         2 * math.pi * R_EQUATOR * math.cos(math.radians(5.2)) / SIDEREAL_DAY, "m/s")
    show("plane change 10° at 7.67 km/s", 2 * circular(r_leo) * math.sin(math.radians(5)), "m/s")
    show("Kepler 3: period ratio for a doubled semi-major axis", 2**1.5)

    print("— Module 5: space systems")
    show("solar array 10 m², 30 %, normal sun", 10 * 0.30 * SOLAR_CONSTANT, "W")
    show("one-way light time ground -> GEO (vertical)", (r_geo - R_EQUATOR) / C, "s")
    show("ground -> GEO -> ground (vertical)", 2 * (r_geo - R_EQUATOR) / C, "s")
    show("radiator 1 m², eps 0.85, 300 K", 0.85 * SIGMA * 300**4, "W")
    eclipse = 2 * math.asin(R_EARTH / r_leo) / (2 * math.pi)
    show("max eclipse share at 400 km (cylindrical shadow)", eclipse)
    show("max eclipse at 400 km",
         eclipse * 2 * math.pi * math.sqrt(r_leo**3 / MU_EARTH) / 60, "min")

    print("— Module 6: avionics")
    show("ARINC 429 word time at 100 kbit/s", 32 / 100e3 * 1e3, "ms")
    show("ARINC 429 words/s at 100 kbit/s with 4-bit gap", 100e3 / 36)
    show("MIL-STD-1553 bit time at 1 Mbit/s", 1 / 1e6 * 1e6, "µs")
    show("INS drift, 1 nm/h after 3 h", 3 * 1.852, "km")


if __name__ == "__main__":
    main()
