# Gramps Descendants Timeline

## Algorithmes — Partie 3 : calcul du `LayoutEngine`

**Version :** 0.3  
**Statut :** Brouillon algorithmique  
**Document cible :** `03_Algorithms.md`

---

# Table des matières

45. Objet de cette partie
46. Entrées et sorties du `LayoutEngine`
47. Principes de placement
48. Détermination des bornes temporelles
49. `TimelineScale`
50. Valeurs temporelles de placement
51. Axe vertical et rangs logiques
52. Placement des personnes
53. Placement des conjoints
54. Placement des nœuds de mariage
55. Placement des remariages
56. Dates inconnues non estimables
57. Références de branches déjà représentées
58. Diagnostics graphiques
59. Dimensions globales du layout
60. Zoom, déplacement et viewport
61. Pseudo-code général
62. Exemple complet
63. Invariants du layout
64. Complexité
65. Points à tester
66. Décisions reportées

---

# 45. Objet de cette partie

Cette partie décrit l'algorithme du `LayoutEngine`.

Le moteur répond à la question :

> **Comment transformer un ordre logique de personnes et de familles en une géométrie stable, déterministe et indépendante du support d'affichage ?**

Le `LayoutEngine` reçoit des données déjà consolidées.

Il ne :

- lit pas directement Gramps ;
- ne calcule pas la descendance ;
- ne produit pas d'inférences temporelles ;
- ne choisit pas l'ordre des personnes ;
- ne dessine pas.

Il transforme :

```text
TimelineModel
        +
TraversalResult
        │
        ▼
TimelineLayout
```

Cette partie met notamment en œuvre **L001 à L011**, **G001 à G012**, **P001 à P007** et **C001 à C014**.

---

# 46. Entrées et sorties du `LayoutEngine`

## 46.1 Entrées

Le moteur reçoit :

```text
TimelineModel
TraversalResult
LayoutOptions
```

`TimelineModel` fournit les personnes, les familles, les dates connues, les résultats d'inférence, les générations et les rôles généalogiques.

`TraversalResult` fournit l'ordre logique des lignes, les rôles `PERSON`, `SPOUSE`, `BRANCH_REFERENCE`, les références vers les branches principales et les diagnostics de parcours.

`LayoutOptions` fournit notamment :

```text
row_height
top_margin
bottom_margin
left_margin
right_margin
units_per_time
bar_height
marriage_node_radius
```

## 46.2 Sortie

Le moteur retourne un `TimelineLayout`.

```text
TimelineLayout
    time_bounds
    scale
    width
    height
    person_placements
    relationship_node_placements
    remarriage_segments
    branch_reference_placements
    diagnostic_placements
```

Le résultat ne dépend ni du zoom ni de la taille de la fenêtre.

---

# 47. Principes de placement

## LAY-P001 — Séparer les axes

L'axe horizontal dépend du temps.

L'axe vertical dépend de l'ordre logique produit par le DFS.

```text
temps ─────────────► X

rang logique
      │
      ▼
      Y
```

## LAY-P002 — Ne pas réinterpréter le parcours

Le `LayoutEngine` ne modifie jamais l'ordre de `TraversalResult`.

## LAY-P003 — Utiliser des coordonnées logiques

Les coordonnées appartiennent à un espace logique propre à la timeline et ne sont pas exprimées directement en pixels.

## LAY-P004 — Distinguer information temporelle et nécessité graphique

Une valeur utilisée uniquement pour l'affichage ne devient jamais une information temporelle.

Une `display_value` ne peut jamais être réinjectée dans le moteur d'inférence.

## LAY-P005 — Déterminisme

À modèle, parcours et options identiques, le `TimelineLayout` est identique.

---

# 48. Détermination des bornes temporelles

## 48.1 Objectif

Le moteur détermine :

```text
timeline_min
timeline_max
```

## 48.2 Valeurs prises en compte

Sont prises en compte :

- les naissances connues ;
- les décès connus ;
- les mariages connus ;
- les valeurs représentatives issues de l'inférence ;
- les bornes d'intervalles exploitables ;
- la date courante pour les personnes vivantes.

Les valeurs purement graphiques créées par le layout ne servent pas à définir les bornes temporelles de référence.

## 48.3 Calcul

```text
timeline_min = minimum de toutes les bornes utilisables
timeline_max = maximum de toutes les bornes utilisables
```

Puis le moteur ajoute une marge temporelle définie dans `LayoutOptions`.

