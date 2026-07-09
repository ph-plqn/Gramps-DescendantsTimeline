# Gramps Descendants Timeline

Gramps Descendants Timeline est un greffon destiné à Gramps 6.x.

Principe fondamental : Gramps Descendants Timeline est un greffon de visualisation et d'analyse.
Il ne modifie jamais les données généalogiques de la base Gramps.

Contrairement aux arbres généalogiques classiques,
il représente la descendance sur une véritable échelle du temps.

Le greffon repose sur trois principes fondamentaux :

- les descendants sont représentés selon un parcours en profondeur (Depth-First Search, DFS) ;
- un moteur d'inférence temporelle déduit, justifie et explique les dates estimées ;
- aucune donnée de la base Gramps n'est jamais modifiée.

Cette représentation met immédiatement en évidence :

- les durées de vie ;
- les générations ;
- les mariages ;
- les remariages.

Schéma conceptuel :

            Base Gramps
                 │
                 ▼
      Moteur d'inférence temporelle
                 │
                 ▼
          TimelineModel
                 │
                 ▼
          Layout (DFS)
                 │
                 ▼
             Renderer
                 │
                 ▼
      Vue interactive / PDF / SVG

État du projet

Version : 0.1
Statut : En développement

Remerciements

Idée originale, cahier de conception et validation fonctionnelle : Philippe
Architecture logicielle, documentation technique et assistance au développement réalisées avec ChatGPT (OpenAI).