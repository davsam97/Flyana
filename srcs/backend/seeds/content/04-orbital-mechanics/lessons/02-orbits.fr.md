## La vitesse orbitale

Sur une orbite **circulaire** de rayon $r$ (mesuré depuis le centre de la Terre, rayon moyen 6 371 km), la gravité fournit exactement la force centripète :

$$
v = \sqrt{\frac{\mu}{r}}
$$

**Exemple : l'ISS.** À 400 km d'altitude, $r = 6\,771$ km :

$$
v = \sqrt{\frac{3{,}986 \times 10^{14}}{6{,}771 \times 10^{6}}} \approx 7\,670 \text{ m/s}
$$

soit plus de 27 000 km/h. Un tour prend $T = 2\pi r / v \approx 92$ minutes.

Plus l'orbite est haute, **plus la vitesse est faible** et plus la période est longue.

## L'équation de la vis-viva

Pour une orbite elliptique de demi-grand axe $a$, la vitesse à la distance $r$ vaut :

$$
v^2 = \mu\left(\frac{2}{r} - \frac{1}{a}\right)
$$

Pour un cercle, $r = a$ et on retrouve $v = \sqrt{\mu/r}$. Quand $a$ devient infini, on obtient la **vitesse de libération**, celle qui permet d'échapper à la Terre :

$$
v_{lib} = \sqrt{\frac{2\mu}{r}} = \sqrt{2}\;v_{circ}
$$

Elle vaut 11,2 km/s depuis la surface.

## Les grandes familles d'orbites

| Orbite | Altitude | Exemples |
|---|---|---|
| **LEO**, orbite basse (*Low Earth Orbit*) | environ 160 à 2 000 km | ISS (~400 km), Hubble (un peu plus de 500 km), observation de la Terre |
| **MEO**, orbite moyenne | environ 2 000 à 35 000 km | navigation : GPS (~20 200 km), Galileo (~23 200 km) |
| **GEO**, orbite géostationnaire | 35 786 km, au-dessus de l'équateur | télécommunications, météo (Meteosat) |

**L'orbite géostationnaire** a une période égale au **jour sidéral** (23 h 56 min 4 s), le temps que met la Terre à faire un tour par rapport aux étoiles. Circulaire et dans le plan de l'équateur, elle tourne au même rythme que la Terre : le satellite semble **immobile** dans le ciel, et une antenne fixe au sol peut le viser. Sa vitesse n'est que de 3,07 km/s.

**L'orbite héliosynchrone** (*sun-synchronous*) est une orbite basse quasi polaire, inclinée d'environ 98°, dont le plan tourne d'un tour par an grâce à l'aplatissement de la Terre. Le satellite survole chaque lieu à la même heure solaire, ce qui donne des images à l'éclairage comparable : c'est l'orbite des satellites d'observation.

## Inclinaison et site de lancement

L'**inclinaison** est l'angle entre le plan de l'orbite et celui de l'équateur. Un lanceur tiré depuis une latitude $\varphi$ atteint directement une inclinaison au moins égale à $\varphi$. Lancer **vers l'est** fait profiter de la rotation de la Terre : 465 m/s à l'équateur, 463 m/s à Kourou (5° N). C'est un des atouts du Centre spatial guyanais, en particulier pour l'orbite géostationnaire, qui demande une inclinaison nulle.
