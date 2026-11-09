Une aile en mouvement dans l'air subit une force aérodynamique. On la décompose en deux parties :

- la **portance** (*lift*), perpendiculaire à l'écoulement de l'air qui arrive sur l'aile (le vent relatif), qui soutient l'avion ;
- la **traînée** (*drag*), parallèle à cet écoulement et opposée au mouvement, qui le freine.

## D'où vient la portance ?

Une aile inclinée et cambrée **dévie l'air vers le bas**. D'après la troisième loi de Newton, si l'aile pousse l'air vers le bas, l'air pousse l'aile vers le haut. Vu autrement, l'air accélère sur le dessus de l'aile (l'extrados), où la pression baisse, tandis que la pression reste plus forte dessous (l'intrados). Cette différence de pression, intégrée sur toute la surface, donne la même force. Newton et Bernoulli décrivent **le même phénomène**, ce ne sont pas deux théories rivales.

> Une explication fausse circule encore : celle des « temps de parcours égaux ». Elle prétend que l'air de l'extrados, ayant plus de chemin à faire, doit aller plus vite pour retrouver au bord de fuite l'air de l'intrados. Rien n'impose ce rendez-vous. En réalité, l'air de l'extrados arrive au bord de fuite **avant** celui de l'intrados.

## L'équation de la portance

$$
L = \tfrac{1}{2}\,\rho\,V^2\,S\,C_L
$$

- $\rho$ : masse volumique de l'air (kg/m³)
- $V$ : vitesse de l'avion par rapport à l'air (m/s)
- $S$ : surface de l'aile (m²)
- $C_L$ : coefficient de portance, sans unité, qui dépend de la forme de l'aile et de son **angle d'attaque**

Le terme $q = \tfrac{1}{2}\rho V^2$ s'appelle la **pression dynamique**. La vitesse y est au carré : **doubler la vitesse multiplie la portance par quatre**.

**Exemple.** Un avion léger vole au niveau de la mer ($\rho = 1{,}225$ kg/m³) à 70 m/s. Son aile mesure 16 m² et travaille à $C_L = 0{,}5$ :

$$
L = 0{,}5 \times 1{,}225 \times 70^2 \times 16 \times 0{,}5 \approx 24\,000 \text{ N}
$$

C'est de quoi soutenir environ 2,4 tonnes.

## L'angle d'attaque et le décrochage

L'**angle d'attaque** (*angle of attack*) est l'angle entre la corde de l'aile et le vent relatif. Il ne faut pas le confondre avec l'assiette, qui est l'angle entre l'avion et l'horizon. Quand l'angle d'attaque augmente, $C_L$ augmente presque proportionnellement, jusqu'à un **angle critique**, souvent autour de 15°. Au-delà, l'écoulement décolle de l'extrados, la portance chute : c'est le **décrochage** (*stall*). Il dépend de l'angle d'attaque, pas directement de la vitesse : un avion peut décrocher à n'importe quelle vitesse si on dépasse l'angle critique.

## La traînée

$$
D = \tfrac{1}{2}\,\rho\,V^2\,S\,C_D
$$

Elle a deux grandes familles :

- **La traînée parasite** : frottement de l'air sur la peau de l'avion et résistance de forme. Elle croît avec la vitesse.
- **La traînée induite** : c'est le prix de la portance. En bout d'aile, l'air s'enroule de l'intrados vers l'extrados et forme des tourbillons marginaux. Elle est d'autant plus forte que $C_L$ est grand, donc à basse vitesse, et d'autant plus faible que l'aile est **allongée**. L'allongement (*aspect ratio*) est le rapport de l'envergure au carré sur la surface. Les **winglets** la réduisent aussi.

Le rapport $L/D$, la **finesse**, mesure l'efficacité aérodynamique : de l'ordre de 15 à 20 pour un avion de ligne, plus de 50 pour un planeur de compétition.
