# Gramps Descendants Timeline

## Architecture logicielle

**Version :** 0.1  
**Statut :** Brouillon d'architecture  
**Document :** `02_Architecture.md`

---

# Table des matières

1. Objet du document
2. Principes architecturaux
3. Vue d'ensemble
4. Frontière avec Gramps
5. Chaîne de traitement
6. Composants principaux
7. Modèle architectural central
8. Gestion de l'inférence temporelle
9. Parcours de descendance et unicité des branches
10. Calcul du layout
11. Rendu et supports de sortie
12. Gestion de l'état et des recalculs
13. Dépendances autorisées
14. Erreurs, diagnostics et dégradation gracieuse
15. Traçabilité entre spécifications et code
16. Décisions d'architecture
17. Évolutions prévues

---

# 1. Objet du document

Le présent document décrit l'architecture logicielle de **Gramps Descendants Timeline**.

Il répond à la question :

> **Comment organiser le logiciel afin d'implémenter les spécifications fonctionnelles sans mélanger les responsabilités ?**

Les règles fonctionnelles sont définies dans `01_Specifications.md`.

Le présent document ne redéfinit pas ces règles. Il décrit les composants nécessaires pour les mettre en œuvre et les relations entre ces composants.

En cas de divergence entre l'architecture et les spécifications fonctionnelles, les spécifications prévalent conformément à **PDC001**.

---

# 2. Principes architecturaux

L'architecture applique directement les principes de conception définis dans les spécifications.

## A001 — Lecture seule de Gramps

Le greffon accède aux données Gramps en lecture seule.

Aucun composant de l'architecture ne possède de responsabilité d'écriture dans la base Gramps.

Les estimations, contraintes, diagnostics et positions graphiques existent uniquement en mémoire.

Cette décision découle notamment de **O003**, **R009** et **E007**.

---

## A002 — Séparation des responsabilités

Chaque composant possède une responsabilité principale clairement définie.

L'architecture sépare :

1. l'accès aux données Gramps ;
2. la construction du modèle généalogique utile ;
3. l'inférence temporelle ;
4. le parcours déterministe de la descendance ;
5. le calcul du layout ;
6. le rendu graphique ;
7. l'intégration avec l'interface Gramps ;
8. les exports.

Cette séparation met en œuvre **PDC003** et **P004**.

---

## A003 — Modèle interne indépendant de Gramps

Après la phase de lecture, le cœur du logiciel ne manipule pas directement les objets Gramps `Person`, `Family` ou `Event`.

Les données nécessaires sont transformées en objets internes du projet.

Cette décision permet :

- de tester le moteur sans lancer Gramps ;
- de limiter l'impact d'une évolution de l'API Gramps ;
- d'empêcher toute modification accidentelle de la base ;
- de réutiliser le moteur dans d'autres contextes.

---

## A004 — Calcul avant dessin

Le rendu graphique ne prend aucune décision généalogique ou temporelle.

Le `Renderer` reçoit un layout déjà calculé.

Il ne :

- parcourt pas la base Gramps ;
- calcule pas les générations ;
- n'estime pas les dates ;
- ne choisit pas l'ordre des descendants ;
- ne déplace pas les objets.

Cette décision met en œuvre **PDC003**, **PDC004**, **D010** et **P004**.

---

## A005 — Résultats explicables

Toute estimation temporelle est accompagnée des contraintes qui l'ont produite.

Les diagnostics et contradictions sont conservés sous forme structurée.

Le moteur ne doit jamais produire une date estimée impossible à expliquer.

Cette décision met en œuvre **PDC008**, **E006** et **P006**.

---

## A006 — Déterminisme

À données et options identiques, les composants de calcul produisent les mêmes résultats.

L'ordre des enfants fourni par Gramps est conservé conformément à **PDC007** et **L007**.

Le moteur n'utilise aucun choix aléatoire.

---

# 3. Vue d'ensemble

L'architecture repose sur une chaîne de composants spécialisés.

```text
┌──────────────────────────────┐
│        Base Gramps           │
│ Person / Family / Event      │
└──────────────┬───────────────┘
               │ lecture seule
               ▼
┌──────────────────────────────┐
│      GrampsDataAdapter       │
│ extraction et normalisation  │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│     DescendanceBuilder       │
│ modèle généalogique interne  │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│   TemporalInferenceEngine    │
│ contraintes et estimations   │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│        TimelineModel         │
│ données consolidées          │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│     DescendanceTraversal     │
│ DFS + branches déjà vues     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│        LayoutEngine          │
│ coordonnées et géométrie     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│        TimelineLayout        │
│ résultat de placement        │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│          Renderer            │
│ dessin indépendant du média  │
└───────┬────────┬────────┬────┘
        │        │        │
        ▼        ▼        ▼
   Vue Gramps   SVG      PDF / PNG
```

Le flux principal est unidirectionnel.

Un composant reçoit le résultat du composant précédent, le transforme et transmet un nouvel objet au composant suivant.

