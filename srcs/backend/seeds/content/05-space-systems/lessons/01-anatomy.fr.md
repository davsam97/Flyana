Un satellite se divise en deux grandes parties :

- la **charge utile** (*payload*) : ce pour quoi il existe. Une caméra pour un satellite d'observation, des répéteurs (*transponders*) pour un satellite de télécommunications, un télescope pour une mission scientifique ;
- la **plateforme** (*bus*) : tout ce qui permet à la charge utile de fonctionner. Elle fournit l'énergie, garde la bonne température, oriente le satellite, communique avec le sol.

Une même plateforme peut porter des charges utiles très différentes : les constructeurs proposent des gammes de plateformes « sur étagère ».

## Les sous-systèmes de la plateforme

| Sous-système | Rôle | Exemples d'équipements |
|---|---|---|
| **Structure** | supporter les efforts du lancement (plusieurs g, vibrations, chocs) | panneaux en nid d'abeille d'aluminium, fibres de carbone |
| **Énergie** (EPS, *Electrical Power System*) | produire, stocker, distribuer l'électricité | panneaux solaires, batteries, régulateurs |
| **Contrôle thermique** (TCS) | garder chaque équipement dans sa plage de température | isolants multicouches, radiateurs, réchauffeurs |
| **Contrôle d'attitude et d'orbite** (SCAO, en anglais ADCS ou AOCS) | connaître et piloter l'orientation du satellite | senseurs stellaires, roues de réaction, magnéto-coupleurs |
| **Propulsion** | corriger l'orbite, la maintenir, désorbiter en fin de vie | propulseurs chimiques ou électriques |
| **Télécommunications** (TT&C, *Telemetry, Tracking and Command*) | recevoir les ordres, envoyer l'état de santé et les données | antennes, émetteurs-récepteurs |
| **Calculateur de bord** (OBC, gestion des données) | faire fonctionner l'ensemble, stocker les données | processeur durci, mémoire de masse |

## Concevoir sans pouvoir réparer

Une fois lancé, un satellite ne se répare pas, sauf rares exceptions comme Hubble. Sa conception repose donc sur :

- des **budgets** tenus de bout en bout : masse, puissance, delta-v, débit de données, chacun avec des marges ;
- la **redondance** : les équipements critiques sont doublés, et le satellite peut basculer sur l'équipement de secours ;
- un **mode survie** (*safe mode*) : en cas d'anomalie, le satellite coupe tout ce qui n'est pas vital, pointe ses panneaux vers le Soleil et attend les ordres du sol.
