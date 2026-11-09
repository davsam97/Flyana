## Savoir où l'on pointe : le contrôle d'attitude

L'**attitude** est l'orientation du satellite dans l'espace. Une caméra doit viser la Terre, une antenne la station sol, les panneaux le Soleil. Le système de contrôle d'attitude mesure puis corrige cette orientation.

**Les capteurs :**

- **senseurs solaires** : simples et robustes, ils donnent la direction du Soleil ;
- **senseurs stellaires** (*star trackers*) : de petites caméras qui reconnaissent les constellations et donnent l'attitude à quelques secondes d'arc près ;
- **magnétomètres** : ils mesurent le champ magnétique terrestre, utiles en orbite basse ;
- **gyromètres** : ils mesurent les vitesses de rotation entre deux mesures absolues.

**Les actionneurs :**

- **roues de réaction** : des volants d'inertie entraînés par un moteur. Accélérer la roue dans un sens fait tourner le satellite dans l'autre (conservation du moment cinétique), sans consommer d'ergols. Mais une perturbation constante, comme la pression de radiation solaire, oblige la roue à tourner de plus en plus vite jusqu'à **saturer**. Il faut alors la « désaturer » avec un autre actionneur ;
- **magnéto-coupleurs** (*magnetorquers*) : des bobines qui s'appuient sur le champ magnétique terrestre. Ils ne fonctionnent bien qu'en orbite basse ;
- **propulseurs** : ils agissent partout, mais consomment des ergols.

## Parler avec le sol

Le satellite échange avec les stations sol par ondes radio, dans des bandes de fréquences réglementées : la **bande S** (vers 2 GHz) sert souvent à la télécommande et à la télémesure, la **bande X** (vers 8 GHz) aux données d'observation, la **bande Ka** (vers 20 à 30 GHz) aux très hauts débits.

Le **bilan de liaison** (*link budget*) vérifie qu'assez de puissance arrive au récepteur. Le facteur dominant est la distance : la puissance reçue décroît comme $1/d^2$. **Doubler la distance divise la puissance reçue par quatre.** La distance impose aussi un délai : à 35 786 km, l'aller-retour sol-satellite-sol prend environ 0,24 s pour la lumière.

## Un environnement hostile

- **Le vide** : les matériaux dégazent et peuvent contaminer les optiques ; les lubrifiants classiques s'évaporent.
- **Les radiations** :
  - les **ceintures de Van Allen**, des particules chargées (protons, électrons) piégées par le champ magnétique terrestre ;
  - l'**anomalie de l'Atlantique Sud**, où la ceinture intérieure descend jusqu'aux orbites basses ;
  - les éruptions solaires et le rayonnement cosmique.

  Elles provoquent des **inversions de bits** (*single event upsets*) dans les mémoires, une **dégradation cumulée** de l'électronique (la dose) et l'usure des cellules solaires. On y répond par des composants **durcis**, des codes correcteurs d'erreurs et du blindage.
- **L'oxygène atomique**, en orbite basse, érode certains matériaux comme les polymères.
- **La traînée résiduelle** de la haute atmosphère freine les satellites bas : l'ISS doit être régulièrement remontée.
- **Les micrométéorites et les débris spatiaux** : des millions de fragments, dont des dizaines de milliers de plus de 10 cm suivis depuis le sol. À plusieurs km/s, même un éclat de peinture est dangereux.