---

# 4. Frontière avec Gramps

## 4.1 Rôle du `GrampsDataAdapter`

`GrampsDataAdapter` constitue la seule frontière entre le cœur du projet et l'API de données Gramps.

Sa responsabilité est de lire les objets Gramps nécessaires à partir de la personne racine.

Il extrait notamment :

- les personnes ;
- les familles ;
- l'ordre des enfants ;
- les événements de naissance ;
- les événements de décès ;
- les événements de mariage ;
- les identifiants internes nécessaires aux références.

Il convertit ensuite ces informations en objets internes simples.

---

## 4.2 Interdiction d'écriture

`GrampsDataAdapter` ne fournit aucune méthode de création, modification ou suppression d'objet Gramps.

Les opérations suivantes sont hors de sa responsabilité :

```text
add_person()
update_person()
add_family()
update_family()
commit()
delete()
```

Cette absence volontaire de fonctions d'écriture constitue une protection architecturale supplémentaire de **R009**.

---

## 4.3 Conservation des identifiants Gramps

Chaque objet interne issu de Gramps conserve le `handle` de l'objet source.

Le `handle` sert uniquement à :

- garantir l'identité d'un objet ;
- détecter les objets déjà rencontrés ;
- établir les références ;
- permettre l'ouverture future de la fiche correspondante dans l'interface Gramps.

Le `handle` n'est pas utilisé comme critère d'ordre si les spécifications définissent un autre ordre.

En particulier, l'ordre des enfants provient de la famille Gramps conformément à **L007**.

---

# 5. Chaîne de traitement

La génération d'une timeline suit les étapes suivantes.

```text
1. Sélection de la personne racine
              │
              ▼
2. Lecture des données Gramps
              │
              ▼
3. Construction du modèle de descendance
              │
              ▼
4. Construction des contraintes temporelles
              │
              ▼
5. Résolution des estimations et diagnostics
              │
              ▼
6. Consolidation du TimelineModel
              │
              ▼
7. Parcours DFS de la descendance
              │
              ▼
8. Attribution des rangs verticaux
              │
              ▼
9. Calcul des coordonnées du layout
              │
              ▼
10. Rendu
```

Chaque étape doit pouvoir être testée indépendamment.

---

# 6. Composants principaux

## 6.1 `GrampsDataAdapter`

**Responsabilité :** lire et normaliser les données provenant de Gramps.

**Entrée :**

- base Gramps ;
- handle de la personne racine.

**Sortie :**

- objets généalogiques internes bruts.

**Ne fait pas :**

- d'inférence ;
- de DFS de présentation ;
- de placement ;
- de dessin.

---

## 6.2 `DescendanceBuilder`

**Responsabilité :** construire le sous-graphe généalogique utile à la timeline.

Il part de la personne racine et collecte :

- ses familles ;
- ses conjoints ;
- ses enfants ;
- les familles des descendants ;
- les descendants successifs.

Il respecte l'ordre des enfants fourni par Gramps.

Il construit un graphe interne et non un arbre strict, car une même personne ou une même famille peut être atteinte par plusieurs chemins généalogiques.

Cette distinction est essentielle pour les unions entre descendants apparentés.

---

## 6.3 `TemporalInferenceEngine`

**Responsabilité :** déterminer les informations temporelles exploitables sans modifier les données Gramps.

Le moteur :

1. collecte les dates connues ;
2. crée des contraintes temporelles ;
3. combine les contraintes compatibles ;
4. détecte les contradictions ;
5. détermine un intervalle possible ;
6. propose éventuellement une date estimée ;
7. calcule un niveau de certitude ;
8. conserve la justification complète.

Le moteur produit des résultats en mémoire uniquement.

---

## 6.4 `TimelineModel`

**Responsabilité :** fournir une représentation consolidée des données nécessaires aux étapes de parcours, de layout et de rendu.

`TimelineModel` contient notamment :

- les personnes ;
- les familles ;
- les relations utiles ;
- les générations ;
- les dates connues ;
- les résultats d'inférence ;
- les diagnostics temporels.

`TimelineModel` ne contient pas les coordonnées graphiques finales.

Il représente **ce qui doit être affiché**, et non **où cela doit être affiché**.

---

## 6.5 `DescendanceTraversal`

**Responsabilité :** produire l'ordre vertical déterministe des descendants.

Le composant applique le parcours en profondeur défini par **L006**.

Pour chaque famille, les enfants sont parcourus dans l'ordre fourni par Gramps conformément à **L007**.

Le composant détecte également les branches de descendance déjà représentées conformément à **R010** et **P007**.

Il produit une séquence de lignes logiques destinée au `LayoutEngine`.

---

## 6.6 `LayoutEngine`

**Responsabilité :** transformer la séquence logique et les informations temporelles en coordonnées graphiques.

Le `LayoutEngine` calcule notamment :

