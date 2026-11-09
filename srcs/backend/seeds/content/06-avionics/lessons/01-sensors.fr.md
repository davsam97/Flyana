L'**avionique** (*avionics*, contraction d'*aviation electronics*) regroupe tous les systèmes électroniques de bord : capteurs, calculateurs, écrans, radios, pilote automatique. Sur un avion de ligne moderne, elle représente une part majeure du coût. Sur un lanceur ou un satellite, le même rôle est tenu par l'**électronique de bord**, avec les mêmes principes.

## Mesurer l'air : la chaîne anémo-barométrique

- **La prise statique** (*static port*), sur le flanc du fuselage, mesure la pression de l'air ambiant $p_s$. Comparée à l'atmosphère standard, elle donne l'**altitude pression**.
- **Le tube de Pitot** (*pitot tube*), face au vent, mesure la **pression totale** $p_t$, celle de l'air arrêté net. La différence $p_t - p_s$ est la pression dynamique $\tfrac{1}{2}\rho V^2$, dont on tire la **vitesse air**.
- **Les sondes d'incidence** mesurent l'angle d'attaque, indispensable pour les protections contre le décrochage.

Un Pitot bouché par la glace fausse la vitesse affichée : c'est une cause connue d'accidents, d'où des sondes réchauffées et triplées.

## Se repérer sans rien voir : la centrale inertielle

Une **centrale inertielle** (INS, *Inertial Navigation System*) contient une **IMU** (*Inertial Measurement Unit*) :

- trois **accéléromètres**, qui mesurent les accélérations selon trois axes ;
- trois **gyromètres**, qui mesurent les vitesses de rotation.

Le calculateur **intègre** ces mesures : une fois les accélérations, il obtient la vitesse ; deux fois, la position. L'INS est autonome (aucun signal extérieur, impossible à brouiller) et fournit des mesures à haute cadence. Mais chaque petite erreur s'accumule dans l'intégration : la position **dérive** avec le temps. Une bonne centrale d'avion dérive de l'ordre d'un mille nautique par heure (1,852 km/h) : après 3 h, l'erreur peut atteindre environ 5,6 km.

## Les signaux venus du ciel : le GNSS

Les systèmes de navigation par satellites (**GNSS** : GPS américain, Galileo européen, GLONASS, BeiDou) donnent une position dont l'erreur **ne grandit pas** avec le temps, à quelques mètres près. Mais la cadence est plus faible, et le signal, très faible au sol, peut être masqué ou brouillé.

## Le meilleur des deux : l'hybridation

On combine INS et GNSS dans un **filtre de Kalman**, un algorithme qui pondère chaque source selon sa confiance. L'INS assure la continuité et la réactivité, le GNSS corrige régulièrement la dérive. Si le GNSS disparaît, l'INS prend le relais, avec une erreur qui recommence lentement à grandir.

Autres capteurs courants : **radioaltimètre** (hauteur au-dessus du sol par écho radar, utile à l'atterrissage), **magnétomètre**, **senseurs stellaires** sur les engins spatiaux.
