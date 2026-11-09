Une fusée emporte **à la fois son carburant et son comburant** (l'oxydant). Elle ne dépend pas de l'air : c'est le seul moteur qui fonctionne dans l'espace.

## L'impulsion spécifique

Pour comparer les moteurs-fusées, on utilise l'**impulsion spécifique** (*specific impulse*) :

$$
I_{sp} = \frac{F}{\dot m\,g_0}
$$

avec $g_0 = 9{,}80665$ m/s². Elle se mesure en **secondes**. C'est la durée pendant laquelle un kilogramme d'ergols peut produire une poussée égale à son propre poids au sol. Plus elle est grande, plus le moteur est efficace. Elle est directement liée à la vitesse d'éjection :

$$
v_e = I_{sp}\,g_0
$$

Une $I_{sp}$ de 300 s correspond ainsi à une vitesse d'éjection de 2 940 m/s.

| Type de propulsion | $I_{sp}$ typique (vide) |
|---|---|
| Propergol solide (poudre) | 250 à 290 s |
| Kérosène et oxygène liquide | 300 à 350 s |
| Ergols hypergoliques (MMH et N₂O₄) | 300 à 320 s |
| Hydrogène et oxygène liquides | 430 à 460 s |
| Propulsion électrique (ionique, à effet Hall) | 1 500 à 4 000 s |

La propulsion électrique a une impulsion spécifique énorme mais une poussée minuscule (quelques dixièmes de newton). Elle sert aux satellites, pas au décollage.

## La tuyère de Laval

Les gaz brûlés sortent de la chambre très chauds et sous haute pression. La **tuyère convergente-divergente** (de Laval) les accélère : le col, la partie la plus étroite, est atteint exactement à Mach 1. Dans la partie divergente, l'écoulement devient supersonique et continue d'accélérer en se détendant. Une tuyère plus longue détend davantage, ce qui convient au vide. Au sol, une tuyère trop longue serait sur-détendue : la pression ambiante y écraserait le jet.

## L'équation de Tsiolkovski

En éjectant de la masse, la fusée s'allège et accélère de plus en plus. Konstantin Tsiolkovski a établi en 1903 le gain de vitesse total, le **delta-v** ($\Delta v$), qu'elle obtient en brûlant ses ergols :

$$
\Delta v = I_{sp}\,g_0\,\ln\frac{m_0}{m_f}
$$

- $m_0$ : masse initiale, ergols compris
- $m_f$ : masse finale, à réservoirs vides
- $m_0 / m_f$ : le **rapport de masse**

**Exemple.** Avec $I_{sp} = 300$ s et un rapport de masse de 4 :

$$
\Delta v = 300 \times 9{,}81 \times \ln 4 \approx 4\,080 \text{ m/s}
$$

Le logarithme est cruel : doubler le rapport de masse n'ajoute que $I_{sp}\,g_0 \ln 2$, alors que doubler l'impulsion spécifique double le delta-v.

```simulator tsiolkovsky
```

## Pourquoi des étages ?

Atteindre l'orbite basse demande environ 9,4 km/s de delta-v, en comptant les pertes dues à la gravité et à la traînée. Même avec de l'hydrogène ($I_{sp} \approx 450$ s), il faudrait un rapport de masse d'environ 8,4 : plus de 88 % de la masse au décollage en ergols, et moins de 12 % pour les réservoirs, les moteurs et la charge utile réunis. C'est à la limite du possible. La solution est l'**étagement** : on largue les réservoirs vides et les moteurs devenus inutiles, pour ne pas les accélérer jusqu'au bout. Chaque étage repart avec un bon rapport de masse.