- les bornes temporelles ;
- la conversion d'une date en coordonnée horizontale ;
- le rang vertical de chaque personne ;
- la position des barres de vie ;
- la position des nœuds de mariage ;
- les segments de remariage ;
- les références vers des branches déjà représentées.

Le `LayoutEngine` ne dessine rien.

---

## 6.7 `TimelineLayout`

**Responsabilité :** contenir le résultat complet du calcul de placement.

Il s'agit d'un objet de données en lecture seule pour les composants de rendu.

Il contient notamment :

- les dimensions logiques de la timeline ;
- l'échelle temporelle ;
- les barres de vie positionnées ;
- les nœuds de mariage positionnés ;
- les segments de remariage ;
- les textes ;
- les références de branches ;
- les marqueurs de diagnostic.

Le même `TimelineLayout` doit pouvoir être utilisé par la vue interactive et par les exports conformément à **PDC004**.

---

## 6.8 `Renderer`

**Responsabilité :** traduire un `TimelineLayout` en primitives graphiques.

Le renderer dessine :

- les axes ;
- les graduations ;
- les barres de vie ;
- les nœuds de mariage ;
- les segments ;
- les textes ;
- les références ;
- les marqueurs visuels.

Il applique les règles graphiques **G001 à G012**.

Il ne recalcule jamais le layout.

---

## 6.9 Adaptateurs de sortie

Les supports d'affichage et d'export sont des adaptateurs utilisant le même résultat de layout.

Les premiers adaptateurs prévus sont :

- `GrampsViewAdapter` ;
- `SvgExporter` ;
- `PdfExporter` ;
- `PngExporter`.

Ils ne contiennent aucune logique généalogique.

---

# 7. Modèle architectural central

Le cœur de l'architecture repose sur trois catégories d'objets.

## 7.1 Objets généalogiques internes

Ils représentent les données lues dans Gramps.

Exemples envisagés :

```text
PersonNode
FamilyNode
EventData
```

Ces objets conservent l'identité des objets Gramps d'origine.

---

## 7.2 Objets d'inférence

Ils représentent les raisonnements temporels.

Exemples envisagés :

```text
TemporalConstraint
TemporalInterval
InferenceResult
InferenceReason
InferenceDiagnostic
CertaintyLevel
```

Ils sont indépendants du rendu.

---

## 7.3 Objets de layout

Ils représentent la géométrie calculée.

Exemples envisagés :

```text
TimelineLayout
PersonPlacement
MarriageNodePlacement
RemarriageSegment
BranchReferencePlacement
TimelineScale
```

Ils sont indépendants de Gramps et du moteur d'inférence.

---

# 8. Gestion de l'inférence temporelle

## 8.1 Principe

Le moteur d'inférence ne cherche pas directement une date.

Il cherche d'abord à déterminer les contraintes qui encadrent l'événement.

Exemple :

```text
Naissance après celle du frère aîné : ≥ 1786
Naissance avant celle du frère cadet : ≤ 1792
```

Le moteur obtient alors :

```text
Intervalle possible : [1786, 1792]
```

Une date proposée peut ensuite être calculée à partir de cet intervalle.

---

## 8.2 `TemporalConstraint`

Une contrainte temporelle décrit une borne ou une relation.

Elle doit au minimum conserver :

- le type de contrainte ;
- la borne minimale éventuelle ;
- la borne maximale éventuelle ;
- l'objet source ;
- la règle de spécification concernée ;
- une justification lisible par l'utilisateur.

Exemple conceptuel :

```text
TemporalConstraint
    kind        = AFTER_SIBLING
    minimum     = 1786
    source      = "Jean DUPONT"
    rule        = "E005"
    explanation = "L'enfant est placé après son frère aîné dans la famille Gramps."
```

---

## 8.3 `InferenceResult`

Le résultat d'une inférence contient :

```text
event_type
known_value
estimated_value
minimum
maximum
certainty
constraints
diagnostics
```

Une valeur connue dans Gramps reste une valeur connue.

Le moteur ne remplace jamais une valeur Gramps par une estimation.

---

## 8.4 Niveau de certitude

Le projet utilise les niveaux suivants :

1. `CERTAIN` — Certaine
2. `VERY_PROBABLE` — Très probable
3. `PROBABLE` — Probable
4. `POSSIBLE` — Possible
5. `UNDETERMINED` — Indéterminée

Le calcul exact du niveau de certitude sera décrit dans `03_Algorithms.md`.

Le niveau de certitude ne doit pas être confondu avec le niveau de confiance d'une information éventuellement enregistré dans Gramps.

---

## 8.5 Diagnostics

Lorsque les contraintes sont contradictoires, le moteur ne force pas une estimation.

Il crée un diagnostic.

Exemple :

```text
Contrainte A : naissance >= 1795
Contrainte B : naissance <= 1792

Résultat : CONTRADICTION
```

Le diagnostic conserve les deux contraintes responsables de l'incompatibilité.

---

# 9. Parcours de descendance et unicité des branches

## 9.1 Graphe et non arbre strict

Le modèle généalogique interne est traité comme un graphe.