## 48.4 Cas sans aucune date exploitable

Si aucune date exploitable n'existe :

```text
timeline_min = None
timeline_max = None
```

Le moteur bascule vers un mode de placement conventionnel, signalé comme non chronologique.

---

# 49. `TimelineScale`

## 49.1 Rôle

`TimelineScale` convertit une valeur temporelle en position horizontale logique.

```text
date_to_x(date)
x_to_date(x)
```

## 49.2 Transformation linéaire

Première proposition :

```text
x = left_margin + (date - timeline_min) × units_per_time
```

L'unité temporelle interne exacte sera alignée sur la précision des dates Gramps.

## 49.3 Transformation inverse

`x_to_date(x)` pourra notamment servir à afficher la date sous le pointeur.

---

# 50. Valeurs temporelles de placement

## 50.1 Ordre de priorité

Pour placer un événement, le moteur cherche :

```text
1. representative_value issue de Gramps ou de l'inférence
2. display_value produite par le layout
3. absence de position temporelle précise
```

## 50.2 `representative_value`

Elle appartient à `TemporalValue` et possède une signification temporelle documentée.

## 50.3 `display_value`

Elle appartient au résultat de placement.

Elle est créée uniquement lorsqu'aucune `representative_value` n'est disponible mais qu'un objet doit être dessiné.

```text
DisplayTemporalPosition
    display_value
    placement_reason
```

Exemples :

```text
UNKNOWN_BIRTH
UNKNOWN_DEATH
UNKNOWN_MARRIAGE
NO_TEMPORAL_DATA
```

## 50.4 Interdiction de réutilisation

Une `display_value` :

- ne devient jamais une donnée du `TimelineModel` ;
- ne modifie jamais un `TemporalValue` ;
- ne produit jamais une `TemporalConstraint` ;
- ne peut jamais augmenter un niveau de certitude.

---

# 51. Axe vertical et rangs logiques

Chaque élément de `TraversalResult` possède un rang logique.

```text
y = top_margin + rank × row_height
```

Le rang reste stable lors d'un zoom ou d'un redimensionnement.

`row_height` doit permettre l'affichage de la barre de vie, du nom, des dates et du nœud de mariage.

---

# 52. Placement des personnes

## 52.1 Début de la barre

```text
x_start = date_to_x(birth.representative_value)
```

Si aucune valeur représentative n'existe, une `display_value` peut être utilisée selon la section 56.

## 52.2 Fin de la barre

La fin dépend du décès, de la date courante si la personne est explicitement vivante, ou d'une `display_value`.

## 52.3 Cohérence

Le moteur vérifie :

```text
x_start <= x_end
```

Sinon, il associe un diagnostic au placement sans corriger silencieusement les données.

## 52.4 Placement logique

```text
PersonPlacement
    person_handle
    role
    generation
    x_start
    x_end
    y
    birth_origin
    death_origin
    diagnostics
```

---

# 53. Placement des conjoints

`SPOUSE` est un rôle de représentation indépendant du genre.

Le conjoint occupe une ligne logique propre issue de `TraversalResult`.

Le `Renderer` appliquera la couleur grise conformément à **G003**.

---

# 54. Placement des nœuds de mariage

## 54.1 Conditions de création

Un nœud de mariage est créé uniquement si :

- la famille comporte deux individus ;
- une valeur temporelle de placement existe pour la relation.

Une famille avec un seul individu ne produit aucun nœud conformément à **C013** et **C014**.

## 54.2 Position horizontale

```text
marriage_x = date_to_x(marriage_value)
```

`marriage_value` peut être une `representative_value` issue de Gramps ou de l'inférence.

Une `display_value` peut être utilisée uniquement pour l'affichage et reste marquée comme telle.

## 54.3 Position verticale

```text
marriage_y =
    milieu entre
    le bord inférieur de la barre du descendant
    et
    le bord supérieur de la barre du conjoint
```

Conceptuellement :

```text
marriage_y = (descendant_bottom + spouse_top) / 2
```

## 54.4 Placement logique

```text
RelationshipNodePlacement
    family_handle
    x
    y
    temporal_origin
    evidence_status
    is_display_only
```

---

# 55. Placement des remariages

Les nœuds des mariages successifs d'une même personne sont reliés par un segment vertical.

Le moteur utilise l'ordre des familles défini par **L009**.

```text
ordered_families(person)
```

Pour deux nœuds successifs, il produit :

```text
RemarriageSegmentPlacement
    person_handle
    x
    y_start
    y_end
```

