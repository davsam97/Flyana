Un avion ne vole pas dans le vide : il s'appuie sur l'air. Avant de parler d'ailes, il faut donc connaître ce fluide, et surtout savoir qu'il **change avec l'altitude**.

## Un modèle commun : l'atmosphère standard

La température, la pression et la densité de l'air varient chaque jour et en chaque lieu. Pour que les ingénieurs, les pilotes et les instruments parlent de la même chose, on utilise un modèle de référence : l'**atmosphère standard internationale** (ISA, *International Standard Atmosphere*, norme ISO 2533).

Au niveau de la mer, elle fixe :

| Grandeur | Valeur ISA |
|---|---|
| Température $T_0$ | 15 °C, soit 288,15 K |
| Pression $p_0$ | 1013,25 hPa (101 325 Pa) |
| Masse volumique $\rho_0$ | 1,225 kg/m³ |

## Ce qui se passe quand on monte

- **Dans la troposphère** (de 0 à 11 km), la température baisse de 6,5 K par kilomètre : il fait −56,5 °C (216,65 K) à 11 km.
- **À la tropopause** (11 km), cette décroissance s'arrête. Dans la basse **stratosphère**, de 11 à 20 km, la température reste constante dans le modèle ISA.
- **La pression chute bien plus vite que la température** : elle est déjà divisée par deux vers 5 500 m. Sa décroissance n'est pas linéaire mais à peu près exponentielle.

La masse volumique suit la loi des gaz parfaits :

$$
\rho = \frac{p}{R\,T}
$$

avec $R = 287{,}05$ J/(kg·K) pour l'air sec. À 11 km, $\rho \approx 0{,}364$ kg/m³, soit moins d'un tiers de sa valeur au sol.

> Pourquoi c'est important : la portance d'une aile et la poussée d'un moteur dépendent directement de la masse volumique de l'air. Un aérodrome chaud et en altitude (*hot and high*) impose des distances de décollage plus longues.

## La vitesse du son et le nombre de Mach

Le son est une petite perturbation de pression qui se propage dans l'air. Sa vitesse ne dépend que de la température :

$$
a = \sqrt{\gamma\,R\,T}
$$

avec $\gamma = 1{,}4$ pour l'air. On obtient 340 m/s au niveau de la mer, mais seulement 295 m/s à 11 km, parce qu'il y fait plus froid.

Le **nombre de Mach** compare la vitesse de l'avion à cette vitesse du son locale :

$$
M = \frac{V}{a}
$$

Il décrit le comportement de l'air autour de l'avion bien mieux qu'une vitesse en km/h. On distingue :

| Régime | Nombre de Mach |
|---|---|
| Subsonique | $M < 0{,}8$ environ |
| Transsonique | de 0,8 à 1,2 environ |
| Supersonique | de 1,2 à 5 |
| Hypersonique | au-delà de 5 |

Un avion de ligne qui croise à 250 m/s (900 km/h) à 11 km vole à $M = 250 / 295 \approx 0{,}85$.