Une union entre deux descendants de la personne racine peut rendre une même branche accessible par plusieurs chemins.

Le moteur doit donc distinguer :

- la première représentation d'une branche ;
- les rencontres ultérieures de cette même branche.

---

## 9.2 Parcours DFS

Le parcours vertical suit **L006**.

Le moteur développe la première branche jusqu'à son dernier descendant.

Il revient ensuite au frère ou à la sœur suivante.

Schéma conceptuel :

```text
Racine
  │
  ├── Enfant 1
  │     │
  │     ├── Enfant 1.1
  │     │      │
  │     │      └── Enfant 1.1.1
  │     │
  │     └── Enfant 1.2
  │
  └── Enfant 2
```

Ordre produit :

```text
Racine
Enfant 1
Enfant 1.1
Enfant 1.1.1
Enfant 1.2
Enfant 2
```

---

## 9.3 Registre des branches représentées

`DescendanceTraversal` maintient un registre des branches déjà développées.

Ce registre doit permettre de déterminer si une descendance a déjà reçu une représentation principale.

Lors d'une seconde rencontre :

1. la branche n'est pas développée une seconde fois ;
2. une référence logique est créée ;
3. le `LayoutEngine` positionne cette référence ;
4. le `Renderer` l'affiche conformément à **G012**.

Le choix exact de la clé d'identité d'une branche sera formalisé dans `03_Algorithms.md`.

---

# 10. Calcul du layout

## 10.1 Coordonnées logiques

## 10.1 Coordonnées logiques

Le layout est calculé dans un système de coordonnées propre à la timeline et indépendant du support d'affichage.

La position horizontale d'un objet est déterminée par sa position temporelle.

La position verticale est déterminée par son rang dans l'ordre de représentation calculé par le parcours de descendance.

Ces coordonnées ne sont pas exprimées directement en pixels.

Lors de l'affichage ou de l'export, une transformation convertit les coordonnées logiques en coordonnées propres au support utilisé.

Le zoom et le déplacement de la vue modifient uniquement cette transformation.

Ils ne modifient pas le layout et n'entraînent aucun nouveau calcul de placement.

---

## 10.2 Axe horizontal

La coordonnée horizontale dépend uniquement du temps.

Conceptuellement :

```text
x = transformation(date)
```

La fonction exacte de transformation sera définie dans `03_Algorithms.md`.

Tous les éléments utilisent la même transformation temporelle conformément à **G008**.

---

## 10.3 Axe vertical

La coordonnée verticale dépend de l'ordre produit par `DescendanceTraversal`.

Chaque ligne logique reçoit un rang vertical stable.

Conceptuellement :

```text
y = rang_de_ligne × hauteur_de_ligne
```

Les détails d'espacement restent sous la responsabilité du `LayoutEngine`.

---

## 10.4 Nœuds de mariage

Pour une famille comprenant deux individus et disposant d'une date de mariage connue ou estimée, le `LayoutEngine` calcule un nœud de mariage.

Sa position horizontale correspond à la date du mariage.

Sa position verticale se situe entre les barres de vie des deux individus conformément à **G004**.

Une famille comportant un seul individu ne produit aucun nœud conformément à **C013** et **C014**.

---

# 11. Rendu et supports de sortie

Le rendu repose sur un contrat commun.

Conceptuellement :

```text
render(layout, drawing_context, render_options)
```

Le renderer ignore l'origine du contexte graphique.

Le contexte peut représenter :

- une zone de dessin de la vue Gramps ;
- une surface SVG ;
- une surface PDF ;
- une surface raster destinée au PNG.

Cette approche garantit l'homogénéité définie par **G010**.

---

# 12. Gestion de l'état et des recalculs

Les différents changements n'entraînent pas tous les mêmes recalculs.

| Changement | Modèle | Inférence | DFS | Layout | Rendu |
|---|---:|---:|---:|---:|---:|
| Zoom | Non | Non | Non | Non | Oui |
| Déplacement de la vue | Non | Non | Non | Non | Oui |
| Taille de fenêtre | Non | Non | Non | Non* | Oui |
| Changement de personne racine | Oui | Oui | Oui | Oui | Oui |
| Modification de la base Gramps | Oui | Oui | Oui | Oui | Oui |
| Changement d'une règle d'affichage | Non | Non | Non | Selon option | Oui |
| Changement d'une règle d'inférence | Non | Oui | Selon résultat | Oui | Oui |

`*` Une modification de taille ne recalcule pas le layout tant que les coordonnées logiques restent indépendantes du viewport.

La stratégie précise d'invalidation sera détaillée dans `03_Algorithms.md`.

---

# 13. Dépendances autorisées

Les dépendances suivent une direction unique.

```text
GrampsDataAdapter
        ↓
DescendanceBuilder
        ↓
TemporalInferenceEngine
        ↓
TimelineModel
        ↓
DescendanceTraversal
        ↓
LayoutEngine
        ↓
TimelineLayout
        ↓
Renderer
        ↓
View / Exporters
```