La coordonnée `x` correspond à la date du remariage avec le nouveau conjoint.

Aucun segment n'est créé lorsqu'il n'existe qu'un seul mariage.

---

# 56. Dates inconnues non estimables

## 56.1 Principe

Le `LayoutEngine` peut devoir placer un objet sans disposer d'une valeur temporelle représentative.

Il doit produire une position graphique sans inventer une date généalogique.

## 56.2 Contraintes

La stratégie doit :

- rester déterministe ;
- préserver l'ordre DFS ;
- éviter une incohérence visuelle manifeste ;
- marquer la valeur comme `display_only` ;
- ne jamais réinjecter cette valeur dans l'inférence.

## 56.3 Naissance inconnue

Première stratégie proposée :

```text
si décès connu:
    display_birth = décès - default_lifespan
sinon si mariage personnel connu:
    display_birth = mariage - default_marriage_age
sinon:
    display_birth = position conventionnelle liée à la génération
```

Ces valeurs sont uniquement graphiques.

## 56.4 Décès inconnu

```text
si naissance connue:
    display_death = naissance + default_lifespan
sinon:
    display_death = display_birth + default_lifespan
```

La barre pourra être stylisée pour signaler son caractère indéterminé.

## 56.5 Mariage inconnu

```text
si les deux conjoints ont des barres:
    display_marriage =
        point conventionnel appartenant
        à l'intersection visuelle de leurs barres
sinon:
    display_marriage =
        position conventionnelle proche du descendant
```

Cette valeur ne constitue pas une estimation temporelle.

## 56.6 Validation future

Les stratégies exactes seront validées sur des cas généalogiques réels.

---

# 57. Références de branches déjà représentées

`TraversalResult` fournit un `BRANCH_REFERENCE`.

Le moteur lui attribue une position logique.

```text
BranchReferencePlacement
    source_handle
    target_branch_key
    target_rank
    x
    y
```

Le texte final reste du ressort du renderer ou des options utilisateur.

---

# 58. Diagnostics graphiques

Le layout peut positionner des marqueurs pour :

- contradiction temporelle ;
- date non prouvée ;
- valeur purement graphique ;
- cycle généalogique ;
- donnée manquante importante.

Le `LayoutEngine` ne crée pas le diagnostic métier : il positionne un diagnostic déjà présent.

---

# 59. Dimensions globales du layout

## 59.1 Hauteur

```text
height =
    top_margin
    + number_of_rows × row_height
    + bottom_margin
```

## 59.2 Largeur

```text
width =
    left_margin
    + temporal_span × units_per_time
    + right_margin
```

## 59.3 Textes

La première version peut prévoir une marge fixe pour les libellés.

Une version ultérieure pourra mesurer précisément les textes.

---

# 60. Zoom, déplacement et viewport

Le zoom et le déplacement ne modifient pas `TimelineLayout`.

Ils modifient uniquement `ViewportTransform`.

```text
screen_x = logical_x × zoom + offset_x
screen_y = logical_y × zoom + offset_y
```

Les exports utilisent leur propre transformation tout en réutilisant le même layout.

---

# 61. Pseudo-code général

```text
function compute_layout(model, traversal, options):

    bounds = compute_time_bounds(model, options)
    scale = TimelineScale(bounds, options)

    person_placements = []
    relationship_nodes = []
    remarriage_segments = []
    branch_references = []
    diagnostics = []

    for row in traversal.rows:

        y = rank_to_y(row.rank, options)

        if row.type == PERSON or row.type == SPOUSE:

            placement = place_person(
                row,
                model,
                scale,
                y,
                options
            )

            person_placements.append(placement)

        else if row.type == BRANCH_REFERENCE:

            branch_references.append(
                place_branch_reference(
                    row,
                    y,
                    options
                )
            )

    for family in model.families:

        if family is represented:

            node = place_relationship_node(
                family,
                person_placements,
                scale,
                options
            )

            if node exists:
                relationship_nodes.append(node)

    remarriage_segments = build_remarriage_segments(
        model,
        relationship_nodes
    )

    width, height = compute_layout_size(
        scale,
        traversal,
        options
    )

    return TimelineLayout(
        bounds = bounds,
        scale = scale,
        width = width,
        height = height,
        person_placements = person_placements,
        relationship_nodes = relationship_nodes,
        remarriage_segments = remarriage_segments,
        branch_references = branch_references,
        diagnostics = diagnostics
    )
```

---

