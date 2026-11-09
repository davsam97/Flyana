Tout moteur d'avion ou de fusée repose sur la **troisième loi de Newton** : pour avancer, on éjecte de la matière vers l'arrière. La force que le moteur exerce sur cette matière pour l'accélérer, la matière l'exerce en retour sur le moteur : c'est la **poussée** (*thrust*).

## La poussée vient du débit de quantité de mouvement

Un moteur qui éjecte chaque seconde une masse $\dot m$ (le **débit massique**, en kg/s) à la vitesse $v_e$ par rapport à lui reçoit une poussée :

$$
F = \dot m\,v_e
$$

**Exemple.** Un moteur-fusée qui éjecte 250 kg de gaz par seconde à 3 000 m/s pousse avec $250 \times 3\,000 = 750\,000$ N, soit 750 kN.

On peut obtenir la même poussée en éjectant **peu de masse très vite** ou **beaucoup de masse lentement**. Ce choix est au cœur de la conception des moteurs.

## Le cas de la fusée

Une fusée n'a besoin d'aucun appui extérieur : elle pousse sur ses propres gaz. Elle fonctionne donc **aussi dans le vide**, et même mieux, car l'atmosphère ne gêne plus l'écoulement à la sortie de la tuyère. Son équation complète ajoute un terme de pression :

$$
F = \dot m\,v_e + (p_e - p_a)\,A_e
$$

- $p_e$ : pression des gaz à la sortie de la tuyère
- $p_a$ : pression ambiante
- $A_e$ : aire de sortie de la tuyère

Au sol, $p_a$ vaut environ 1 bar et ce terme réduit la poussée. Dans le vide, $p_a = 0$ et il l'augmente. Un même moteur pousse donc **plus fort dans le vide qu'au sol**.

## Le cas du moteur à réaction

Un turboréacteur, lui, aspire l'air devant lui (qui arrive à la vitesse de vol $v_0$) et le rejette plus vite. Seule la **différence de vitesse** produit de la poussée :

$$
F \approx \dot m_{air}\,(v_e - v_0)
$$

On néglige ici la petite masse de carburant ajoutée.

## Décoller : le rapport poussée sur poids

Une fusée qui part verticalement doit pousser plus fort que son poids : son rapport poussée/poids au décollage doit dépasser 1, typiquement 1,2 à 1,5. Un avion, lui, n'a pas besoin d'une poussée égale à son poids : l'aile fournit la portance, le moteur ne doit vaincre que la traînée, environ dix à vingt fois plus faible.