Une couche basse ne dépend jamais d'une couche de présentation.

En particulier :

- `TemporalInferenceEngine` ne dépend pas de GTK ;
- `LayoutEngine` ne dépend pas de Cairo ;
- `TimelineModel` ne dépend pas du `Renderer` ;
- les exports ne lisent pas directement la base Gramps.

---

# 14. Erreurs, diagnostics et dégradation gracieuse

Le projet distingue trois catégories de situations.

## 14.1 Donnée absente

Exemple : date de naissance inconnue.

Traitement :

- tentative d'inférence ;
- représentation partielle si nécessaire.

---

## 14.2 Donnée incohérente

Exemple : naissance postérieure au décès.

Traitement :

- conservation de la donnée Gramps ;
- création d'un diagnostic ;
- aucune correction silencieuse.

---

## 14.3 Erreur technique

Exemple : objet Gramps devenu inaccessible pendant la construction du modèle.

Traitement :

- erreur journalisée ;
- arrêt contrôlé du traitement concerné ;
- message compréhensible pour l'utilisateur lorsque nécessaire.

Le principe de **C012 — Dégradation gracieuse** s'applique aux données généalogiques incomplètes.

Il ne doit pas masquer les erreurs techniques de programmation.

---

# 15. Traçabilité entre spécifications et code

Les composants et tests doivent référencer les règles qu'ils mettent en œuvre lorsque cela apporte une information utile.

Exemple :

```python
# L006, L007
# Parcours DFS en respectant l'ordre des enfants fourni par Gramps.
```

Les références aux règles ne remplacent pas les commentaires expliquant l'algorithme.

Elles établissent le lien entre :

```text
Spécification
      ↓
Architecture
      ↓
Algorithme
      ↓
Code
      ↓
Test
```

---

# 16. Décisions d'architecture

Les décisions importantes doivent être conservées dans le présent document ou, si leur nombre augmente, dans des Architecture Decision Records (ADR).

Premières décisions identifiées :

| ID | Décision |
|---|---|
| ADR-001 | Le cœur du moteur utilise un modèle interne indépendant des objets Gramps. |
| ADR-002 | Le parcours vertical est un DFS déterministe. |
| ADR-003 | L'ordre des enfants provient de Gramps. |
| ADR-004 | Les inférences sont conservées avec leurs contraintes et justifications. |
| ADR-005 | Le layout est calculé indépendamment du rendu. |
| ADR-006 | Une branche de descendance possède une représentation principale unique. |
| ADR-007 | Le greffon n'écrit jamais dans la base Gramps. |

Les ADR seront détaillés lorsque l'architecture sera stabilisée.

---

# 17. Évolutions prévues

L'architecture doit permettre ultérieurement :

- l'ajout de nouvelles règles d'inférence ;
- l'ajout de nouveaux niveaux ou méthodes de calcul de certitude ;
- l'ajout de marqueurs de diagnostics ;
- l'ajout de nouveaux formats d'export ;
- l'ajout d'une vue Web ou HTML ;
- l'ajout d'autres représentations chronologiques ;
- l'exploitation du moteur d'inférence par d'autres outils.

Ces évolutions ne doivent pas nécessiter de réécrire le modèle généalogique central.

---

# 18. Orchestration générale

## 18.1 `TimelineEngine`

L'architecture introduit un composant d'orchestration nommé
conceptuellement `TimelineEngine`.

Sa responsabilité est de coordonner la chaîne de traitement. Il ne
réalise lui-même aucun calcul généalogique, temporel, de parcours ou de
placement.

``` text
TimelineEngine
      │
      ├── GrampsDataAdapter
      ├── DescendanceBuilder
      ├── TemporalInferenceEngine
      ├── TimelineModel
      ├── DescendanceTraversal
      └── LayoutEngine
```

Conceptuellement :

``` text
generate(root_person)
        │
        ▼
raw_data = adapter.read(root_person)
        │
        ▼
graph = builder.build(raw_data)
        │
        ▼
inference = inference_engine.resolve(graph)
        │
        ▼
model = create_model(graph, inference)
        │
        ▼
traversal = traversal_engine.traverse(model)
        │
        ▼
layout = layout_engine.compute(model, traversal)
        │
        ▼
return layout
```

`TimelineEngine` retourne un `TimelineLayout`. Le rendu intervient après
cette chaîne de calcul.

## 18.2 Pourquoi un orchestrateur séparé ?

Sans orchestrateur, la vue Gramps devrait connaître toutes les étapes
internes du moteur.

La vue demande simplement :

> Génère la timeline pour cette personne racine.

Le moteur retourne un `TimelineLayout`.

La vue ne connaît pas les détails de l'inférence, du DFS ou du
placement.

------------------------------------------------------------------------

# 19. Contrats entre composants

Chaque composant communique avec les autres au moyen d'objets
explicitement définis.