# 62. Exemple complet

Données :

```text
Jean
naissance : 1708
décès : 1791

Françoise
naissance : 1712
décès : 1763

mariage : 1735
```

Rangs :

```text
Jean       rank 0
Françoise  rank 1
```

Options :

```text
timeline_min = 1700
units_per_year = 10
left_margin = 100
row_height = 40
top_margin = 50
```

Calcul horizontal :

```text
Jean naissance:
x = 100 + (1708 - 1700) × 10 = 180

Jean décès:
x = 100 + (1791 - 1700) × 10 = 1010

Mariage:
x = 100 + (1735 - 1700) × 10 = 450
```

Calcul vertical :

```text
Jean:
y = 50 + 0 × 40 = 50

Françoise:
y = 50 + 1 × 40 = 90
```

Le nœud de mariage est placé à `x = 450` et verticalement entre les deux barres.

---

# 63. Invariants du layout

## LAY-INV001

Le `LayoutEngine` ne modifie jamais `TimelineModel` ni `TraversalResult`.

## LAY-INV002

L'ordre vertical est identique à l'ordre de `TraversalResult`.

## LAY-INV003

Une même date produit la même coordonnée horizontale partout dans le layout.

## LAY-INV004

Le zoom ne modifie jamais le `TimelineLayout`.

## LAY-INV005

Une `display_value` ne peut jamais être utilisée par une `InferenceRule`.

## LAY-INV006

Une famille avec un seul individu ne produit aucun nœud de mariage.

## LAY-INV007

Un nœud de mariage est placé verticalement entre les barres des deux conjoints.

## LAY-INV008

Les conjoints conservent leur rôle `SPOUSE` indépendamment de leur genre.

## LAY-INV009

Une contradiction temporelle n'est jamais corrigée silencieusement par inversion des coordonnées.

## LAY-INV010

À entrées et options identiques, le layout est identique.

---

# 64. Complexité

Le calcul parcourt principalement les lignes logiques, les personnes représentées, les familles représentées et les références de branches.

L'objectif est une complexité proche de :

```text
O(R + P + F)
```

où :

```text
R = nombre de lignes logiques
P = nombre de placements de personnes
F = nombre de familles représentées
```

Les recherches fréquentes utilisent des index par handle.

---

# 65. Points à tester

Les tests devront couvrir au minimum :

1. personne seule avec dates connues ;
2. personne seule sans date ;
3. couple avec mariage connu ;
4. couple avec mariage inféré ;
5. couple avec mariage inconnu non estimable ;
6. famille monoparentale ;
7. personne vivante ;
8. naissance inconnue avec décès connu ;
9. décès inconnu avec naissance connue ;
10. naissance et décès inconnus ;
11. date Gramps calculée affichable mais non utilisable comme preuve ;
12. intervalle Gramps documenté ;
13. remariage unique ;
14. plusieurs remariages ;
15. absence de remariage ;
16. mêmes dates alignées verticalement ;
17. référence de branche ;
18. diagnostic temporel ;
19. zoom sans recalcul ;
20. export utilisant le même layout ;
21. stabilité sur deux exécutions ;
22. contradiction naissance-décès ;
23. dates inconnues avec `display_value` ;
24. vérification que `display_value` ne modifie pas l'inférence ;
25. très grande étendue temporelle ;
26. aucune date exploitable dans toute la descendance.

---

# 66. Décisions reportées

Les points suivants restent à préciser :

- unité temporelle interne exacte ;
- gestion précise des calendriers ;
- marge temporelle par défaut ;
- stratégie définitive de `display_value` ;
- style graphique des dates inconnues ;
- mesure exacte des textes ;
- traitement d'une barre de vie entièrement inconnue ;
- représentation visuelle des intervalles temporels ;
- comportement lorsque deux mariages successifs ont la même date ;
- position exacte du texte des références de branche ;
- interaction entre diagnostics et layout.

---

# Conclusion de la partie 3

Le `LayoutEngine` ne décide ni de la généalogie ni de la vérité temporelle.

Il transforme des informations déjà établies en une géométrie cohérente.

```text
TimelineModel
        +
TraversalResult
        │
        ▼
coordonnées logiques
        │
        ▼
TimelineLayout
        │
        ▼
Renderer
```

Son principe fondamental peut être résumé ainsi :

> **Le temps détermine l'axe horizontal, le DFS détermine l'axe vertical et toute valeur créée uniquement pour l'affichage reste strictement séparée du raisonnement généalogique.**
