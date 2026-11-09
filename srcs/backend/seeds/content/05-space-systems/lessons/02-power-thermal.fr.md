## L'énergie : le Soleil et des batteries

Au voisinage de la Terre, le Soleil fournit environ **1 361 W/m²** : c'est la **constante solaire**, mesurée hors de l'atmosphère. Des **cellules photovoltaïques** la convertissent en électricité. Les cellules à triple jonction en arséniure de gallium des satellites atteignent environ 30 % de rendement, contre 15 à 20 % pour le silicium.

**Exemple.** Un panneau de 10 m² à 30 % de rendement, face au Soleil, produit en début de vie :

$$
P = 10 \times 0{,}30 \times 1\,361 \approx 4\,080 \text{ W}
$$

Il faut en pratique compter avec :

- l'**angle d'incidence** : la puissance est multipliée par $\cos\theta$ si le Soleil n'est pas perpendiculaire au panneau ;
- la **dégradation** des cellules par les radiations, quelques pour cent de puissance perdus au fil des années ;
- les **éclipses** : quand le satellite passe dans l'ombre de la Terre, il vit sur ses **batteries** (aujourd'hui au lithium-ion), rechargées au soleil.

En orbite basse, à 400 km, l'ombre peut durer jusqu'à **36 minutes** sur un tour de 92 : les batteries se chargent et se déchargent environ 16 fois par jour, des dizaines de milliers de fois sur la vie du satellite. En orbite géostationnaire, les éclipses n'ont lieu qu'autour des **équinoxes**, quand le Soleil passe dans le plan de l'équateur, et durent au plus 72 minutes par jour environ.

## Le contrôle thermique : vivre entre −150 °C et +150 °C

Dans le vide, il n'y a **ni convection ni conduction vers l'extérieur** : un satellite n'échange de la chaleur avec son environnement que par **rayonnement**. Il reçoit le Soleil, la lumière réfléchie par la Terre (l'albédo) et l'infrarouge terrestre, et il rayonne vers l'espace froid. La face éclairée peut dépasser +100 °C pendant que la face à l'ombre descend sous −100 °C. Or les batteries veulent rester autour de 0 à 30 °C, et l'électronique entre −20 et +50 °C environ.

La puissance rayonnée par une surface suit la loi de **Stefan-Boltzmann** :

$$
P = \varepsilon\,\sigma\,A\,T^4
$$

avec $\sigma = 5{,}67 \times 10^{-8}$ W/(m²·K⁴) et $\varepsilon$ l'émissivité de la surface (de 0 à 1). Un radiateur de 1 m², d'émissivité 0,85, à 300 K (27 °C), évacue environ 390 W.

Les outils du thermicien :

- **l'isolation multicouche** (MLI, *Multi-Layer Insulation*) : des dizaines de feuilles aluminisées très fines, les « couvertures dorées » des satellites, qui bloquent le rayonnement ;
- **les radiateurs** : des surfaces très émissives et peu absorbantes au Soleil (peinture blanche, miroirs), tournées vers l'espace froid ;
- **les réchauffeurs** électriques, pilotés par thermostat, pour les équipements qui risquent de geler ;
- **les caloducs** (*heat pipes*), qui transportent la chaleur des équipements vers les radiateurs.