``` text
Gramps
   │
   ▼
RawGenealogyData
   │
   ▼
DescendanceGraph
   │
   ├──────────────► InferenceReport
   │                       │
   └──────────────┬────────┘
                  ▼
            TimelineModel
                  │
                  ▼
          TraversalResult
                  │
                  ▼
           TimelineLayout
```

## 19.1 `RawGenealogyData`

Contient les données normalisées extraites de Gramps :

-   personnes ;
-   familles ;
-   événements ;
-   personne racine.

RawGenealogyData est un sous-ensemble ciblé et minimal des données Gramps nécessaires à la racine sélectionnée. Il est limité au nombre de personnes utiles et aux données utiles :

Base Gramps
     ↓
sélection ciblée
     ↓
données minimales utiles
     ↓
RawGenealogyData


Person Gramps
├── nom              ✓ utile
├── genre            ✓ utile
├── familles         ✓ utile
├── événements       ✓ utiles selon leur type
├── notes            ✗
├── médias           ✗
├── URL              ✗
└── tags             ✗

La liste des données utiles pourrait évoluer si une future InferenceRule a besoin d'une nouvelle donnée Gramps. C'est cohérent avec ## P005.

À ce stade, aucune date n'est estimée, aucun DFS de présentation n'est
effectué et aucune coordonnée n'existe.

## 19.2 `DescendanceGraph`

Représente le sous-graphe généalogique accessible depuis la personne
racine.

Il conserve :

-   les descendants ;
-   les conjoints nécessaires ;
-   les familles ;
-   l'ordre Gramps des enfants ;
-   les relations ;
-   la génération des descendants.

Une même personne rencontrée par plusieurs chemins n'est pas dupliquée
dans le graphe.

## 19.3 `InferenceReport`

Regroupe les résultats et diagnostics du moteur d'inférence.

Conceptuellement :

``` text
(person_handle, BIRTH)    -> InferenceResult
(person_handle, DEATH)    -> InferenceResult
(family_handle, MARRIAGE) -> InferenceResult
```

Le `TimelineModel` peut ainsi consulter une information temporelle sans
relancer l'inférence.

## 19.4 `TraversalResult`

Décrit l'ordre logique de représentation.

Il contient une séquence ordonnée d'éléments tels que :

``` text
PERSON
SPOUSE
BRANCH_REFERENCE
```

Chaque élément reçoit un rang logique. Ce rang n'est pas une coordonnée
en pixels.

------------------------------------------------------------------------

# 20. Identité, références et unicité

## 20.1 Identité des objets

L'identité d'une personne ou d'une famille repose sur son `handle`
Gramps.

Le nom et les dates ne sont jamais utilisés comme identité technique.

Deux personnes peuvent avoir le même nom et les mêmes dates tout en
restant deux objets distincts.

## 20.2 Références internes

Les objets internes utilisent des références par identité plutôt que des
copies récursives.

Conceptuellement :

``` text
PersonNode
    handle
    family_handles

FamilyNode
    handle
    parent_handles
    child_handles
```

Cette organisation évite la duplication des objets et permet de gérer
les unions entre descendants apparentés.

## 20.3 Représentation principale

Le moteur distingue :

``` text
objets déjà rencontrés
```

et :

``` text
branches déjà développées
```

Ces notions ne sont pas équivalentes.

Une personne déjà rencontrée peut devoir apparaître comme conjoint.

Une branche déjà développée ne doit pas être développée une seconde fois
conformément à R010 et P007.

L'identité exacte d'une branche sera définie dans `03_Algorithms.md`.

------------------------------------------------------------------------

# 21. Architecture extensible du moteur d'inférence

## 21.1 Règles d'inférence indépendantes

Le moteur d'inférence ne doit pas devenir une fonction contenant une
longue succession de conditions.

Il utilise des règles indépendantes.

``` text
TemporalInferenceEngine
          │
          ├── BirthOrderRule
          ├── ParentMarriageRule
          ├── PersonalMarriageRule
          ├── LifeIntervalRule
          └── futures règles...
```

Chaque règle produit zéro, une ou plusieurs `TemporalConstraint`.

## 21.2 Contrat d'une règle

Conceptuellement :

``` text
InferenceRule
    rule_id
    applies_to(context)
    produce_constraints(context)
```

Une règle observe les données et produit des contraintes.

Elle ne choisit pas la date estimée finale.

## 21.3 Résolution centralisée

Le moteur rassemble les contraintes puis effectue une résolution
commune.

``` text
Contraintes
     │
     ▼
Intersection des intervalles
     │
     ├── compatible ──► intervalle
     │                     │
     │                     ▼
     │                 estimation
     │                     │
     │                     ▼
     │               niveau de certitude
     │
     └── incompatible ─► diagnostic
```

Cette séparation met directement en œuvre P005.

## 21.4 Registre des règles

Les règles actives sont fournies au moteur sous forme d'une collection
ordonnée.

L'ajout d'une nouvelle règle ne doit pas nécessiter la modification des
règles existantes.

