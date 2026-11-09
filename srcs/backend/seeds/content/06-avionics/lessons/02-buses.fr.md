## Pourquoi des bus ?

Un avion de ligne compte des centaines d'équipements qui échangent des milliers de données. Les relier tous deux à deux demanderait des kilomètres de câbles en plus, donc des centaines de kilos. On les fait plutôt dialoguer sur des **bus de données** partagés, normalisés pour que des équipements de fournisseurs différents se comprennent. Chaque bus fait des choix différents entre simplicité, débit et déterminisme.

## ARINC 429 : simple et à sens unique

Le standard historique de l'aviation civile (années 1970, toujours omniprésent) :

- **unidirectionnel** : sur une paire torsadée, **un seul émetteur** parle, jusqu'à 20 récepteurs écoutent. Pour répondre, il faut un second bus ;
- des **mots de 32 bits**, dont un **label** de 8 bits qui indique la nature de la donnée (altitude, cap…) ;
- deux vitesses : 12,5 kbit/s ou **100 kbit/s**. À 100 kbit/s, un mot dure $32 / 100\,000 = 0{,}32$ ms.

Très robuste et facile à certifier, mais il faut beaucoup de câbles.

## MIL-STD-1553 : commande et réponse

Né dans l'aviation militaire américaine (1973, version B en 1978), aussi utilisé sur des satellites et sur l'ISS :

- **1 Mbit/s** sur un bus partagé, **doublé** pour la redondance ;
- un **contrôleur de bus** (*bus controller*) unique décide qui parle : il envoie une commande, le **terminal distant** (*remote terminal*) visé répond. Jusqu'à 31 terminaux ;
- aucune collision possible, donc un comportement **déterministe** : on sait exactement quand chaque message passe.

## CAN : multi-maître et priorités

Inventé par Bosch pour l'automobile (années 1980), le bus **CAN** (*Controller Area Network*) s'est répandu dans les drones, les petits satellites et, avec le profil ARINC 825, dans certains avions :

- **multi-maître** : tout nœud peut émettre quand le bus est libre ;
- chaque message porte un **identifiant** qui fixe sa priorité. Si deux nœuds émettent en même temps, un **arbitrage** bit à bit fait gagner l'identifiant le plus faible, sans détruire son message : l'autre nœud se tait et réessaie ;
- jusqu'à 1 Mbit/s en CAN classique, davantage en CAN FD.

## AFDX : l'Ethernet déterministe

Les avions récents (A380, A350) utilisent l'**AFDX** (ARINC 664 partie 7) : de l'Ethernet commuté, en double, où chaque flux circule sur un **lien virtuel** à débit garanti. On obtient les débits de l'Ethernet avec la prévisibilité qu'exige l'aviation.

| Bus | Débit | Topologie | Accès |
|---|---|---|---|
| ARINC 429 | 12,5 ou 100 kbit/s | un émetteur, ≤ 20 récepteurs | sens unique |
| MIL-STD-1553 | 1 Mbit/s | bus partagé doublé | commande/réponse |
| CAN | ≤ 1 Mbit/s (classique) | bus partagé | multi-maître, arbitrage |
| AFDX | 10/100 Mbit/s | Ethernet commuté doublé | liens virtuels |
