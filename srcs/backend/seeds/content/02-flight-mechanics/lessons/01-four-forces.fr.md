Quatre forces s'exercent sur un avion en vol. Comprendre comment elles s'équilibrent, c'est comprendre presque toutes ses performances.

| Force | Direction | Origine |
|---|---|---|
| **Poids** (*weight*) $W = m\,g$ | vers le centre de la Terre, appliqué au centre de gravité | la gravité |
| **Portance** (*lift*) $L$ | perpendiculaire au vent relatif | l'aile |
| **Traînée** (*drag*) $D$ | parallèle au vent relatif, opposée au mouvement | l'air sur tout l'avion |
| **Poussée** (*thrust*) $T$ | le long de l'axe des moteurs | les moteurs |

## Le vol en palier stabilisé

En **palier rectiligne à vitesse constante**, l'accélération est nulle, donc les forces s'annulent deux à deux :

$$
L = W \qquad T = D
$$

Un avion de ligne de 70 tonnes doit donc produire en croisière une portance d'environ $70\,000 \times 9{,}81 \approx 690$ kN. La poussée nécessaire est bien plus faible : $W$ divisé par la finesse, soit environ 40 kN si $L/D = 17$.

## Monter et descendre

En montée stabilisée selon une pente $\gamma$, une partie du poids s'oppose au mouvement :

$$
T - D = W \sin\gamma
$$

C'est l'**excédent de poussée** $T - D$ qui permet de monter. En **vol plané**, sans poussée, c'est au contraire une composante du poids qui entraîne l'avion vers l'avant. La pente de descente vérifie $\tan\gamma = D/L$ : un planeur de finesse 40 parcourt 40 km pour 1 km de hauteur perdue, sans aucun moteur.

**Exemple.** Un avion de finesse 15 perd son moteur à 1 000 m. Il peut parcourir environ $1\,000 \times 15 = 15$ km avant de toucher le sol, par air calme.

## Le virage et le facteur de charge

Pour virer, le pilote **incline** l'avion d'un angle $\varphi$ : la portance s'incline avec les ailes. Sa composante horizontale tire l'avion vers l'intérieur du virage ; sa composante verticale $L\cos\varphi$ doit toujours équilibrer le poids. Il faut donc **plus** de portance qu'en ligne droite. On mesure ce supplément par le **facteur de charge** (*load factor*) :

$$
n = \frac{L}{W} = \frac{1}{\cos\varphi}
$$

À 60° d'inclinaison, $n = 2$ : les passagers se sentent deux fois plus lourds, on dit qu'ils subissent « 2 g ». La vitesse de décrochage augmente comme $\sqrt{n}$ : elle est multipliée par $\sqrt{2} \approx 1{,}41$ à 60°. C'est pourquoi un virage serré à basse vitesse est dangereux.