L'ordre d'exécution ne doit pas modifier le résultat final lorsque les
contraintes produites sont identiques.

------------------------------------------------------------------------

# 22. Modèle des dates

## 22.1 Date source et date exploitable

L'architecture distingue la date Gramps de la position temporelle
exploitable.

Une date Gramps peut être :

-   exacte ;
-   partielle ;
-   approximative ;
-   comprise dans un intervalle ;
-   absente.

Le moteur ne transforme donc pas immédiatement toute date en une simple
année.

## 22.2 `TemporalValue`

Un objet conceptuel `TemporalValue` peut contenir :

``` text
source_value
minimum
maximum
representative_value
origin
certainty
```

`source_value` conserve la valeur Gramps lorsqu'elle existe.

`minimum` et `maximum` décrivent l'intervalle exploitable.

`representative_value` est utilisée lorsqu'un point unique est
nécessaire au placement.

`origin` distingue notamment :

``` text
GRAMPS
INFERRED
```

## 22.3 Précision et certitude

Une date précise peut provenir d'une information peu fiable.

Une estimation peut être fortement contrainte par plusieurs informations
cohérentes.

L'architecture distingue donc :

-   la précision temporelle ;
-   la certitude de l'inférence ;
-   le niveau de confiance éventuellement présent dans Gramps.

Ces trois notions ne sont pas confondues.

------------------------------------------------------------------------

# 23. Architecture du layout

## 23.1 Deux axes indépendants

Le `LayoutEngine` traite séparément les deux axes.

``` text
Temps ─────────────► X

Ordre DFS
     │
     ▼
     Y
```

La position horizontale dépend du temps.

La position verticale dépend du parcours déterministe.

## 23.2 Coordonnées logiques

Le layout est calculé dans un système de coordonnées propre à la
timeline et indépendant du support d'affichage.

La position horizontale d'un objet est déterminée par sa position
temporelle.

La position verticale est déterminée par son rang dans l'ordre de
représentation calculé par le parcours de descendance.

Ces coordonnées ne sont pas exprimées directement en pixels.

Lors de l'affichage ou de l'export, une transformation convertit les
coordonnées logiques en coordonnées propres au support utilisé.

Le zoom et le déplacement modifient uniquement cette transformation. Ils
ne modifient pas le layout et n'entraînent aucun nouveau calcul de
placement.

## 23.3 `TimelineScale`

`TimelineScale` centralise la transformation du temps en position
horizontale logique.

Conceptuellement :

``` text
date_to_x(date)
x_to_date(x)
```

La transformation inverse pourra servir à déterminer la date
correspondant à la position du pointeur.

## 23.4 Géométrie verticale

Le `LayoutEngine` utilise les rangs de `TraversalResult`.

Conceptuellement :

``` text
y = top_margin + rank × row_height
```

Les conjoints occupent leur propre ligne conformément à R008.

Le nœud de mariage est placé verticalement entre les deux barres de vie
conformément à G004.

## 23.5 Objets de placement

Le `TimelineLayout` contient des objets de placement et non des objets
Gramps.

Exemples :

``` text
PersonPlacement
RelationshipNodePlacement
RemarriageSegmentPlacement
BranchReferencePlacement
DiagnosticPlacement
```

Un `PersonPlacement` peut conceptuellement contenir :

``` text
person_handle
x_start
x_end
y
generation
role
label
```

`role` distingue notamment `DESCENDANT` et `SPOUSE`.

Le `Renderer` applique ainsi les conventions graphiques sans recalculer
la généalogie.

------------------------------------------------------------------------

# 24. Rendu et transformation d'affichage

## 24.1 `ViewportTransform`

La vue interactive utilise une transformation d'affichage.

Conceptuellement :

``` text
screen_x = logical_x × zoom + offset_x
screen_y = logical_y × zoom + offset_y
```

`ViewportTransform` contient notamment :

``` text
zoom
offset_x
offset_y
```

Le `TimelineLayout` reste inchangé lorsque ces valeurs changent.

## 24.2 Renderer commun

Le renderer reçoit :

``` text
TimelineLayout
RenderOptions
DrawingContext
```

`DrawingContext` expose les primitives graphiques nécessaires :

``` text
draw_line
draw_circle
draw_rounded_rectangle
draw_text
```

Le renderer demande des opérations graphiques sans dépendre directement
du format final.

## 24.3 Cohérence des exports

SVG, PDF et PNG utilisent le même `TimelineLayout` et les mêmes règles
de rendu.

Les différences entre supports sont limitées aux contraintes techniques
du format.

Cette architecture met en œuvre G010.

------------------------------------------------------------------------

# 25. Intégration dans Gramps

## 25.1 Responsabilité de la vue

La vue Gramps gère :

-   la personne racine active ;
-   le lancement de la génération ;
-   l'affichage ;
-   le zoom ;
-   le déplacement ;
-   les actions d'export ;
-   l'ouverture éventuelle d'une fiche Gramps.

Elle ne contient aucune logique d'inférence ou de DFS.

