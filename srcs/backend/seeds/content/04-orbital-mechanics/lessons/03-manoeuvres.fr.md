## Le delta-v, la monnaie du voyage spatial

Dans l'espace, on ne parle pas de distance mais de **delta-v** ($\Delta v$) : la somme des changements de vitesse nécessaires à une mission. Chaque manœuvre a un coût en delta-v, et l'équation de Tsiolkovski (module 3) dit combien d'ergols il faut pour le payer. Un **budget de delta-v** est donc le premier calcul de toute mission.

Pour changer d'orbite, on allume le moteur brièvement en un point précis : c'est une **impulsion**. Accélérer dans le sens du mouvement **élève le point opposé** de l'orbite. Freiner l'abaisse.

## Le transfert de Hohmann

Comment passer d'une orbite circulaire basse (rayon $r_1$) à une orbite circulaire haute (rayon $r_2$) avec le moins de delta-v possible, quand $r_2$ n'est pas trop grand devant $r_1$ ? Walter Hohmann a proposé la solution en 1925 :

1. **Première impulsion** au point de départ : on accélère pour passer sur une **ellipse de transfert** dont le périgée est sur l'orbite basse et l'apogée sur l'orbite haute. Son demi-grand axe vaut $a = (r_1 + r_2)/2$.
2. On parcourt **une demi-ellipse**, moteur éteint.
3. **Seconde impulsion** à l'apogée : on accélère de nouveau pour **circulariser** l'orbite haute.

Les vitesses s'obtiennent par la vis-viva :

$$
\Delta v_1 = \sqrt{\mu\left(\frac{2}{r_1} - \frac{1}{a}\right)} - \sqrt{\frac{\mu}{r_1}}
\qquad
\Delta v_2 = \sqrt{\frac{\mu}{r_2}} - \sqrt{\mu\left(\frac{2}{r_2} - \frac{1}{a}\right)}
$$

**Exemple : de 400 km à l'orbite géostationnaire** ($r_1 = 6\,771$ km, $r_2 = 42\,164$ km), dans le même plan :

- $\Delta v_1 \approx 2{,}40$ km/s
- $\Delta v_2 \approx 1{,}46$ km/s
- au total, environ **3,86 km/s**
- durée du transfert, une demi-période de l'ellipse : $\pi\sqrt{a^3/\mu} \approx 5{,}3$ heures

```simulator hohmann
```

En pratique, les lanceurs comme Ariane déposent les satellites de télécommunications directement sur une **orbite de transfert géostationnaire** (GTO), une ellipse dont l'apogée est à 35 786 km. Le satellite effectue lui-même la circularisation avec son moteur d'apogée.

## Changer de plan coûte cher

Modifier l'inclinaison de $\Delta i$ sur une orbite circulaire de vitesse $v$ demande :

$$
\Delta v = 2\,v\,\sin\frac{\Delta i}{2}
$$

À 7,67 km/s, un changement de 10° coûte déjà 1,34 km/s ! On le fait donc là où le satellite va **le plus lentement** : à l'apogée de l'orbite de transfert, en le combinant avec la circularisation. C'est aussi pour cela qu'un site de lancement proche de l'équateur fait économiser du delta-v pour l'orbite géostationnaire.
