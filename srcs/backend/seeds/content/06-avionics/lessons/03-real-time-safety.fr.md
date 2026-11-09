## Le temps réel : juste, et à l'heure

Un système **temps réel** ne doit pas seulement calculer juste : il doit rendre son résultat **avant une échéance**. Une loi de pilotage qui calcule l'ordre de gouverne correct avec 200 ms de retard peut faire osciller l'avion. On distingue :

- le **temps réel dur** (*hard real time*) : rater une échéance est une défaillance, comme pour les commandes de vol ;
- le **temps réel souple** : un retard dégrade le service sans danger, comme pour un écran de divertissement.

Il ne s'agit pas d'aller « le plus vite possible » mais d'être **déterministe** : connaître le **pire temps d'exécution** (WCET, *Worst-Case Execution Time*) de chaque tâche et prouver que toutes respectent leurs échéances. Les ordonnanceurs classiques suivent la règle **rate monotonic** : la tâche de période la plus courte reçoit la priorité la plus haute. Un **chien de garde** (*watchdog*) redémarre le calculateur si le logiciel cesse de répondre.

L'avionique modulaire intégrée (IMA) fait tourner plusieurs fonctions sur un même calculateur. La norme **ARINC 653** les isole dans des **partitions**, chacune avec sa mémoire et ses créneaux de temps, pour qu'une fonction défaillante ne perturbe pas les autres.

## Survivre aux pannes : la redondance

- **Redondance active avec vote** : trois calculateurs identiques calculent en parallèle et un voteur retient la valeur majoritaire. Une panne est masquée (« deux sur trois »).
- **Redondance dissemblable** : une même erreur de conception, logicielle surtout, frappera tous les exemplaires identiques en même temps (**mode commun**). Les commandes de vol d'Airbus utilisent donc des calculateurs de conceptions différentes, programmés par des équipes différentes.

## Un cas d'école : Ariane 501

Le 4 juin 1996, le premier vol d'Ariane 5 s'est terminé par la destruction du lanceur environ 40 secondes après le décollage. La commission d'enquête a établi la cause :

1. Le logiciel des centrales inertielles (SRI), **repris d'Ariane 4**, convertissait une valeur flottante sur 64 bits (le biais horizontal) en entier signé sur 16 bits. Avec la trajectoire d'Ariane 5, plus rapide, la valeur a **dépassé la capacité** de l'entier, ce qui a déclenché une exception non traitée.
2. La centrale de secours, **identique**, avait subi la même erreur un instant plus tôt.
3. Le calculateur de bord a interprété le message de diagnostic comme des données de vol et commandé un braquage extrême des tuyères.

Les leçons : la redondance ne protège pas d'une erreur logicielle commune, et un logiciel réutilisé doit être revalidé dans son **nouveau** contexte.

## Certifier le logiciel : la DO-178C

Pour être certifié, le logiciel embarqué dans un avion doit suivre la **DO-178C** (*Software Considerations in Airborne Systems and Equipment Certification*), publiée en 2011 par la RTCA, et en Europe par l'EUROCAE sous le nom d'ED-12C. Elle classe chaque logiciel selon les conséquences d'une défaillance, le **niveau d'assurance de conception** (DAL, *Design Assurance Level*) :

| Niveau | Conséquence d'une défaillance | Exemple d'exigence de test |
|---|---|---|
| A | catastrophique (perte de l'avion) | couverture **MC/DC** |
| B | dangereuse | couverture des décisions |
| C | majeure | couverture des instructions |
| D | mineure | — |
| E | sans effet sur la sécurité | aucun objectif |

La **MC/DC** (*Modified Condition/Decision Coverage*) exige de montrer, par les tests, que chaque condition d'une décision influe à elle seule sur son résultat. La DO-178C demande aussi la traçabilité entre exigences, code et tests, et des revues indépendantes. Le matériel électronique complexe suit une norme sœur, la DO-254.