## 25.2 Modification de la base

Lorsque Gramps signale une modification susceptible d'affecter la
timeline, le résultat calculé est invalidé.

La génération suivante reconstruit le modèle à partir de Gramps.

Dans une première version, le moteur ne tente pas de mettre à jour
partiellement le graphe interne objet par objet.

Cette décision privilégie la simplicité, le déterminisme et la
vérifiabilité.

Une stratégie incrémentale ne sera étudiée que si des mesures de
performance la rendent nécessaire.

## 25.3 Navigation vers Gramps

Les objets de placement conservent indirectement le handle de leur objet
Gramps source.

La vue pourra ultérieurement :

-   ouvrir une personne ;
-   ouvrir une famille ;
-   centrer la timeline sur une personne.

Le cœur du moteur ne déclenche jamais lui-même ces actions.

------------------------------------------------------------------------

# 26. Organisation proposée du code

``` text
src/
└── DescendantsTimeline/
    ├── gramps/
    │   └── data_adapter.py
    ├── model/
    │   ├── genealogy.py
    │   ├── timeline.py
    │   ├── temporal.py
    │   └── diagnostics.py
    ├── builders/
    │   └── descendance_builder.py
    ├── inference/
    │   ├── engine.py
    │   ├── rules/
    │   │   ├── base.py
    │   │   └── birth_order.py
    │   └── certainty.py
    ├── traversal/
    │   └── descendance_traversal.py
    ├── layout/
    │   ├── engine.py
    │   ├── scale.py
    │   └── placements.py
    ├── rendering/
    │   ├── renderer.py
    │   ├── context.py
    │   └── options.py
    ├── export/
    │   ├── svg.py
    │   ├── pdf.py
    │   └── png.py
    ├── ui/
    │   └── gramps_view.py
    └── engine.py
```

Cette structure est une proposition architecturale.

Les noms exacts des classes et modules seront stabilisés dans
`04_API.md`.

------------------------------------------------------------------------

# 27. Règles de dépendance

Le package `model` constitue le noyau le plus indépendant.

Les dépendances suivantes sont notamment interdites :

``` text
model ────────────X► Gramps
model ────────────X► UI
inference ────────X► rendering
traversal ────────X► GTK
layout ───────────X► Gramps
rendering ────────X► base Gramps
```

Cette règle protège la séparation des responsabilités.

------------------------------------------------------------------------

# 28. Testabilité architecturale

Le cœur du moteur doit pouvoir être testé avec des données créées
entièrement en mémoire.

Un test peut construire :

``` text
PersonNode A
PersonNode B
FamilyNode F
```

sans lancer Gramps.

Il peut vérifier séparément :

-   le graphe de descendance ;
-   les contraintes temporelles ;
-   l'ordre DFS ;
-   le layout.

Exemple pour L007 :

``` text
Enfants Gramps : [I010, I007, I015]

Ordre attendu :
I010
I007
I015
```

Exemple pour E005 :

``` text
1786
?
1792
```

Résultat attendu :

``` text
minimum = 1786
maximum = 1792
justification contient E005
```

Cette architecture prépare directement `07_TestCases.md`.

------------------------------------------------------------------------

# 29. Décisions à formaliser dans `03_Algorithms.md`

Les sujets suivants relèvent désormais des algorithmes :

1.  définition exacte d'une branche de descendance pour R010 et P007 ;
2.  pseudo-code complet du DFS ;
3.  gestion des unions entre deux descendants ;
4.  détection d'une branche déjà développée ;
5.  ordre des familles d'une même personne ;
6.  création et propagation des contraintes temporelles ;
7.  intersection des intervalles ;
8.  choix d'une valeur représentative ;
9.  calcul du niveau de certitude ;
10. traitement des dates Gramps partielles et approximatives ;
11. calcul des bornes temporelles globales ;
12. calcul des segments de remariage ;
13. stratégie d'invalidation et de cache.

Ces décisions ne doivent pas apparaître implicitement dans le code.

------------------------------------------------------------------------

# 30. Conclusion architecturale

L'architecture sépare strictement :

``` text
données généalogiques
          │
          ▼
raisonnement temporel
          │
          ▼
ordre de représentation
          │
          ▼
géométrie
          │
          ▼
dessin
```

Cette séparation garantit que :

-   les données Gramps restent intactes ;
-   les inférences restent explicables ;
-   le parcours reste déterministe ;
-   le layout reste indépendant du zoom ;
-   le rendu reste indépendant du calcul ;
-   les règles d'inférence peuvent être enrichies ;
-   les composants principaux peuvent être testés séparément.

La prochaine étape de conception est `03_Algorithms.md`, qui formalisera
les mécanismes précis sans remettre en cause les responsabilités
définies dans l'architecture.

*Ce document décrit l'architecture logique du projet. Les algorithmes détaillés, notamment le DFS, l'identification des branches déjà représentées et la résolution des contraintes temporelles, sont décrits dans `03_Algorithms.md`.*
