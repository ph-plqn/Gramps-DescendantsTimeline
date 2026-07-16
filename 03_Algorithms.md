# Gramps Descendants Timeline

## Algorithmes — Partie 1 : parcours déterministe de la descendance

**Version :** 0.1  
**Statut :** Brouillon algorithmique  
**Document cible :** `03_Algorithms.md`

---

# Table des matières

1. Objet du document
2. Principes algorithmiques
3. Données d'entrée du parcours
4. Graphe de descendance
5. Ordre des familles
6. Ordre des enfants
7. Parcours en profondeur
8. Production des lignes logiques
9. Unions entre descendants
10. Branche déjà développée
11. Références de branche
12. Protection contre les cycles
13. Déterminisme
14. Complexité
15. Pseudo-code complet
16. Exemples de parcours
17. Cas limites
18. Résultats produits
19. Invariants
20. Points à tester
21. Décisions reportées

---

# 1. Objet du document

Le présent document décrit les algorithmes utilisés par **Gramps Descendants Timeline**.

Il répond à la question :

> **Comment les composants définis dans `02_Architecture.md` accomplissent-ils précisément leurs responsabilités ?**

Les spécifications fonctionnelles définissent le résultat attendu.

L'architecture définit les composants et leurs frontières.

Le présent document définit les mécanismes de calcul.

Cette première partie traite du parcours déterministe de la descendance.

Elle formalise notamment :

- le parcours en profondeur défini par **L006** ;
- le respect de l'ordre Gramps des enfants défini par **L007** ;
- l'ordre des familles défini par **L009** ;
- l'unicité de représentation des descendances définie par **R010** ;
- la réutilisation des branches définie par **P007**.

---

# 2. Principes algorithmiques

## ALG-P001 — Le parcours ne choisit pas la disposition

Le parcours de descendance ne cherche pas à optimiser visuellement le graphique.

Il ne :

- minimise pas les croisements ;
- n'équilibre pas les branches ;
- ne trie pas les personnes par date ;
- ne déplace pas une branche pour économiser de l'espace.

L'ordre vertical découle directement de la structure généalogique et des ordres fournis par Gramps.

---

## ALG-P002 — Le parcours est en profondeur

Une branche est développée jusqu'à son dernier descendant avant de revenir à la branche suivante.

Le parcours est donc un **Depth-First Search**, ou DFS.

---

## ALG-P003 — L'ordre Gramps est une information

L'ordre des enfants fourni par une famille Gramps est conservé.

L'ordre des familles d'une personne est conservé lorsque l'ordre chronologique ne peut pas être établi conformément à **L009**.

Le moteur n'utilise jamais le handle, le nom ou l'ordre alphabétique comme critère arbitraire de remplacement.

---

## ALG-P004 — Le modèle est un graphe

Le sous-ensemble généalogique parcouru n'est pas considéré comme un arbre strict.

Une personne ou une famille peut être atteinte par plusieurs chemins.

Le parcours doit donc mémoriser ce qui a déjà été développé.

---

## ALG-P005 — Une branche principale, des références secondaires

Une descendance possède une seule représentation développée.

Toute rencontre ultérieure produit une référence vers cette représentation.

---

# 3. Données d'entrée du parcours

`DescendanceTraversal` reçoit un `TimelineModel`.

Pour le parcours, les informations minimales sont :

```text
root_person_handle

persons
    handle
    generation
    family_handles

families
    handle
    parent_handles
    child_handles
    temporal_information
    gramps_order
```

Le parcours ne lit jamais directement la base Gramps.

Il ne lance aucune inférence temporelle.

Les informations temporelles nécessaires à l'ordre des familles ont déjà été consolidées dans le `TimelineModel`.

---

# 4. Graphe de descendance

## 4.1 Nœuds du graphe

Le graphe logique comporte deux catégories principales de nœuds :

```text
PersonNode
FamilyNode
```

Une personne est reliée aux familles auxquelles elle appartient.

Une famille est reliée :

- à zéro, un ou deux parents connus ;
- à zéro ou plusieurs enfants.

Conceptuellement :

```text
Person ──► Family ──► Child Person
```

---

## 4.2 Graphe biparti

Le modèle peut être vu comme un graphe biparti.

Les arêtes relient toujours :

```text
Person ↔ Family
```

et jamais directement :

```text
Person ↔ Person
```

Cette représentation correspond naturellement au modèle généalogique utilisé par le projet.

Exemple :

```text
Person A
    │
    ▼
Family F1
    │
    ├── Person B
    └── Person C
```

---

## 4.3 Pourquoi ne pas construire un arbre récursif ?

Une structure imbriquée comme :

```text
Person
  Family
    Child
      Family
        Child
```

semble simple.

Elle devient incorrecte lorsqu'une personne ou une famille est accessible par plusieurs branches.

Exemple :

```text
Branche 1 ──► I009
                 \
                  Family F77
                 /
Branche 2 ──► I077
```

Si la famille `F77` est copiée dans deux sous-arbres, sa descendance est dupliquée.

Le graphe interne conserve au contraire un seul `FamilyNode` pour `F77`.

---

# 5. Ordre des familles

## 5.1 Objectif

Lorsqu'une personne appartient à plusieurs familles, le DFS doit déterminer dans quel ordre ces familles sont développées.

La règle **L009** s'applique.

---

## 5.2 Comparaison temporelle de deux familles

Chaque famille peut disposer d'un `TemporalValue` pour son mariage.

Pour deux familles `A` et `B`, le moteur examine leurs intervalles temporels.

```text
A = [A.min, A.max]
B = [B.min, B.max]
```

Si :

```text
A.max < B.min
```

alors `A` précède certainement `B`.

Si :

```text
B.max < A.min
```

alors `B` précède certainement `A`.

Sinon, l'ordre chronologique entre les deux familles n'est pas démontré.

---

## 5.3 Ordre partiel

Les informations temporelles peuvent permettre certaines comparaisons sans permettre un tri chronologique total.

Exemple :

```text
F0 : 1780
F1 : 1770–1820
F2 : 1810
```

Nous ne pouvons pas déterminer avec certitude si `F1` précède ou suit `F0`.

Nous ne pouvons pas non plus déterminer avec certitude si `F1` précède `F2`.

Le moteur ne transforme pas la valeur représentative de `F1` en preuve chronologique.

---

## 5.4 Règle de repli sur l'ordre Gramps

Lorsque l'ordre chronologique complet et certain des familles ne peut pas être établi, le parcours conserve l'ordre des familles défini dans Gramps.

Cette décision évite de produire un ordre artificiel.

Conceptuellement :

```text
ordre_chronologique_certain(families) ?
        │
    ┌───┴───┐
    │       │
   oui     non
    │       │
    ▼       ▼
temps    ordre Gramps
```

---

## 5.5 Conséquence algorithmique

Le parcours reçoit une fonction conceptuelle :

```text
ordered_families(person)
```

Elle retourne une séquence stable.

Elle ne modifie jamais l'ordre stocké dans le modèle.

---

# 6. Ordre des enfants

## 6.1 Source de l'ordre

Pour une famille donnée, les enfants sont parcourus exactement dans l'ordre fourni par Gramps.

Conceptuellement :

```text
family.child_handles
```

est déjà une séquence ordonnée.

Le moteur ne la trie pas.

---

## 6.2 Cas des dates identiques

Deux enfants peuvent posséder la même date de naissance.

L'ordre Gramps reste la référence.

Le moteur n'utilise pas :

- le prénom ;
- le handle ;
- l'identifiant public ;
- l'ordre alphabétique.

---

## 6.3 Cas des dates inconnues

Une date inconnue ne modifie pas l'ordre du parcours.

L'inférence temporelle peut exploiter l'ordre des enfants.

Elle ne modifie jamais cet ordre.

Cette distinction est fondamentale :

```text
ordre généalogique Gramps
          │
          ├── utilisé par le DFS
          │
          └── utilisé comme information par l'inférence
```

Le moteur d'inférence observe l'ordre.

Il ne le réécrit pas.

---

# 7. Parcours en profondeur

## 7.1 Principe général

Le parcours commence par la personne racine.

Pour chaque famille de cette personne :

1. le conjoint nécessaire est ajouté à la représentation ;
2. les enfants sont visités dans l'ordre Gramps ;
3. pour chaque enfant, sa propre descendance est développée immédiatement ;
4. lorsque sa branche est terminée, le parcours revient à l'enfant suivant.

---

## 7.2 Exemple

Graphe :

```text
A
│
└── F1
    ├── B
    │   └── F2
    │       ├── D
    │       │   └── F4
    │       │       └── G
    │       └── E
    └── C
        └── F3
            └── F
```

Ordre DFS des descendants :

```text
A
B
D
G
E
C
F
```

Le parcours ne produit pas :

```text
A
B
C
D
E
F
G
```

Ce second ordre serait un parcours par niveau.

---

## 7.3 Appel récursif conceptuel

Le DFS peut être décrit récursivement :

```text
visit_person(person)

    représenter person

    families = ordered_families(person)

    pour chaque family dans families

        représenter le conjoint si nécessaire

        si la branche de family est déjà développée
            créer une référence
            continuer

        marquer la branche comme développée

        pour chaque child dans family.children
            visit_person(child)
```

Le pseudo-code détaillé est précisé en section 15.

---

# 8. Production des lignes logiques

## 8.1 Le DFS ne produit pas directement des coordonnées

Le résultat du parcours est une séquence de lignes logiques.

Exemple :

```text
0 PERSON I001
1 SPOUSE I002
2 PERSON I010
3 SPOUSE I011
4 PERSON I020
5 PERSON I021
6 BRANCH_REFERENCE F077
```

Le `LayoutEngine` convertira ensuite ces rangs en positions verticales.

Le rôle SPOUSE est indépendant du genre et désigne l'autre personne connue de la famille dans le contexte du descendant courant.

---

## 8.2 Types d'éléments de parcours

La première version prévoit au minimum :

```text
PERSON
SPOUSE
BRANCH_REFERENCE
```

D'autres types pourront être ajoutés si l'architecture du layout le nécessite.

Le type d'un élément décrit son rôle dans la représentation.

Il ne modifie pas l'identité généalogique de la personne.

Une même personne peut conceptuellement être rencontrée comme descendant puis ailleurs comme conjoint, sans devenir deux personnes distinctes dans le modèle.

---

## 8.3 Attribution du rang

Le rang logique est attribué au moment où l'élément est ajouté à la séquence.

Conceptuellement :

```text
rank = len(rows)
rows.append(element)
```

Le rang est donc une conséquence directe du DFS.

---

# 9. Unions entre descendants

## 9.1 Situation

Deux descendants de la personne racine peuvent former une famille.

Exemple :

```text
Racine
├── Branche A
│   └── I009
└── Branche B
    └── I077

I009 + I077 = F100
```

La famille `F100` est accessible par les deux branches.

---

## 9.2 Première rencontre

Lors de la première rencontre de `F100` :

```text
branche déjà développée ? non
```

Le moteur :

1. crée la représentation de la famille ;
2. développe ses enfants ;
3. développe leurs descendants ;
4. enregistre la branche comme développée.

---

## 9.3 Rencontre ultérieure

Lors de la seconde rencontre :

```text
branche déjà développée ? oui
```

Le moteur :

1. ne parcourt pas les enfants une seconde fois ;
2. ne duplique pas la descendance ;
3. crée un `BranchReference` ;
4. continue le DFS de la branche courante.

---

# 10. Branche déjà développée

## 10.1 Pourquoi `visited_persons` ne suffit pas

Un ensemble classique :

```text
visited_persons
```

est insuffisant.

Une personne déjà rencontrée peut devoir être affichée comme conjoint dans une autre partie de la représentation.

Interdire toute seconde rencontre d'une personne ferait perdre une relation généalogique utile.

---

## 10.2 Pourquoi `visited_families` est plus proche du besoin

La répétition de descendance apparaît lorsqu'une même famille productrice d'enfants est atteinte plusieurs fois.

La famille constitue donc un candidat naturel pour identifier une branche développée.

Conceptuellement :

```text
expanded_family_handles
```

Lorsqu'une famille est développée pour la première fois, son handle est ajouté au registre.

---

## 10.3 Définition provisoire d'une branche

Pour la première version de l'algorithme :

> **Une branche de descendance est la descendance développée à partir des enfants d'une famille donnée.**

La représentation principale d'une branche est donc associée au `FamilyNode` qui introduit cette liste d'enfants.

Cette définition rend la clé suivante naturelle :

```text
branch_key = family_handle
```

---

## 10.4 Limite de cette définition

Cette définition devra être vérifiée avec des cas généalogiques complexes.

Il faut notamment tester :

- plusieurs familles sans enfant ;
- une même personne descendante rencontrée par plusieurs chemins ;
- des relations familiales atypiques ;
- les familles monoparentales ;
- les éventuelles structures cycliques incohérentes.

Si les tests démontrent qu'un `family_handle` ne suffit pas à identifier une branche, la clé sera enrichie.

Cette décision est volontairement reportée aux tests algorithmiques.

---

# 11. Références de branche

## 11.1 Objet logique

Lorsqu'une branche a déjà été développée, le parcours produit un objet conceptuel :

```text
BranchReference
```

Il contient au minimum :

```text
source_family_handle
target_branch_key
target_first_rank
```

`target_first_rank` désigne le rang logique de la représentation principale.

---

## 11.2 Texte de référence

Le texte final n'est pas figé par l'algorithme.

Exemples possibles :

```text
Descendance déjà représentée plus haut
```

ou :

```text
Voir la descendance de Jean MARTIN
```

ou :

```text
Voir ligne 42
```

Le `TraversalResult` fournit l'information structurée.

Le `Renderer` et les options utilisateur déterminent la formulation visuelle.

---

## 11.3 Référence interactive

Dans la vue Gramps, une référence pourra ultérieurement devenir interactive.

Un clic pourra :

- déplacer la vue vers la représentation principale ;
- sélectionner la première personne de la branche ;
- mettre temporairement la branche en évidence.

Cette fonctionnalité n'affecte pas l'algorithme DFS.

---

# 12. Protection contre les cycles

## 12.1 Pourquoi prévoir ce cas ?

Une descendance généalogique cohérente est acyclique.

Cependant, une base peut contenir une incohérence de saisie.

Exemple conceptuel impossible :

```text
A descend de B
B descend de C
C descend de A
```

Un DFS récursif naïf ne se terminerait jamais.

---

## 12.2 Pile de parcours active

Le moteur conserve les personnes et familles actuellement présentes dans la branche récursive active.

Conceptuellement :

```text
active_person_path
active_family_path
```

Avant d'entrer dans un nœud, le moteur vérifie s'il est déjà dans le chemin actif.

---

## 12.3 Détection

Si une personne ou une famille apparaît à nouveau dans son propre chemin actif :

```text
cycle détecté
```

Le moteur :

1. arrête le développement de cette branche ;
2. crée un diagnostic ;
3. ne modifie pas les données Gramps ;
4. poursuit les autres branches lorsque cela est possible.

---

## 12.4 Différence entre branche répétée et cycle

Ces deux situations ne doivent jamais être confondues.

### Branche répétée

```text
deux chemins différents
        │
        ▼
même famille
```

Traitement :

```text
BranchReference
```

### Cycle

```text
un chemin revient sur lui-même
```

Traitement :

```text
Diagnostic
```

---

# 13. Déterminisme

Le résultat du parcours dépend uniquement :

- de la personne racine ;
- du `TimelineModel` ;
- de l'ordre des familles déterminé par L009 ;
- de l'ordre Gramps des enfants ;
- des règles de détection des branches déjà développées.

Il ne dépend pas :

- de l'ordre d'un dictionnaire non défini ;
- du hasard ;
- de la largeur de la fenêtre ;
- du zoom ;
- du support de rendu.

Les collections dont l'ordre influence le résultat doivent être des séquences ordonnées explicites.

---

# 14. Complexité

## 14.1 Objectif

Le parcours doit éviter le recalcul des branches conformément à **P003** et **P007**.

---

## 14.2 Coût du DFS

Chaque personne et chaque famille utile est examinée un nombre limité de fois.

Avec des registres basés sur des ensembles ou dictionnaires indexés par handle, les tests d'appartenance sont conçus pour être rapides.

L'objectif est une complexité proche de :

```text
O(V + E)
```

où :

```text
V = nombre de nœuds du graphe
E = nombre de relations parcourues
```

Pour le projet, cela signifie approximativement :

```text
personnes + familles + liens
```

---

## 14.3 Pourquoi ne pas promettre strictement O(n) ici ?

Le graphe comporte plusieurs catégories d'objets et de relations.

La notation `O(V + E)` décrit plus précisément le DFS d'un graphe.

Dans une base généalogique normale, le nombre de liens reste proportionnel au nombre d'objets utiles.

Le comportement attendu reste donc pratiquement linéaire.

---

# 15. Pseudo-code complet

Le pseudo-code suivant décrit la première version de référence.

```text
function traverse(model):

    state.rows = []
    state.expanded_families = {}
    state.active_person_path = []
    state.active_family_path = []

    visit_person(model.root_person, DESCENDANT, state)

    return TraversalResult(
        rows = state.rows,
        expanded_families = state.expanded_families
    )
```

Visite d'une personne :

```text
function visit_person(person, role, state):

    if person.handle in state.active_person_path:
        add_cycle_diagnostic(person)
        return

    push person.handle into state.active_person_path

    add_person_row(person, role, state)

    families = ordered_families(person)

    for family in families:
        visit_family(person, family, state)

    pop person.handle from state.active_person_path
```

Visite d'une famille :

```text
function visit_family(current_person, family, state):

    if family.handle in state.active_family_path:
        add_cycle_diagnostic(family)
        return

    push family.handle into state.active_family_path

    spouse = family.other_parent(current_person)

    if spouse exists:
        add_spouse_row(spouse, family, state)

    if family.handle in state.expanded_families:

        target = state.expanded_families[family.handle]

        add_branch_reference(
            family = family,
            target = target,
            state = state
        )

        pop family.handle from state.active_family_path
        return

    state.expanded_families[family.handle] = current_branch_position(state)

    for child_handle in family.child_handles:

        child = model.persons[child_handle]

        visit_person(
            person = child,
            role = DESCENDANT,
            state = state
        )

    pop family.handle from state.active_family_path
```

Ce pseudo-code constitue un point de départ.

Il devra être confronté aux cas de test avant l'implémentation Python.

---

# 16. Exemples de parcours

## 16.1 Famille simple

```text
A + X
├── B
└── C
```

Résultat logique :

```text
0 A
1 X        [conjoint]
2 B
3 C
```

---

## 16.2 Descendance profonde

```text
A + X
├── B + Y
│   ├── D + Z
│   │   └── G
│   └── E
└── C
```

Résultat :

```text
0 A
1 X
2 B
3 Y
4 D
5 Z
6 G
7 E
8 C
```

---

## 16.3 Deux familles

```text
A + X = F1
└── B

A + Y = F2
└── C
```

Si l'ordre retenu des familles est :

```text
F1
F2
```

alors :

```text
0 A
1 X
2 B
3 Y
4 C
```

---

## 16.4 Union entre descendants

```text
A
├── B
│   └── D
└── C
    └── E

D + E = F10
└── G
```

Première rencontre de `F10` :

```text
D
E
G
```

Seconde rencontre :

```text
E
D
↳ référence vers F10
```

La descendance de `G` n'est pas répétée.

---

# 17. Cas limites

## 17.1 Famille sans enfant

La famille peut produire une ligne de conjoint et un nœud de relation dans le futur layout.

Aucune récursion enfant n'est effectuée.

---

## 17.2 Famille avec un seul parent

Aucun conjoint fictif n'est ajouté.

Le parcours visite les enfants dans l'ordre Gramps.

Aucun nœud de mariage ne sera créé par le layout conformément à C013 et C014.

---

## 17.3 Personne sans famille

La personne reçoit une ligne.

La récursion se termine immédiatement.

---

## 17.4 Personne rencontrée comme conjoint avant sa branche descendante

La personne peut être affichée comme `SPOUSE`.

Lorsqu'elle est ensuite atteinte comme descendant par son chemin généalogique principal, sa branche peut être développée.

Le simple fait d'avoir affiché la personne comme conjoint ne marque pas sa descendance comme déjà développée.

---

## 17.5 Famille déjà développée mais conjoint différent dans le contexte

Le moteur se base sur l'identité de la famille.

Il crée une référence de branche au lieu de redévelopper ses enfants.

Les détails visuels de la relation restent du ressort du layout et du renderer.

---

# 18. Résultats produits

`DescendanceTraversal` retourne conceptuellement :

```text
TraversalResult
    rows
    branch_registry
    diagnostics
```

`rows` contient la séquence logique.

`branch_registry` associe une branche principale à sa première position.

`diagnostics` contient les anomalies de parcours, notamment les cycles.

Le résultat ne contient aucune coordonnée graphique.

---

# 19. Invariants

Les invariants suivants doivent être vrais après un parcours réussi.

## INV001

La première ligne représente la personne racine.

## INV002

L'ordre des enfants d'une famille est identique à l'ordre Gramps.

## INV003

Une branche développée ne l'est qu'une seule fois.

## INV004

Toute rencontre secondaire d'une branche développée produit une référence.

## INV005

Le parcours se termine même si le graphe contient un cycle incohérent.

## INV006

À modèle identique, la séquence de lignes est identique.

## INV007

Le parcours ne modifie jamais `TimelineModel`.

## INV008

Aucune coordonnée graphique n'est calculée par `DescendanceTraversal`.

---

# 20. Points à tester

Les tests du parcours devront couvrir au minimum :

1. personne racine seule ;
2. couple sans enfant ;
3. enfant unique ;
4. plusieurs enfants ;
5. trois générations ;
6. descendance profonde ;
7. ordre Gramps non chronologique des enfants ;
8. jumeaux ;
9. plusieurs familles d'une même personne ;
10. familles chronologiquement comparables ;
11. familles chronologiquement indéterminables ;
12. famille monoparentale ;
13. union entre cousins ;
14. même famille rencontrée deux fois ;
15. personne affichée d'abord comme conjoint puis comme descendant ;
16. cycle généalogique incohérent ;
17. grande profondeur de descendance ;
18. stabilité sur deux exécutions successives.

Ces scénarios seront détaillés dans `07_TestCases.md`.

---

# 21. Décisions reportées

Les questions suivantes restent volontairement ouvertes jusqu'à la rédaction des parties correspondantes de `03_Algorithms.md` :

- calcul exact des intervalles temporels ;
- résolution des contraintes ;
- valeur représentative d'une date estimée ;
- calcul du niveau de certitude ;
- règles initiales du moteur d'inférence ;
- calcul des bornes globales de la timeline ;
- placement horizontal des dates inconnues non estimables ;
- géométrie précise des segments de remariage ;
- texte et interaction des références de branche.

---

# Conclusion de la partie 1

Le parcours de descendance n'est pas un algorithme de mise en page.

Il construit un **ordre logique déterministe** à partir du graphe généalogique.

Son principe peut être résumé ainsi :

> **Développer entièrement la première branche, respecter l'ordre Gramps, ne jamais développer deux fois la même descendance et signaler toute rencontre secondaire par une référence.**

Le `LayoutEngine` utilisera ensuite cette séquence logique pour calculer les positions verticales.

La partie suivante de `03_Algorithms.md` décrira le moteur d'inférence temporelle : production des contraintes, résolution des intervalles, diagnostics et évaluation du niveau de certitude.

# Gramps Descendants Timeline

## Algorithmes --- Partie 2 : moteur d'inférence temporelle

**Version :** 0.2\
**Statut :** Brouillon algorithmique\
**Document cible :** `03_Algorithms.md`

------------------------------------------------------------------------

# Table des matières

22. Objet de cette partie
23. Principes du moteur d'inférence
24. Types de données temporelles
25. Règles d'inférence
26. Contraintes temporelles
27. Contraintes dures et contraintes souples
28. Groupes de preuves
29. Collecte des contraintes
30. Résolution des intervalles
31. Contradictions
32. Valeur représentative
33. Niveau de certitude
34. Évaluation de la certitude
35. Propagation des estimations
36. Prévention des boucles d'inférence
37. Explication des résultats
38. Règles initiales proposées
39. Pseudo-code général
40. Exemple complet
41. Invariants
42. Complexité
43. Points à tester
44. Décisions reportées

------------------------------------------------------------------------

# 22. Objet de cette partie

Cette partie décrit l'algorithme du `TemporalInferenceEngine`.

Le moteur répond à la question :

> **Que peut-on raisonnablement déduire à propos d'un événement temporel
> inconnu à partir des autres informations présentes dans la descendance
> ?**

Le moteur ne modifie jamais les données Gramps.

Il produit uniquement des informations temporaires en mémoire :

-   intervalles temporels ;
-   valeurs représentatives ;
-   contraintes ;
-   diagnostics ;
-   niveaux de certitude ;
-   explications.

Cette partie met notamment en œuvre **E003**, **E005**, **E006**,
**E007**, **P005**, **P006**, **C001**, **C002**, **C003**, **C008**,
**C009** et **C010**.

------------------------------------------------------------------------

# 23. Principes du moteur d'inférence

## INF-P001 --- Déduire avant d'estimer

Le moteur ne commence jamais par choisir une date.

Il commence par déterminer les contraintes applicables.

``` text
données connues
      │
      ▼
contraintes
      │
      ▼
intervalle possible
      │
      ▼
valeur représentative éventuelle
```

## INF-P002 --- Une estimation doit être explicable

Toute estimation conserve :

-   les règles utilisées ;
-   les objets sources ;
-   les contraintes produites ;
-   l'intervalle final ;
-   le niveau de certitude ;
-   les éventuels diagnostics.

Une estimation sans justification structurée est interdite.

## INF-P003 --- Les données Gramps restent prioritaires

Une date connue dans Gramps n'est jamais remplacée par une date estimée.

Le moteur peut toutefois détecter une incohérence entre cette date et
d'autres contraintes.

Dans ce cas :

``` text
date Gramps conservée
        +
diagnostic créé
```

## INF-P004 --- Les règles sont indépendantes

Chaque `InferenceRule` observe le modèle et produit des contraintes.

Une règle ne dépend pas du fonctionnement interne des autres règles.

Elle ne calcule pas le niveau de certitude final.

Elle ne choisit pas directement la date estimée.

## INF-P005 --- Les contraintes sont combinées centralement

Toutes les contraintes sont réunies par `TemporalInferenceEngine`.

La résolution est réalisée par un mécanisme commun.

Cette propriété garantit que l'ajout d'une nouvelle règle ne nécessite
pas la modification de toutes les règles existantes.

## INF-P006 --- Ne jamais masquer l'incertitude

Une valeur représentative sert au placement.

Elle ne transforme jamais un intervalle incertain en date certaine.

Exemple :

``` text
intervalle : 1786–1792
valeur représentative : 1789
certitude : Probable
```

Le moteur conserve toujours l'intervalle original.

------------------------------------------------------------------------

# 24. Types de données temporelles

## 24.1 Événements concernés

La première version du moteur traite au minimum :

``` text
BIRTH
DEATH
MARRIAGE
```

D'autres types d'événements pourront être ajoutés ultérieurement.

## 24.2 `TemporalTarget`

Une cible d'inférence identifie l'événement à estimer.

``` text
TemporalTarget
    object_handle
    event_type
```

Exemples :

``` text
(I0088, BIRTH)
(I0088, DEATH)
(F0032, MARRIAGE)
```

## 24.3 `TemporalValue`

Le moteur manipule un `TemporalValue`.

```text
TemporalValue
    source_value
    minimum
    maximum
    representative_value
    value_origin
    source_quality
    evidence_status
    certainty
```

Chaque champ répond à une question différente :

| Champ | Question |
|---|---|
| `value_origin` | D'où vient la valeur temporelle elle-même ? |
| `source_quality` | Comment Gramps qualifie-t-il la date source ? |
| `evidence_status` | Le moteur peut-il utiliser cette valeur comme preuve ? |
| `minimum` / `maximum` | Quelles bornes temporelles sont exploitables ? |
| `representative_value` | Quelle valeur unique peut être utilisée lorsqu'un point temporel est nécessaire ? |
| `certainty` | Quel niveau de certitude le moteur attribue-t-il au résultat ? |

`value_origin` indique l'origine de la valeur temporelle elle-même et non l'origine des données utilisées par le moteur d'inférence.

`value_origin` vaut notamment :

```text
GRAMPS
INFERRED
UNKNOWN
```

`source_quality` conserve, lorsqu'elle existe, la qualité de la date définie dans Gramps.

Les valeurs exactes seront alignées sur les constantes de Gramps lors de l'implémentation.

Le moteur distingue notamment les dates marquées comme calculées.

`evidence_status` indique si la valeur peut être utilisée comme source directe d'une contrainte temporelle.

Première proposition :

```text
EVIDENCE_USABLE
EVIDENCE_UNPROVEN
EVIDENCE_UNAVAILABLE
```

Ces trois valeurs signifient :

```text
EVIDENCE_USABLE
    → information exploitable comme preuve

EVIDENCE_UNPROVEN
    → information présente mais non admissible comme preuve

EVIDENCE_UNAVAILABLE
    → aucune information temporelle disponible
```

### Exemple 1 — Date Gramps exacte et utilisable

Jean possède une date de naissance saisie dans Gramps :

```text
Jean
naissance : 1786
```

Le moteur construit :

```text
TemporalValue
    source_value = 1786
    minimum = 1786
    maximum = 1786
    representative_value = 1786
    value_origin = GRAMPS
    source_quality = [qualité Gramps]
    evidence_status = EVIDENCE_USABLE
```

Cela signifie :

> La valeur temporelle 1786 provient directement d'une donnée Gramps et peut être utilisée comme source d'une contrainte temporelle.

### Exemple 2 — Intervalle documenté dans Gramps

Une personne part en mer le 10/02/1947.

Son corps est retrouvé le 28/02/1947.

L'acte de décès indique :

```text
décédé entre le 10/02/1947 et le 28/02/1947
```

Le moteur construit :

```text
TemporalValue
    source_value = [intervalle Gramps]
    minimum = 10/02/1947
    maximum = 28/02/1947
    representative_value = 19/02/1947
    value_origin = GRAMPS
    source_quality = [qualité Gramps]
    evidence_status = EVIDENCE_USABLE
```

La date exacte du décès reste inconnue.

Cependant, les bornes inférieure et supérieure proviennent d'une information documentée et peuvent être utilisées par le moteur d'inférence.

Cette situation illustre une distinction importante :

```text
date exacte inconnue
        ≠
information temporelle non prouvée
```

Ici :

```text
date exacte        → inconnue
borne inférieure   → utilisable
borne supérieure   → utilisable
```

### Exemple 3 — Date construite par le moteur

Jacques n'a aucune date de naissance dans Gramps.

Mais :

```text
Jean      1786
Jacques   ?
François  1792
```

Le moteur déduit :

```text
Jacques : 1786–1792
```

Donc :

```text
TemporalValue
    source_value = None
    minimum = 1786
    maximum = 1792
    representative_value = 1789
    value_origin = INFERRED
    source_quality = None
    evidence_status = [déterminé par les règles de provenance]
```

Les preuves utilisées par le moteur proviennent des données exploitables du modèle.

Mais la valeur `1786–1792` n'existe pas dans Gramps.

Elle a été construite par le moteur d'inférence.

C'est pourquoi :

```text
value_origin = INFERRED
```

### Exemple 4 — Date calculée dans Gramps mais non justifiée pour le moteur

Supposons :

```text
Jean
naissance : 1786
qualité Gramps : CALCULATED
```

La valeur existe réellement dans Gramps.

Le moteur construit :

```text
TemporalValue
    source_value = 1786
    minimum = 1786
    maximum = 1786
    representative_value = 1786
    value_origin = GRAMPS
    source_quality = CALCULATED
    evidence_status = EVIDENCE_UNPROVEN
```

Cela signifie :

> La valeur temporelle 1786 provient directement d'une donnée Gramps.

> Cette date est marquée comme calculée dans Gramps.

> Le moteur ne dispose pas d'une justification structurée permettant d'utiliser cette valeur comme preuve directe dans une inférence.

La valeur peut être affichée sur la timeline.

Elle ne peut pas être utilisée comme source directe d'une `TemporalConstraint`.

### Exemple 5 — Valeur inconnue

Supposons :

```text
Pierre
naissance : inconnue
```

et qu'aucune règle ne permette de produire une contrainte exploitable.

```text
TemporalValue
    source_value = None
    minimum = None
    maximum = None
    representative_value = None
    value_origin = UNKNOWN
    source_quality = None
    evidence_status = EVIDENCE_UNAVAILABLE
```

Cela signifie :

> Le moteur ne dispose d'aucune valeur temporelle utilisable pour cet événement.

### Conséquence pour le moteur d'inférence

Une `InferenceRule` ne peut utiliser comme source directe d'une contrainte qu'une valeur dont :

```text
evidence_status = EVIDENCE_USABLE
```

Une valeur `EVIDENCE_UNPROVEN` peut rester visible dans les explications ou sur la timeline.

Elle ne participe pas directement à la résolution de l'intervalle d'une autre cible.

## 24.4 Intervalle fermé

Dans la première version, les intervalles sont considérés comme fermés.

``` text
[min, max]
```

signifie :

``` text
min <= date <= max
```

Une date exacte est donc un intervalle de largeur nulle :

``` text
[1786, 1786]
```
## 24.5 Gestion des calendriers

```text
TemporalValue

    source_value
    source_calendar

    normalized_minimum
    normalized_maximum

    representative_value

    value_origin
```

source_value : valeur telle qu'elle est enregistrée dans Gramps.

source_calendar : calendrier utilisé par cette valeur (grégorien, julien, républicain, etc.).

normalized_minimum : borne inférieure convertie dans le référentiel temporel interne du moteur.

normalized_maximum : borne supérieure convertie dans ce même référentiel.

representative_value : valeur représentative calculée uniquement à partir des valeurs normalisées.

Le moteur distingue systématiquement la représentation documentaire d'une date et sa représentation normalisée.

La représentation documentaire est conservée afin de garantir la traçabilité des preuves.

La représentation normalisée est utilisée exclusivement pour les calculs temporels, les comparaisons, les contraintes et le positionnement sur la timeline.

Exemple :
Acte

Date :
18 pluviôse an VIII

↓

TemporalValue

source_value =
18 pluviôse an VIII

source_calendar =
Calendrier républicain

normalized_minimum =
1800-02-07

normalized_maximum =
1800-02-07

representative_value =
1800-02-07

------------------------------------------------------------------------

# 25. Règles d'inférence

## 25.1 Interface conceptuelle

Une règle d'inférence respecte conceptuellement le contrat suivant :

``` text
InferenceRule
    rule_id
    strength
    constraint_kind
    evidence_group

    applies_to(target, context)
    produce_constraints(target, context)
```

## 25.2 `rule_id`

Chaque règle possède un identifiant permanent.

Exemples :

``` text
IR-BIRTH-ORDER
IR-PARENT-MARRIAGE
IR-PERSON-MARRIAGE
IR-LIFE-INTERVAL
```

Les identifiants ne sont jamais réutilisés.

## 25.3 `strength`

La force d'une règle est qualitative.

Première proposition :

``` text
VERY_STRONG
STRONG
MEDIUM
WEAK
```

Cette force intervient dans l'évaluation de la certitude.

Elle ne transforme pas une contrainte souple en contrainte dure.

## 25.4 `constraint_kind`

Une règle peut produire :

``` text
HARD
SOFT
```

`HARD` limite l'intervalle admissible.

`SOFT` décrit un indice compatible avec une hypothèse, mais insuffisant
pour exclure définitivement une date.

## 25.5 `evidence_group`

Chaque règle appartient à un groupe de preuves.

Premiers groupes envisagés :

``` text
SIBLING_ORDER
PARENT_RELATIONSHIP
PERSON_LIFE_EVENTS
BIOLOGICAL_PLAUSIBILITY
GRAMPS_DATE_STRUCTURE
HISTORICAL_STATISTICS
```

Le groupe est utilisé par `CertaintyEvaluator`.

Il permet d'éviter de compter plusieurs fois comme indépendantes des
preuves issues du même raisonnement.

------------------------------------------------------------------------

# 26. Contraintes temporelles

## 26.1 Structure

Une `TemporalConstraint` contient conceptuellement :

``` text
TemporalConstraint
    target
    minimum
    maximum
    kind
    strength
    evidence_group
    rule_id
    source_handles
    explanation
```

Une borne peut être absente.

``` text
minimum = 1786
maximum = None
```

signifie :

``` text
date >= 1786
```

## 26.2 Contrainte inférieure

> L'enfant est situé après son frère aîné né en 1786.

Résultat :

``` text
minimum = 1786
maximum = None
```

## 26.3 Contrainte supérieure

> L'enfant est situé avant son frère cadet né en 1792.

Résultat :

``` text
minimum = None
maximum = 1792
```

## 26.4 Contrainte d'intervalle

Une règle peut produire directement un intervalle.

Il est cependant souvent préférable de conserver séparément les
contraintes ayant produit chaque borne.

Cela améliore l'explication.

------------------------------------------------------------------------

# 27. Contraintes dures et contraintes souples

## 27.1 Contrainte dure

Une contrainte dure réduit l'intervalle admissible.

Exemple :

``` text
ordre Gramps :
Jean
Jacques
François
```

avec :

``` text
Jean né en 1786
François né en 1792
```

Pour Jacques :

``` text
birth >= 1786
birth <= 1792
```

## 27.2 Contrainte souple

> Un enfant naît probablement après le mariage de ses parents.

Cette observation n'est pas universelle.

Elle peut produire une contrainte `SOFT`.

Elle influence la certitude ou la valeur préférée.

Elle ne doit pas nécessairement exclure les dates antérieures au
mariage.

## 27.3 Règle de priorité

Les contraintes dures définissent d'abord l'intervalle admissible.

Les contraintes souples sont ensuite évaluées.

``` text
HARD constraints
       │
       ▼
intervalle admissible
       │
       ▼
SOFT constraints
       │
       ▼
évaluation de plausibilité
```

------------------------------------------------------------------------

# 28. Groupes de preuves

## 28.1 Pourquoi regrouper les preuves ?

Plusieurs contraintes peuvent dépendre du même fait source.

Le moteur ne doit pas les considérer automatiquement comme plusieurs
preuves indépendantes.

## 28.2 Indépendance approximative

Le moteur ne cherche pas à démontrer une indépendance statistique.

Il utilise une catégorisation explicable.

Exemple :

``` text
SIBLING_ORDER
PARENT_RELATIONSHIP
PERSON_LIFE_EVENTS
```

Trois groupes différents peuvent renforcer davantage une estimation
qu'un grand nombre de contraintes issues d'un seul groupe.

## 28.3 Conséquence pour la certitude

`CertaintyEvaluator` prend en compte :

-   la force des règles ;
-   le type HARD ou SOFT ;
-   la certitude des sources ;
-   le nombre de groupes de preuves compatibles ;
-   la largeur de l'intervalle final ;
-   la présence de contradictions.

------------------------------------------------------------------------

# 29. Collecte des contraintes

Le moteur identifie les cibles temporelles utiles puis applique chaque
règle active.

``` text
constraints = []

for rule in active_rules:

    if rule.applies_to(target, context):

        constraints += rule.produce_constraints(
            target,
            context
        )
```

Chaque contrainte produite est validée.

Une contrainte invalide techniquement est rejetée et journalisée.

Exemples :

``` text
minimum > maximum
source inconnue
rule_id absent
target inexistant
```

------------------------------------------------------------------------

# 30. Résolution des intervalles

## 30.1 Bornes initiales

La résolution commence conceptuellement sans borne minimale ni maximale.

## 30.2 Application des contraintes dures

Pour chaque contrainte dure :

``` text
si constraint.minimum existe:
    minimum = max(minimum, constraint.minimum)

si constraint.maximum existe:
    maximum = min(maximum, constraint.maximum)
```

## 30.3 Résultat compatible

Si :

``` text
minimum <= maximum
```

l'intervalle est compatible.

Exemple :

``` text
>= 1786
<= 1792
```

donne :

``` text
[1786, 1792]
```

## 30.4 Résultat ponctuel

Si :

``` text
minimum == maximum
```

le raisonnement converge vers une valeur unique.

Cela ne signifie pas nécessairement que la date est `CERTAIN`.

La certitude dépend aussi de la qualité des contraintes.

------------------------------------------------------------------------

# 31. Contradictions

Si :

``` text
minimum > maximum
```

les contraintes sont incompatibles.

Le moteur :

1.  ne produit aucune estimation ;
2.  crée un `InferenceDiagnostic` ;
3.  conserve les contraintes responsables ;
4.  produit un résultat de type `CONTRADICTION`.

La première version peut conserver toutes les contraintes actives.

Une version future pourra rechercher un sous-ensemble minimal
contradictoire.

------------------------------------------------------------------------

# 32. Valeur représentative

## 32.1 Rôle

La timeline a besoin d'une position horizontale unique.

Un intervalle ne fournit pas directement un point unique.

Le moteur produit donc une `representative_value`.

## 32.2 Valeur moyenne

Pour un intervalle fini :

``` text
[min, max]
```

la première stratégie proposée est :

``` text
representative = moyenne(min, max)
```

Exemple :

``` text
[1786, 1792] -> 1789
```

## 32.3 Valeur représentative non certaine

La valeur moyenne n'est pas présentée comme la vraie date.

Elle est une position représentative de l'intervalle connu.

## 32.4 Intervalle ouvert d'un côté

Si une seule borne existe, le moteur ne choisit pas arbitrairement une
moyenne.

En l'absence de stratégie justifiable :

``` text
representative_value = None
```

------------------------------------------------------------------------

# 33. Niveau de certitude

Le projet utilise :

``` text
Certaine
Très probable
Probable
Possible
Indéterminée
```

Valeurs internes envisagées :

``` text
CERTAIN
VERY_PROBABLE
PROBABLE
POSSIBLE
UNDETERMINED
```

Le moteur ne doit pas afficher un faux pourcentage de probabilité.

Un score numérique interne peut être utilisé pour classer les résultats.

`CERTAIN` est réservé en priorité aux dates présentes dans Gramps
lorsque le moteur ne détecte pas de contradiction bloquante.

Une date issue uniquement d'inférences ne devient pas automatiquement
`CERTAIN`, même si l'intervalle final est ponctuel.

------------------------------------------------------------------------

# 34. Évaluation de la certitude

## 34.1 `CertaintyEvaluator`

La certitude est calculée par un composant séparé.

Il reçoit :

``` text
target
resolved_interval
constraints
source_values
diagnostics
```

Il retourne un `CertaintyLevel`.

## 34.2 Facteurs pris en compte

``` text
F1 — origine Gramps ou inférence
F2 — force des règles
F3 — contraintes HARD ou SOFT
F4 — certitude des données sources
F5 — groupes de preuves indépendants
F6 — largeur de l'intervalle
F7 — contradictions ou diagnostics
```

## 34.3 Score interne

Une première implémentation pourra utiliser un score interne.

``` text
score = base_score
      + support_strength
      + evidence_diversity
      + interval_precision
      - uncertainty_penalties
      - contradiction_penalties
```

Les coefficients exacts ne sont pas définis ici.

Ils devront être documentés, testés et modifiables sans changer les
règles d'inférence.

## 34.4 Classification qualitative

Le score interne est converti en niveau qualitatif.

Les seuils seront définis ultérieurement.

## 34.5 Explication de la certitude

Exemple :

``` text
Certitude : Très probable

Motifs :
- deux contraintes fortes encadrent la date ;
- l'intervalle est limité à six ans ;
- trois groupes de preuves indépendants sont compatibles ;
- aucune contradiction n'a été détectée.
```

------------------------------------------------------------------------

# 35. Propagation des estimations

## 35.1 Pourquoi propager ?

Une date estimée peut permettre de produire de nouvelles contraintes.

## 35.2 Risque

Une estimation faible peut produire une autre estimation.

Puis cette seconde estimation peut renforcer artificiellement la
première.

Ce phénomène créerait une boucle de confirmation.

## 35.3 Règle de provenance

Chaque `TemporalConstraint` conserve la chaîne de provenance des données
utilisées.

Une contrainte dérivée d'une estimation conserve cette dépendance.

## 35.4 Propagation contrôlée

Une estimation peut produire de nouvelles contraintes, mais sa certitude
source est propagée et ne peut pas être oubliée.

Une règle utilisant une source `POSSIBLE` ne doit pas produire un
résultat `VERY_PROBABLE` uniquement par répétition du raisonnement.

------------------------------------------------------------------------

# 36. Prévention des boucles d'inférence

## 36.1 Exemple de boucle

``` text
A estimé grâce à B
B estimé grâce à A
```

## 36.2 Graphe de dépendance

Le moteur conserve conceptuellement les dépendances entre résultats.

Avant d'utiliser une estimation comme source, il peut vérifier qu'elle
ne dépend pas déjà de la cible courante.

## 36.3 Cycle d'inférence

Si un cycle est détecté :

``` text
A -> B -> C -> A
```

la nouvelle contrainte n'est pas utilisée comme preuve indépendante.

## 36.4 Stabilisation

Une stratégie possible est un calcul par itérations jusqu'à
stabilisation.

``` text
pass 1
pass 2
pass 3
...
aucun résultat modifié
        │
        ▼
stabilisation
```

La stratégie exacte sera choisie après les premiers prototypes et tests.

Le moteur doit imposer une limite d'itérations pour garantir la
terminaison.

------------------------------------------------------------------------

# 37. Explication des résultats

L'utilisateur ne doit pas recevoir uniquement :

``` text
1789
```

mais pouvoir obtenir :

``` text
Naissance estimée : 1789
Intervalle : 1786–1792
Certitude : Très probable
```

Exemple de justification :

``` text
1. Jean DUPONT précède Jacques dans l'ordre Gramps.
2. Jean DUPONT est né en 1786.
3. François DUPONT suit Jacques dans l'ordre Gramps.
4. François DUPONT est né en 1792.
5. La naissance de Jacques est donc encadrée entre 1786 et 1792.
6. La valeur représentative retenue est 1789.
```

Le texte explicatif doit être généré à partir d'objets structurés.

Conceptuellement :

``` text
TemporalConstraint
        │
        ▼
InferenceExplanationBuilder
        │
        ▼
texte utilisateur
```

Cette séparation facilite la traduction, les tests et les changements de
formulation.

------------------------------------------------------------------------

# 38. Règles initiales proposées

## 38.1 `BirthOrderRule`

**Cible :** naissance.\
**Groupe :** `SIBLING_ORDER`.

Utilise l'ordre des enfants Gramps.

Cherche le précédent et le suivant disposant de bornes temporelles
exploitables.

Produit des contraintes inférieures et supérieures.

## 38.2 `ParentMarriageRule`

**Cible :** naissance d'un enfant.\
**Groupe :** `PARENT_RELATIONSHIP`.

Le mariage des parents peut fournir une indication temporelle.

Cette règle doit probablement être `SOFT`.

## 38.3 `PersonalMarriageRule`

**Cible :** naissance.\
**Groupe :** `PERSON_LIFE_EVENTS`.

Le mariage personnel connu d'une personne fournit une borne supérieure
plausible pour sa naissance.

La nature HARD ou SOFT devra être définie avec prudence.

## 38.4 `LifeIntervalRule`

**Cible :** décès.\
**Groupe :** `PERSON_LIFE_EVENTS`.

Une date de décès ne peut pas logiquement précéder une date de naissance
connue dans un modèle cohérent.

Cette règle sert aussi au diagnostic d'incohérence.

## 38.5 `BiologicalParentalAgeRule`

**Cible :** naissance du parent ou de l'enfant selon le contexte.\
**Groupe :** `BIOLOGICAL_PLAUSIBILITY`.

Utilise notamment :

-   le genre ;
-   le rôle parental ;
-   la nature de la relation parent-enfant lorsque disponible.

Cette règle ne doit pas appliquer une contrainte biologique à une
relation adoptive.

La première version devrait probablement produire des contraintes
souples ou des diagnostics de plausibilité plutôt que des bornes dures.

------------------------------------------------------------------------

# 39. Pseudo-code général

``` text
function infer(model, active_rules):

    report = InferenceReport()
    targets = collect_temporal_targets(model)

    for target in targets:

        constraints = []

        for rule in active_rules:

            if rule.applies_to(target, model, report):

                produced = rule.produce_constraints(
                    target,
                    model,
                    report
                )

                constraints += validate(produced)

        result = resolve_target(
            target,
            constraints,
            model
        )

        report.add(result)

    propagate_until_stable(
        model,
        report,
        active_rules
    )

    evaluate_certainty(report)

    return report
```

Résolution d'une cible :

``` text
function resolve_target(target, constraints, model):

    if target has known Gramps date:

        return KnownTemporalResult(
            source = Gramps value,
            diagnostics = check_consistency(...)
        )

    hard_constraints = constraints where kind == HARD
    soft_constraints = constraints where kind == SOFT

    minimum = no lower bound
    maximum = no upper bound

    for constraint in hard_constraints:
        tighten minimum
        tighten maximum

    if minimum > maximum:

        return ContradictionResult(
            constraints = constraints
        )

    representative = choose_representative_value(
        minimum,
        maximum,
        soft_constraints
    )

    return InferenceResult(
        minimum = minimum,
        maximum = maximum,
        representative_value = representative,
        constraints = constraints
    )
```

------------------------------------------------------------------------

# 40. Exemple complet

Famille Gramps :

``` text
1. Jean      né en 1786
2. Jacques   naissance inconnue
3. François  né en 1792
```

Cible :

``` text
(Jacques, BIRTH)
```

`BirthOrderRule` produit :

``` text
C1
minimum = 1786
kind = HARD
strength = STRONG
group = SIBLING_ORDER
source = Jean

C2
maximum = 1792
kind = HARD
strength = STRONG
group = SIBLING_ORDER
source = François
```

Résolution :

``` text
[1786, 1792]
```

Valeur représentative :

``` text
1789
```

Le `CertaintyEvaluator` observe :

``` text
2 contraintes HARD
2 contraintes STRONG
1 groupe de preuves
intervalle de 6 ans
aucune contradiction
```

Il produit un niveau qualitatif selon les seuils qui seront définis
ultérieurement.

------------------------------------------------------------------------

# 41. Invariants

## INF-INV001

Une date connue dans Gramps n'est jamais remplacée par une estimation.

## INF-INV002

Toute estimation possède au moins une contrainte justifiante.

## INF-INV003

Toute contrainte conserve son `rule_id`.

## INF-INV004

Toute contrainte conserve ses sources.

## INF-INV005

Un intervalle contradictoire ne produit aucune valeur estimée.

## INF-INV006

La valeur représentative ne supprime jamais l'intervalle source.

## INF-INV007

Le niveau de certitude est calculé séparément des règles d'inférence.

## INF-INV008

Une estimation propagée conserve sa provenance.

## INF-INV009

Le moteur ne modifie jamais le `TimelineModel` source ni la base Gramps.

## INF-INV010

À données et règles identiques, le rapport d'inférence est identique.

## INF-INV011

Seules les valeurs dont `evidence_status = EVIDENCE_USABLE` peuvent être utilisées comme source directe d'une `TemporalConstraint`.

## INF-INV012

Une valeur Gramps non admissible comme preuve peut être affichée, mais ne participe pas directement à la résolution de l'intervalle d'une autre cible.

## INF-INV013

Toute comparaison temporelle utilise exclusivement les valeurs normalisées.

INF-INV014

La normalisation ne remplace jamais la valeur documentaire ni son calendrier d'origine.

------------------------------------------------------------------------

# 42. Complexité

La collecte initiale applique un ensemble fini de règles à un ensemble
de cibles.

Conceptuellement :

``` text
O(T × R)
```

où :

``` text
T = nombre de cibles temporelles
R = nombre de règles actives
```

Dans la première version, `R` reste faible.

Les règles doivent éviter de reparcourir l'ensemble du graphe pour
chaque cible.

Le modèle doit fournir des accès directs aux informations utiles.

La propagation peut nécessiter plusieurs passes.

Le nombre de passes doit être borné.

Les performances réelles seront mesurées avant toute optimisation plus
complexe.

------------------------------------------------------------------------

# 43. Points à tester

Les tests devront couvrir au minimum :

1.  aucune contrainte disponible ;
2.  une borne inférieure ;
3.  une borne supérieure ;
4.  deux bornes compatibles ;
5.  intervalle ponctuel ;
6.  contraintes contradictoires ;
7.  date Gramps connue et cohérente ;
8.  date Gramps connue mais incohérente ;
9.  ordre des enfants avec deux dates connues ;
10. plusieurs enfants inconnus consécutifs ;
11. contraintes HARD et SOFT mélangées ;
12. plusieurs contraintes d'un même groupe de preuves ;
13. plusieurs groupes de preuves ;
14. source elle-même estimée ;
15. propagation sur deux niveaux ;
16. cycle d'inférence ;
17. stabilisation ;
18. valeur représentative d'un intervalle fini ;
19. intervalle avec une seule borne ;
20. déterminisme du résultat ;
21. niveau de certitude explicable ;
22. relation adoptive et règle biologique non applicable ;
23. genre inconnu ;
24. diagnostic de plausibilité biologique ;
25. ajout d'une nouvelle `InferenceRule` sans modification du moteur
    central.

Ces scénarios seront détaillés dans `07_TestCases.md`.

------------------------------------------------------------------------

# 44. Décisions reportées

Les points suivants restent à formaliser après validation de cette
architecture algorithmique :

-   valeurs exactes de `RuleStrength` ;
-   coefficients éventuels du score interne ;
-   seuils de `CertaintyLevel` ;
-   définition exacte de la certitude d'une source ;
-   influence du niveau de confiance Gramps ;
-   stratégie finale de propagation ;
-   nombre maximal de passes ;
-   sélection de la valeur représentative en présence de contraintes
    SOFT ;
-   règles biologiques initiales ;
-   prise en compte des calendriers et de la précision journalière ;
-   traitement des événements Gramps `before`, `after`, `about` et
    `between`.

Ces décisions seront prises sur des cas généalogiques concrets et des
tests documentés.

------------------------------------------------------------------------

# Conclusion de la partie 2

Le moteur d'inférence ne produit pas une date « magique ».

Il construit un raisonnement.

``` text
faits Gramps
      │
      ▼
règles applicables
      │
      ▼
contraintes
      │
      ▼
intervalle
      │
      ▼
valeur représentative
      │
      ▼
niveau de certitude
      │
      ▼
explication
```

Le cœur du moteur peut être résumé ainsi :

> **Déduire ce qui est permis par les données, conserver la provenance
> du raisonnement, ne jamais masquer l'incertitude et expliquer le
> résultat au généalogiste.**

La partie suivante de `03_Algorithms.md` décrira le calcul du layout :
bornes de la timeline, transformation temporelle, rangs verticaux,
barres de vie, nœuds de mariage et segments de remariage.

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

Toutes les coordonnées horizontales sont calculées à partir des valeurs temporelles normalisées.

date Gramps

	↓

conversion calendrier

	↓

date normalisée

	↓

TimelineScale

	↓

coordonnée X

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

Une display_value est toujours calculée dans le référentiel temporel normalisé.

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


## LAY-INV011

Toutes les positions horizontales proviennent exclusivement des valeurs temporelles normalisées.

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

---

# Table des matières

67. Objet de cette partie
68. Principes du rendu
69. Entrées du `Renderer`
70. `DrawingContext`
71. Transformation des coordonnées
72. Ordre de dessin
73. Rendu des barres de vie
74. Rendu des nœuds de mariage
75. Rendu des segments de remariage
76. Rendu des références de branche
77. Rendu des diagnostics
78. Rendu des textes
79. Gestion du zoom
80. Gestion du déplacement
81. Zone visible et culling
82. Exports SVG, PDF et PNG
83. Invalidation et recalculs
84. Cache
85. Pseudo-code général
86. Exemple de cycle d'affichage
87. Invariants du rendu
88. Complexité
89. Points à tester
90. Décisions reportées

---

# 67. Objet de cette partie

Cette partie décrit les algorithmes de rendu et de mise à jour de l'affichage.

Le `Renderer` répond à la question :

> **Comment transformer un `TimelineLayout` déjà calculé en primitives graphiques cohérentes, quel que soit le support de sortie ?**

Le moteur de rendu ne prend aucune décision généalogique ou temporelle.

Il reçoit :

```text
TimelineLayout
RenderOptions
DrawingContext
ViewportTransform
```

et produit un affichage.

Cette partie décrit également le zoom, le déplacement de la vue, la sélection des objets visibles, les exports, l'invalidation et le cache.

---

# 68. Principes du rendu

## REN-P001 — Le rendu ne recalcule pas le layout

Le `Renderer` ne modifie jamais les positions calculées.

Il ne réordonne pas les lignes, ne déplace pas un nœud pour éviter un chevauchement et ne recalcule aucune date.

## REN-P002 — Même layout, mêmes conventions graphiques

La vue interactive et les exports utilisent le même `TimelineLayout`.

Les différences de support ne doivent pas modifier la structure de la représentation.

## REN-P003 — Transformation séparée

Les coordonnées logiques du layout sont transformées en coordonnées du support au dernier moment.

```text
coordonnées logiques
        │
        ▼
ViewportTransform ou ExportTransform
        │
        ▼
coordonnées du support
```

## REN-P004 — Le style ne modifie pas le sens

Une couleur, une épaisseur de trait ou une police peuvent changer.

La signification généalogique ne doit pas changer.

---

# 69. Entrées du `Renderer`

Le renderer reçoit conceptuellement :

```text
render(
    layout,
    drawing_context,
    render_options,
    transform
)
```

`layout` contient la géométrie.

`drawing_context` expose les primitives graphiques.

`render_options` contient les choix de style.

`transform` convertit les coordonnées logiques vers le support.

---

# 70. `DrawingContext`

## 70.1 Rôle

`DrawingContext` fournit une interface commune.

```text
draw_line(...)
draw_circle(...)
draw_rectangle(...)
draw_rounded_rectangle(...)
draw_text(...)
save_state()
restore_state()
clip(...)
```

## 70.2 Adaptateurs

Les implémentations peuvent être :

```text
GtkDrawingContext
SvgDrawingContext
PdfDrawingContext
PngDrawingContext
```

Le `Renderer` ne dépend pas directement du format final.

---

# 71. Transformation des coordonnées

## 71.1 Vue interactive

La vue interactive utilise deux facteurs de zoom indépendants :

```text
ViewportTransform
    zoom_x
    zoom_y
    offset_x
    offset_y
```

La transformation devient :

```text
screen_x = logical_x × zoom_x + offset_x
screen_y = logical_y × zoom_y + offset_y
```

Cette séparation reflète la différence de nature des deux axes :

```text
X = temps
Y = ordre logique du DFS
```

Elle permet deux modes complémentaires :

```text
Zoom A — zoom uniforme
    zoom_x et zoom_y sont modifiés ensemble

Zoom B — zoom temporel
    seul zoom_x est modifié
```

Le **Zoom A** sert à se positionner dans l'ensemble de la descendance et à afficher plus ou moins de lignes de vie.

Le **Zoom B** sert à examiner une période temporelle plus courte ou plus longue sans modifier le nombre de lignes visibles verticalement.

Convention proposée :

```text
molette
    → Zoom A

Ctrl + molette
    → Zoom B
```

La convention exacte dépendra des possibilités d'intégration dans l'interface Gramps.

## 71.2 Export

Un export peut utiliser :

```text
output_x = logical_x × export_scale + export_offset_x
output_y = logical_y × export_scale + export_offset_y
```

## 71.3 Taille des éléments

Deux politiques sont possibles :

```text
A. tout agrandir avec le zoom
B. agrandir la géométrie mais conserver certains textes lisibles
```

La première version privilégie une transformation cohérente et simple.

Les règles précises de taille de texte seront validées par l'usage.

---

# 72. Ordre de dessin

L'ordre de dessin influence la lisibilité.

Première proposition :

```text
1. fond
2. axe temporel et graduations
3. segments de remariage
4. barres de vie
5. nœuds de mariage
6. références de branche
7. diagnostics
8. textes
```

Les textes sont dessinés en dernier afin de rester lisibles.

---

# 73. Rendu des barres de vie

## 73.1 Descendant

La couleur dépend de la génération.

```text
generation -> theme color
```

## 73.2 Conjoint

Le rôle `SPOUSE` impose le style gris conformément à **G003**.

Le genre n'intervient pas dans le choix de la couleur.

## 73.3 Dates inconnues ou affichage conventionnel

Une barre utilisant une `display_value` peut recevoir un style spécifique.

Exemples possibles :

```text
trait interrompu
hachures
transparence
extrémité ouverte
```

Le style exact reste à valider.

## 73.4 Contradiction

Le renderer n'inverse pas une barre incohérente.

Il applique le placement fourni par le layout et peut dessiner un marqueur de diagnostic.

---

# 74. Rendu des nœuds de mariage

Chaque `RelationshipNodePlacement` produit un cercle.

Le cercle est dessiné aux coordonnées calculées par le `LayoutEngine`.

Le renderer ne recalcule ni la date ni le milieu vertical.

Une convention visuelle future pourra distinguer une date Gramps, une date inférée et une position purement graphique.

---

# 75. Rendu des segments de remariage

Chaque `RemarriageSegmentPlacement` produit un segment vertical.

```text
draw_line(
    x,
    y_start,
    x,
    y_end
)
```

Aucun segment n'est dessiné pour une personne ne possédant qu'une seule union représentée.

---

# 76. Rendu des références de branche

## 76.1 Texte

Une référence peut être affichée sous une forme telle que :

```text
↳ Descendance déjà représentée plus haut
```

ou :

```text
↳ Voir la descendance de Jean MARTIN
```

Le texte final peut être généré à partir des données structurées.

## 76.2 Interactivité

Dans la vue interactive, la référence pourra exposer une zone cliquable.

```text
BranchReferenceHitBox
```

Un clic pourra déclencher :

```text
center_on(target_rank)
```

Cette fonction appartient à la vue, pas au moteur de rendu.

---

# 77. Rendu des diagnostics

Les diagnostics peuvent être signalés par une icône, un symbole, un surlignage ou une infobulle.

Le renderer reçoit un diagnostic déjà calculé.

Il ne décide pas si une donnée est incohérente.

---

# 78. Rendu des textes

## 78.1 Contenu

Les textes peuvent contenir :

- nom ;
- prénom ;
- années de naissance et de décès ;
- indication d'estimation ;
- niveau de certitude ;
- référence de branche.

## 78.2 Mesure

Avant de dessiner un texte, le contexte graphique peut mesurer :

```text
text_width
text_height
```

Ces mesures servent uniquement au rendu.

Elles ne doivent pas modifier l'ordre généalogique.

## 78.3 Troncature

Si l'espace visible est insuffisant, la vue peut tronquer temporairement un texte.

L'export complet doit privilégier l'affichage intégral.

---

# 79. Gestion du zoom

## 79.1 Principe général

Le zoom modifie uniquement `ViewportTransform`.

Le `TimelineLayout` reste inchangé.

Deux modes de zoom sont proposés.

## 79.2 Zoom A — zoom uniforme

Le Zoom A modifie simultanément les deux axes.

```text
zoom_x = zoom_x × factor
zoom_y = zoom_y × factor
```

Il sert principalement à se positionner dans l'arbre, afficher davantage de lignes de vie ou agrandir une zone de la descendance.

Convention proposée :

```text
molette
```

## 79.3 Zoom B — zoom temporel

Le Zoom B modifie uniquement l'axe horizontal.

```text
zoom_x = zoom_x × factor
zoom_y inchangé
```

Il sert principalement à examiner une période courte, comparer plus précisément des dates et observer des écarts temporels faibles sans modifier le nombre de lignes de vie visibles.

Convention proposée :

```text
Ctrl + molette
```

Le Zoom B exploite directement la sémantique de la représentation :

```text
X = temps
Y = ordre DFS
```

## 79.4 Zoom centré sur le pointeur

Les deux modes doivent conserver sous le pointeur le point logique observé.

### Zoom A

Avant le zoom :

```text
logical_x = (mouse_x - offset_x) / zoom_x
logical_y = (mouse_y - offset_y) / zoom_y
```

Après modification de `zoom_x` et `zoom_y` :

```text
offset_x = mouse_x - logical_x × zoom_x
offset_y = mouse_y - logical_y × zoom_y
```

### Zoom B

Avant le zoom temporel :

```text
logical_x = (mouse_x - offset_x) / zoom_x
```

Après modification de `zoom_x` uniquement :

```text
offset_x = mouse_x - logical_x × zoom_x
```

Dans ce cas :

```text
zoom_y
offset_y
```

restent inchangés.

La ligne de vie observée conserve donc exactement sa position verticale.

## 79.5 Bornes de zoom

Les valeurs de zoom doivent être limitées :

```text
min_zoom_x <= zoom_x <= max_zoom_x
min_zoom_y <= zoom_y <= max_zoom_y
```

Les valeurs exactes seront définies lors des essais d'interface.

---

# 80. Gestion du déplacement

Le déplacement modifie :

```text
offset_x
offset_y
```

Conceptuellement :

```text
offset_x += delta_x
offset_y += delta_y
```

Aucun recalcul du layout n'est nécessaire.

---

# 81. Zone visible et culling

## 81.1 Objectif

Une très grande timeline peut contenir des milliers d'objets.

Il est inutile de dessiner un objet entièrement hors de la zone visible.

## 81.2 Test de visibilité

Chaque placement possède une boîte logique ou graphique.

```text
if object_bounds intersects viewport_bounds:
    draw object
```

## 81.3 Culling

Le fait d'ignorer temporairement les objets hors écran est appelé `culling`.

Le culling améliore les performances sans modifier le layout, l'ordre ou le modèle.

---

# 82. Exports SVG, PDF et PNG

## 82.1 Principe commun

Tous les exports utilisent :

```text
TimelineLayout
Renderer
RenderOptions
```

Seul le `DrawingContext` change.

## 82.2 SVG

Le SVG conserve une représentation vectorielle.

Il est particulièrement adapté au zoom, à l'édition ultérieure et à l'impression.

## 82.3 PDF

Le PDF utilise le même layout.

Une grande timeline peut nécessiter une grande page ou plusieurs pages.

La stratégie de pagination reste à définir.

## 82.4 PNG

Le PNG nécessite une résolution raster.

Le moteur doit vérifier les dimensions maximales raisonnables avant de créer une image très grande.

---

# 83. Invalidation et recalculs

## 83.1 Principe

Chaque changement invalide uniquement les résultats qui en dépendent.

## 83.2 Niveaux d'invalidation

Première proposition :

```text
RENDER_ONLY
LAYOUT
TRAVERSAL
INFERENCE
MODEL
```

## 83.3 Exemples

### Zoom

```text
RENDER_ONLY
```

### Déplacement

```text
RENDER_ONLY
```

### Changement de couleur

```text
RENDER_ONLY
```

### Changement de hauteur de ligne

```text
LAYOUT
```

### Changement de personne racine

```text
MODEL
```

### Modification d'une règle d'inférence

```text
INFERENCE
```

### Modification des données Gramps

```text
MODEL
```

## 83.4 Propagation

Une invalidation d'un niveau entraîne celle des niveaux dépendants.

```text
MODEL
  ↓
INFERENCE
  ↓
TRAVERSAL
  ↓
LAYOUT
  ↓
RENDER
```

---

# 84. Cache

## 84.1 Objectif

Les résultats coûteux peuvent être conservés tant que leurs entrées ne changent pas.

## 84.2 Objets pouvant être mis en cache

```text
RawGenealogyData
DescendanceGraph
InferenceReport
TimelineModel
TraversalResult
TimelineLayout
```

## 84.3 Clé de cache

Conceptuellement, une clé peut dépendre de :

```text
root_person_handle
database_revision
inference_rules_version
layout_options
```

La stratégie exacte dépendra des mécanismes disponibles dans Gramps.

## 84.4 Première version

La première version peut utiliser une stratégie simple : un résultat courant en mémoire, invalidé lorsqu'une modification pertinente est détectée.

Il n'est pas nécessaire de construire immédiatement un cache complexe.

---

# 85. Pseudo-code général

```text
function render_view(state):

    if state.model_invalid:
        rebuild_model()

    if state.inference_invalid:
        recompute_inference()

    if state.traversal_invalid:
        recompute_traversal()

    if state.layout_invalid:
        recompute_layout()

    renderer.render(
        layout = state.layout,
        drawing_context = state.context,
        render_options = state.render_options,
        transform = state.viewport_transform
    )
```

Rendu :

```text
function render(layout, context, options, transform):

    visible_bounds = inverse_transform(
        context.viewport_bounds
    )

    draw_background()
    draw_timeline_axis()

    for segment in layout.remarriage_segments:
        if visible(segment):
            draw_remarriage_segment(segment)

    for person in layout.person_placements:
        if visible(person):
            draw_person_bar(person)

    for node in layout.relationship_nodes:
        if visible(node):
            draw_relationship_node(node)

    for reference in layout.branch_references:
        if visible(reference):
            draw_branch_reference(reference)

    for diagnostic in layout.diagnostics:
        if visible(diagnostic):
            draw_diagnostic(diagnostic)

    draw_texts()
```

---

# 86. Exemple de cycle d'affichage

## Étape 1 — Sélection d'une nouvelle racine

```text
MODEL invalid
```

Le moteur recalcule :

```text
RawGenealogyData
DescendanceGraph
InferenceReport
TimelineModel
TraversalResult
TimelineLayout
```

Puis dessine.

## Étape 2 — Zoom

```text
RENDER_ONLY
```

Le moteur conserve `TimelineLayout` et modifie seulement `ViewportTransform`.

## Étape 3 — Modification d'une couleur

```text
RENDER_ONLY
```

Aucun calcul généalogique n'est relancé.

## Étape 4 — Modification de la base Gramps

```text
MODEL invalid
```

Toute la chaîne dépendante est recalculée.

---

# 87. Invariants du rendu

## REN-INV001

Le renderer ne modifie jamais `TimelineLayout`.

## REN-INV002

Le zoom ne déclenche pas de recalcul du layout.

## REN-INV003

Le déplacement ne déclenche pas de recalcul du layout.

## REN-INV004

Le même `TimelineLayout` peut être utilisé pour l'écran et les exports.

## REN-INV005

Le culling ne modifie pas le contenu du layout.

## REN-INV006

Le renderer ne produit aucune inférence.

## REN-INV007

Le renderer ne change jamais l'ordre vertical des objets.

## REN-INV008

Une modification de style n'invalide pas le modèle généalogique.

## REN-INV009

Une référence interactive ne modifie pas le graphe.

## REN-INV010

À layout, options et transformation identiques, le rendu est déterministe.

## REN-INV011

Un zoom temporel modifie uniquement la transformation horizontale et ne modifie ni le rang vertical ni le nombre de lignes logiques.

## REN-INV012

Le Zoom A et le Zoom B ne modifient jamais le `TimelineLayout`.

## REN-INV013

Lors d'un Zoom B, `zoom_y` et `offset_y` restent inchangés.

---

# 88. Complexité

Sans culling, le rendu est proportionnel au nombre d'objets du layout.

```text
O(N)
```

Avec culling, le coût de dessin dépend principalement du nombre d'objets visibles.

Une structure spatiale plus avancée pourra être ajoutée si nécessaire.

La première version privilégie un test de visibilité simple.

---

# 89. Points à tester

Les tests devront couvrir au minimum :

1. rendu d'une personne ;
2. rendu d'un conjoint ;
3. couleurs de générations ;
4. conjoint gris ;
5. nœud de mariage ;
6. remariage ;
7. référence de branche ;
8. diagnostic ;
9. zoom avant ;
10. zoom arrière ;
11. zoom centré sur le pointeur ;
12. déplacement horizontal ;
13. déplacement vertical ;
14. culling d'un objet hors écran ;
15. même layout affiché en SVG ;
16. même layout affiché en PDF ;
17. même layout affiché en PNG ;
18. modification de couleur sans recalcul ;
19. modification de hauteur de ligne avec recalcul du layout ;
20. nouvelle racine avec recalcul complet ;
21. modification Gramps avec invalidation complète ;
22. stabilité du rendu ;
23. texte long ;
24. très grand layout ;
25. export avec dates inconnues ;
26. affichage d'une `display_value` sans effet sur l'inférence.

---

# 90. Décisions reportées

Les points suivants restent à préciser :

- bibliothèque graphique exacte utilisée dans la vue Gramps ;
- stratégie finale de pagination PDF ;
- limites de taille PNG ;
- style exact des diagnostics ;
- style exact des dates inconnues ;
- comportement du texte lors du Zoom A et du Zoom B ;
- facteurs et limites exacts de `zoom_x` et `zoom_y` ;
- convention définitive des raccourcis souris et clavier ;
- format exact des infobulles ;
- stratégie de sélection d'une personne ;
- navigation interactive vers une référence de branche ;
- éventuelle structure spatiale pour accélérer le culling ;
- mécanisme exact de détection de la révision de la base Gramps.

---

# Conclusion de la partie 4

Le rendu constitue la dernière étape de la chaîne.

```text
données
  ↓
inférence
  ↓
parcours
  ↓
layout
  ↓
rendu
```

Il ne doit jamais remonter cette chaîne pour modifier une décision prise en amont.

Son principe fondamental peut être résumé ainsi :

> **Le renderer dessine ce que le layout a décidé, le viewport décide ce qui est visible et l'invalidation décide ce qui doit réellement être recalculé.**

Cette séparation garantit un affichage fluide, des exports cohérents et une architecture évolutive.

---

# Table des matières

91. Objet de cette partie
92. Hypothèse de rendu en couleur
92b. Affichage des calendriers
93. Principes généraux d'export
94. Chaîne commune d'export
95. Export SVG
96. Export PDF
97. Export PNG
98. Dimensions et échelle de sortie
99. Gestion des très grands documents
100. Pagination PDF
101. Marges et zone imprimable
102. Polices et textes
103. Cohérence des couleurs
104. Diagnostics et informations temporaires
105. Métadonnées du document exporté
106. Gestion des erreurs d'export
107. Pseudo-code général
108. Exemple d'export PDF
109. Invariants d'export
110. Complexité
111. Points à tester
112. Décisions reportées

---

# 91. Objet de cette partie

Cette partie décrit les algorithmes d'export de la timeline vers des formats externes.

Les premiers formats prévus sont :

```text
SVG
PDF
PNG
```

Les exports utilisent le même `TimelineLayout` que la vue interactive.

Ils ne recalculent jamais :

- le modèle généalogique ;
- l'inférence temporelle ;
- le DFS ;
- le layout.

L'export répond à la question :

> **Comment produire un document fidèle à la représentation interactive à partir d'un `TimelineLayout` déjà calculé ?**

---

# 92. Hypothèse de rendu en couleur

## 92.1 Principe

La première version du projet suppose que l'écran, le fichier exporté et le périphérique d'impression utilisent la couleur.

Cette hypothèse est cohérente avec le rôle fonctionnel des couleurs dans le projet.

Les couleurs permettent notamment de distinguer :

```text
les générations
les conjoints
les diagnostics
les informations estimées ou particulières
```

---

## 92.2 Absence de mode noir et blanc dédié

La première version ne définit pas :

- de motifs de hachures spécifiques ;
- de types de traits alternatifs par génération ;
- de symboles particuliers remplaçant les couleurs ;
- de conversion automatique vers un thème noir et blanc.

Le moteur n'essaie donc pas de reconstruire une seconde grammaire graphique destinée à l'impression monochrome.

---

## 92.3 Conséquence

Un document imprimé en noir et blanc par un périphérique externe peut perdre une partie de l'information portée par les couleurs.

Cette limitation est acceptée dans la première version.

Un mode monochrome dédié pourra être étudié ultérieurement si un besoin réel apparaît.

---

# 92b. Affichage des calendriers

Le document exporté utilise :

- la représentation normalisée pour la timeline ;

- la représentation documentaire pour les justifications et preuves.

Exemple :

Timeline

────────────●────────────

1800

Justification

Décès :

18 pluviôse an VIII
(calendrier républicain)

Date normalisée utilisée
pour le calcul :

7 février 1800

---

# 93. Principes généraux d'export

## EXP-P001 — Un seul layout

Tous les formats utilisent le même `TimelineLayout`.

---

## EXP-P002 — Aucun recalcul généalogique

L'export ne relance jamais :

```text
GrampsDataAdapter
DescendanceBuilder
TemporalInferenceEngine
DescendanceTraversal
LayoutEngine
```

---

## EXP-P003 — Fidélité

Le document exporté doit conserver :

- l'ordre vertical ;
- l'échelle temporelle ;
- les couleurs ;
- les nœuds de mariage ;
- les segments de remariage ;
- les références de branche ;
- les diagnostics activés.

---

## EXP-P004 — Transformation de sortie séparée

L'export utilise une transformation adaptée au support.

```text
TimelineLayout
      │
      ▼
ExportTransform
      │
      ▼
DrawingContext spécifique
```

---

## EXP-P005 — Déterminisme

À layout, options d'export et format identiques, le résultat doit être reproductible.

---

# 94. Chaîne commune d'export

La chaîne générale est :

```text
TimelineLayout
      │
      ▼
ExportOptions
      │
      ▼
ExportTransform
      │
      ▼
DrawingContext
      │
      ▼
Renderer
      │
      ▼
fichier
```

Conceptuellement :

```text
export(layout, format, options)

    context = create_context(format, options)

    transform = create_export_transform(
        layout,
        options
    )

    renderer.render(
        layout,
        context,
        options.render_options,
        transform
    )

    context.finalize()
```

---

# 95. Export SVG

## 95.1 Caractéristiques

Le SVG est vectoriel.

Il conserve une représentation précise quelle que soit l'échelle d'affichage.

Il est particulièrement adapté :

- aux grandes timelines ;
- au zoom ;
- à l'édition dans un logiciel vectoriel ;
- à l'impression.

---

## 95.2 Dimensions

Le document SVG peut utiliser les dimensions logiques du layout transformées selon l'échelle d'export.

```text
svg_width
svg_height
```

---

## 95.3 Avantage principal

Le SVG constitue probablement le format le plus fidèle pour les très grands arbres.

Il n'impose pas immédiatement une pagination.

---

# 96. Export PDF

## 96.1 Caractéristiques

Le PDF est destiné principalement :

- à l'impression ;
- au partage ;
- à l'archivage.

---

## 96.2 Deux stratégies possibles

Une timeline peut être exportée :

```text
sur une seule grande page
```

ou :

```text
sur plusieurs pages
```

La première version doit permettre au minimum une stratégie fiable.

---

## 96.3 Grande page

Une grande page conserve la continuité de la timeline.

Elle convient notamment :

- aux traceurs ;
- aux impressions grand format ;
- à la consultation numérique.

---

## 96.4 Pagination

La pagination est traitée comme une transformation du document.

Elle ne modifie pas le `TimelineLayout`.

---

# 97. Export PNG

## 97.1 Caractéristiques

Le PNG est raster.

Il est simple à partager mais peut devenir très volumineux.

---

## 97.2 Résolution

L'utilisateur ou le système définit :

```text
scale
dpi
```

Le moteur calcule les dimensions finales.

---

## 97.3 Limites

Avant création, le moteur vérifie :

```text
pixel_width
pixel_height
estimated_memory
```

Un export trop grand doit être refusé proprement ou proposer une réduction d'échelle.

---

# 98. Dimensions et échelle de sortie

## 98.1 Principe

Les dimensions de sortie dépendent :

```text
layout_width
layout_height
export_scale
```

Conceptuellement :

```text
output_width = layout_width × export_scale
output_height = layout_height × export_scale
```

---

## 98.2 Conservation des proportions

Par défaut :

```text
scale_x = scale_y
```

L'export ne reprend pas le Zoom B temporel de la vue interactive sauf demande explicite future.

Le document exporté représente la géométrie normale du layout.

---

## 98.3 Ajustement à une page

Une option future peut calculer :

```text
scale = min(
    printable_width / layout_width,
    printable_height / layout_height
)
```

Cette stratégie peut rendre les textes trop petits pour de très grandes descendances.

Elle ne doit donc pas être imposée automatiquement.

---

# 99. Gestion des très grands documents

## 99.1 Problème

Une grande descendance peut produire :

```text
une très grande largeur
une très grande hauteur
```

---

## 99.2 SVG

Le SVG peut généralement conserver une grande surface logique.

---

## 99.3 PDF

Le PDF peut utiliser :

- une grande page ;
- une pagination.

---

## 99.4 PNG

Le PNG est le format le plus contraint par la mémoire.

Le moteur doit calculer avant création :

```text
estimated_bytes =
    width × height × bytes_per_pixel
```

---

# 100. Pagination PDF

## 100.1 Principe

La pagination découpe la surface d'export.

Elle ne découpe pas le modèle.

---

## 100.2 Tuiles

Conceptuellement :

```text
page_column
page_row
```

Chaque page correspond à une fenêtre sur le layout.

---

## 100.3 Continuité temporelle

Les limites de page doivent conserver l'échelle temporelle.

Une date située à une coordonnée donnée reste au même emplacement logique.

---

## 100.4 Répétition de repères

Une future stratégie pourra répéter :

- l'échelle temporelle ;
- certaines graduations ;
- un titre ;
- des informations de page.

---

## 100.5 Décision prudente

La pagination PDF est considérée comme une fonctionnalité indépendante.

Elle ne doit pas retarder la production d'un export PDF sur une grande page si celui-ci fonctionne correctement.

---

# 101. Marges et zone imprimable

## 101.1 Marges du layout

Les marges logiques appartiennent au `TimelineLayout`.

---

## 101.2 Marges du document

Le document peut ajouter :

```text
document_margin_top
document_margin_bottom
document_margin_left
document_margin_right
```

---

## 101.3 Imprimante

Le moteur ne dépend pas directement d'un pilote d'imprimante.

Il produit un PDF.

Le logiciel d'impression gère ensuite les contraintes physiques du périphérique.

---

# 102. Polices et textes

## 102.1 Cohérence

Les exports utilisent les mêmes familles de polices que la vue lorsque cela est possible.

---

## 102.2 Disponibilité

Si une police n'est pas disponible dans le contexte d'export, une police de remplacement est utilisée.

---

## 102.3 Mesure

Le contexte d'export mesure les textes avec les métriques du support.

Ces différences peuvent modifier légèrement l'encombrement visuel.

Elles ne doivent pas modifier l'ordre généalogique ni l'échelle temporelle.

---

# 103. Cohérence des couleurs

## 103.1 Palette commune

Les couleurs proviennent du même thème graphique que la vue interactive.

---

## 103.2 Générations

Une génération conserve la même couleur quel que soit le format.

---

## 103.3 Conjoints

Les conjoints restent gris.

---

## 103.4 Impression couleur

La première version suppose une impression couleur.

Le projet ne garantit pas la conservation de la distinction des générations après conversion monochrome par une imprimante externe.

---

# 104. Diagnostics et informations temporaires

## 104.1 Export des diagnostics

Selon les options, les diagnostics peuvent être :

```text
affichés
masqués
```

---

## 104.2 Valeurs inférées

Les conventions graphiques indiquant une valeur inférée doivent rester cohérentes avec la vue.

---

## 104.3 `display_value`

Une position purement graphique peut être exportée.

Elle conserve son style indiquant qu'elle ne représente pas une date prouvée.

---

# 105. Métadonnées du document exporté

Un export peut contenir :

```text
nom du projet
date de génération
personne racine
version du greffon
format d'export
```

Ces informations ne font pas partie du layout généalogique.

Elles appartiennent au document exporté.

---

# 106. Gestion des erreurs d'export

Le moteur doit traiter proprement :

```text
fichier non accessible
espace disque insuffisant
dimensions PNG excessives
contexte graphique indisponible
échec de finalisation
```

Une erreur d'export :

- ne modifie jamais la base Gramps ;
- ne détruit pas le `TimelineLayout` ;
- doit produire un message compréhensible.

---

# 107. Pseudo-code général

```text
function export_timeline(
    layout,
    format,
    options
):

    validate_export_options(
        layout,
        format,
        options
    )

    context = create_drawing_context(
        format,
        options
    )

    transform = create_export_transform(
        layout,
        format,
        options
    )

    try:

        renderer.render(
            layout,
            context,
            options.render_options,
            transform
        )

        context.finalize()

    except ExportError as error:

        context.abort_if_possible()

        raise UserVisibleExportError(
            explain(error)
        )
```

---

# 108. Exemple d'export PDF

Entrée :

```text
TimelineLayout
    width = 8000
    height = 3000
```

Options :

```text
format = PDF
mode = LARGE_PAGE
scale = 1.0
color = true
```

Le moteur crée :

```text
PdfDrawingContext
```

Puis :

```text
ExportTransform
    scale_x = 1.0
    scale_y = 1.0
```

Le `Renderer` dessine exactement les objets du layout.

Le PDF obtenu conserve :

- la timeline ;
- les couleurs des générations ;
- les conjoints gris ;
- les nœuds de mariage ;
- les remariages ;
- les références ;
- les diagnostics activés.

---

# 109. Invariants d'export

## EXP-INV001

Un export ne modifie jamais `TimelineLayout`.

## EXP-INV002

Un export ne relance jamais l'inférence temporelle.

## EXP-INV003

Un export ne relance jamais le DFS.

## EXP-INV004

Un export ne recalcule jamais le layout.

## EXP-INV005

Les couleurs des générations sont conservées entre les formats.

## EXP-INV006

Les conjoints restent gris dans tous les formats couleur.

## EXP-INV007

Le projet ne garantit pas un équivalent sémantique complet en impression monochrome.

## EXP-INV008

Une erreur d'export ne modifie jamais les données Gramps.

## EXP-INV009

À layout et options identiques, l'export est déterministe.

## EXP-INV010

La pagination éventuelle ne modifie pas les coordonnées logiques du layout.

## EXP-INV011

Une justification peut afficher la date documentaire dans son calendrier d'origine,
même si la timeline utilise la date normalisée.

---

# 110. Complexité

Le coût d'un export est principalement proportionnel au nombre d'objets à dessiner.

```text
O(N)
```

Pour le PNG, le coût mémoire dépend également du nombre de pixels.

```text
O(width × height)
```

Le SVG et le PDF sont généralement moins dépendants d'une grande surface raster.

---

# 111. Points à tester

Les tests devront couvrir au minimum :

1. export SVG simple ;
2. export PDF simple ;
3. export PNG simple ;
4. conservation des couleurs ;
5. conjoint gris ;
6. plusieurs générations ;
7. remariages ;
8. référence de branche ;
9. diagnostic visible ;
10. diagnostic masqué ;
11. valeur inférée ;
12. `display_value` ;
13. grande largeur ;
14. grande hauteur ;
15. très grand SVG ;
16. PDF grande page ;
17. PNG dépassant une limite raisonnable ;
18. erreur de fichier ;
19. export répété déterministe ;
20. vérification qu'aucun recalcul de layout n'est déclenché ;
21. métadonnées du document ;
22. impression couleur comme hypothèse de conception.

---

# 112. Décisions reportées

Les points suivants restent à préciser :

- format SVG exact ;
- bibliothèque PDF exacte ;
- stratégie de pagination PDF ;
- dimensions maximales d'une page PDF ;
- limites de sécurité PNG ;
- choix du DPI par défaut ;
- polices incorporées ou référencées ;
- position des métadonnées ;
- export éventuel d'une légende ;
- options de masquage des diagnostics ;
- éventuel mode monochrome futur.

---

# Conclusion de la partie 5

Les exports sont des vues de sortie du même `TimelineLayout`.

```text
TimelineLayout
      │
      ├── écran
      ├── SVG
      ├── PDF
      └── PNG
```

Aucun format ne possède sa propre logique généalogique.

Le principe fondamental est :

> **Le projet produit une seule géométrie, puis l'adapte aux différents supports sans modifier son sens.**

La première version suppose un rendu et une impression en couleur.

Cette décision permet de conserver une grammaire graphique simple et cohérente, fondée notamment sur la couleur des générations et le gris des conjoints.

---

# Table des matières

113. Objet de cette partie
114. Responsabilité de la couche `ui/`
115. Frontière entre le cœur et Gramps
116. Composants principaux de l'interface
117. Cycle d'initialisation de la vue
118. Sélection de la personne racine
119. Construction et affichage de la timeline
120. Cycle de dessin
121. Gestion des événements utilisateur
122. Zoom A — zoom uniforme
123. Zoom B — zoom temporel
124. Déplacement de la vue
125. Sélection d'un objet graphique
126. Navigation vers une personne ou une famille
127. Références de branches déjà représentées
128. Infobulles et informations contextuelles
129. Mise à jour après modification de Gramps
130. Gestion de l'état de la vue
131. Commandes d'export
132. Gestion des erreurs dans l'interface
133. Travail long et réactivité
134. Pseudo-code général
135. Exemple de cycle utilisateur
136. Invariants de l'interface
137. Complexité
138. Points à tester
139. Décisions reportées
140. Conclusion générale de `03_Algorithms.md`

---

# 113. Objet de cette partie

Cette partie décrit l'intégration de la timeline dans l'interface graphique de Gramps.

La couche `ui/` répond à la question :

> **Comment relier les événements et composants graphiques de Gramps au moteur de timeline sans introduire de logique généalogique dans l'interface ?**

La chaîne générale est :

```text
Gramps
  │
  ▼
ui/
  │
  ▼
TimelineEngine
  │
  ▼
TimelineLayout
  │
  ▼
Renderer
  │
  ▼
surface graphique Gramps
```

La couche `ui/` orchestre les interactions. Elle ne remplace aucun moteur spécialisé.

---

# 114. Responsabilité de la couche `ui/`

La couche `ui/` est responsable de :

- créer et intégrer la vue dans Gramps ;
- connaître la personne racine courante ;
- déclencher la construction de la timeline ;
- conserver l'état interactif de la vue ;
- transmettre les événements souris et clavier ;
- déclencher les rafraîchissements ;
- appeler le `Renderer` ;
- déclencher les exports ;
- afficher les erreurs et diagnostics destinés à l'utilisateur ;
- réagir aux changements pertinents de la base Gramps.

Elle n'est pas responsable de :

- parcourir la descendance ;
- calculer une inférence ;
- ordonner les enfants ;
- ordonner les familles ;
- calculer les coordonnées logiques ;
- interpréter une contradiction généalogique ;
- modifier les données Gramps.

---

# 115. Frontière entre le cœur et Gramps

## 115.1 Principe

Le cœur du projet doit rester aussi indépendant que possible de l'interface graphique de Gramps.

Conceptuellement :

```text
GRAMPS-SPECIFIC
    GrampsDataAdapter
    ui/

INDEPENDENT CORE
    domain/
    inference/
    traversal/
    layout/
    rendering/
    export/
```

## 115.2 Conséquence

Les objets spécifiques à l'interface Gramps ne doivent pas circuler dans :

```text
TemporalInferenceEngine
DescendanceTraversal
LayoutEngine
TimelineLayout
```

## 115.3 Adaptation

La couche `ui/` traduit :

```text
événement graphique
        │
        ▼
commande du projet
```

et :

```text
résultat du projet
        │
        ▼
présentation Gramps
```

---

# 116. Composants principaux de l'interface

Une première organisation conceptuelle peut être :

```text
ui/
    gramps_view.py
    view_state.py
    interaction_controller.py
    hit_testing.py
    dialogs.py
```

Les noms exacts pourront évoluer lors de l'implémentation.

## 116.1 `GrampsTimelineView`

Responsable de l'intégration dans Gramps.

Elle crée la surface graphique, reçoit les événements, déclenche le dessin et connecte la vue au cycle de vie de Gramps.

## 116.2 `ViewState`

Conserve l'état interactif :

```text
ViewState
    root_person_handle
    viewport_transform
    selected_object
    hovered_object
    render_options
    invalidation_state
    current_layout
```

## 116.3 `InteractionController`

Transforme les événements utilisateur en actions :

```text
mouse_wheel
Ctrl + mouse_wheel
mouse_drag
mouse_click
double_click
keyboard_shortcut
```

## 116.4 `HitTester`

Détermine quel objet graphique se trouve sous une position du pointeur.

---

# 117. Cycle d'initialisation de la vue

À l'ouverture de la vue :

```text
1. créer les composants UI
2. créer ViewState
3. déterminer la personne racine initiale
4. construire la timeline
5. calculer le layout
6. ajuster la vue initiale
7. demander le premier dessin
```

Conceptuellement :

```text
initialize_view()

    create_widgets()
    connect_events()

    root = resolve_initial_root()
    state.root_person_handle = root

    rebuild_timeline()
    fit_initial_view()
    request_redraw()
```

---

# 118. Sélection de la personne racine

La personne racine peut provenir de la personne active ou sélectionnée dans Gramps.

Lorsqu'une nouvelle racine est choisie :

```text
state.root_person_handle = new_root
invalidate(MODEL)
rebuild_if_needed()
request_redraw()
```

Par défaut, une nouvelle racine peut déclencher un nouvel ajustement de la vue. Le comportement exact sera validé par l'usage.

---

# 119. Construction et affichage de la timeline

La vue appelle une façade d'orchestration.

Conceptuellement :

```text
result = timeline_engine.build(
    database,
    root_person_handle,
    options
)
```

Le résultat contient ou permet d'obtenir :

```text
TimelineModel
TraversalResult
TimelineLayout
Diagnostics
```

La vue conserve le `TimelineLayout` courant.

---

# 120. Cycle de dessin

Le framework graphique demande à la vue de se redessiner.

La vue ne dessine pas directement les objets généalogiques. Elle appelle le `Renderer`.

```text
on_draw(graphics_context):

    if state.current_layout is None:
        draw_empty_state()
        return

    renderer.render(
        layout = state.current_layout,
        drawing_context = graphics_context,
        render_options = state.render_options,
        transform = state.viewport_transform
    )
```

Un événement de dessin ne doit jamais déclencher silencieusement une reconstruction complète de la généalogie.

---

# 121. Gestion des événements utilisateur

La chaîne générale est :

```text
événement Gramps / toolkit graphique
        │
        ▼
GrampsTimelineView
        │
        ▼
InteractionController
        │
        ▼
modification de ViewState
        │
        ▼
request_redraw()
```

Pour une action nécessitant un recalcul :

```text
InteractionController
        │
        ▼
invalidate(level)
        │
        ▼
rebuild_if_needed()
        │
        ▼
request_redraw()
```

---

# 122. Zoom A — zoom uniforme

Interaction proposée :

```text
molette
```

Action :

```text
zoom_x *= factor
zoom_y *= factor
```

Le zoom reste centré sur le pointeur.

Il permet de voir davantage de lignes, de se rapprocher d'une branche et de naviguer dans l'ensemble de la descendance.

Invalidation :

```text
RENDER_ONLY
```

---

# 123. Zoom B — zoom temporel

Interaction proposée :

```text
Ctrl + molette
```

Action :

```text
zoom_x *= factor
zoom_y inchangé
```

Il permet d'examiner une période courte, de comparer des écarts temporels et de conserver le même contexte vertical.

Invalidation :

```text
RENDER_ONLY
```

---

# 124. Déplacement de la vue

Une action de glisser-déplacer modifie :

```text
offset_x
offset_y
```

Le déplacement agit uniquement sur `ViewportTransform`.

Invalidation :

```text
RENDER_ONLY
```

---

# 125. Sélection d'un objet graphique

L'utilisateur peut vouloir sélectionner :

- une personne ;
- un nœud de mariage ;
- une référence de branche ;
- un diagnostic.

La position écran est convertie en position logique :

```text
logical_point =
    inverse_transform(screen_point)
```

Puis :

```text
hit_tester.find_object_at(
    logical_point,
    layout
)
```

Si plusieurs objets se chevauchent, une priorité doit être définie. Première proposition :

```text
diagnostic
relationship_node
person
branch_reference
```

Cette priorité reste à valider.

---

# 126. Navigation vers une personne ou une famille

Une interaction pourra demander à Gramps d'ouvrir ou de sélectionner la personne correspondant au `person_handle`.

Un nœud de mariage conserve le `family_handle` et pourra permettre d'ouvrir la famille correspondante.

La timeline référence les objets Gramps existants. Elle ne crée pas d'objets de substitution.

---

# 127. Références de branches déjà représentées

Une `BranchReferencePlacement` peut être interactive.

Lors d'un clic :

```text
target_rank
    │
    ▼
calcul de la position logique cible
    │
    ▼
mise à jour du viewport
    │
    ▼
request_redraw()
```

Conceptuellement :

```text
center_on_rank(target_rank)
```

Aucun DFS n'est relancé.

---

# 128. Infobulles et informations contextuelles

Le déplacement du pointeur peut déclencher un hit test léger.

Une infobulle peut afficher :

- identité ;
- dates ;
- origine d'une valeur ;
- niveau de certitude ;
- justification d'une inférence ;
- diagnostic.

L'infobulle affiche des informations déjà disponibles. Elle ne lance pas une nouvelle inférence.

---

# 129. Mise à jour après modification de Gramps

Une modification pertinente de la base invalide le modèle courant :

```text
invalidate(MODEL)
```

La reconstruction produit ensuite :

```text
nouvelles données
nouvelle inférence
nouveau parcours
nouveau layout
```

Si Gramps permet ultérieurement d'identifier précisément la nature d'une modification, une invalidation plus fine pourra être utilisée.

La première version peut privilégier une stratégie sûre :

> **Toute modification généalogique pertinente invalide la chaîne complète.**

---

# 130. Gestion de l'état de la vue

État persistant pendant la session :

```text
root_person_handle
viewport_transform
selected_object
render_options
current_layout
```

État recalculable :

```text
TimelineModel
TraversalResult
TimelineLayout
```

La fermeture de la vue ne modifie aucune donnée Gramps.

La persistance éventuelle de préférences relève d'un mécanisme séparé.

---

# 131. Commandes d'export

La vue peut proposer :

```text
Exporter en SVG
Exporter en PDF
Exporter en PNG
```

La commande :

```text
1. vérifie qu'un layout existe
2. demande le chemin de destination
3. collecte les options
4. appelle ExportService
5. affiche le résultat ou l'erreur
```

Le `ViewportTransform` interactif n'est pas transmis comme géométrie d'export.

En particulier, un Zoom B actif ne déforme pas le document exporté.

---

# 132. Gestion des erreurs dans l'interface

L'interface peut rencontrer :

```text
erreur de données
erreur de calcul
erreur de rendu
erreur d'export
erreur d'intégration Gramps
```

Une erreur technique interne ne doit pas être affichée brute à l'utilisateur si un message plus compréhensible peut être produit.

Les détails techniques peuvent être écrits dans le mécanisme de journalisation approprié.

Si une reconstruction échoue, la stratégie de conservation éventuelle de l'ancien layout devra être définie avec prudence.

---

# 133. Travail long et réactivité

Une très grande descendance peut nécessiter un calcul perceptible.

La première version peut :

```text
afficher un état de chargement
effectuer le calcul
mettre à jour la vue
```

Une version ultérieure pourra utiliser :

- traitement différé ;
- tâche asynchrone ;
- annulation ;
- progression.

Toute exécution en arrière-plan devra respecter les contraintes d'accès à la base Gramps et au toolkit graphique.

Aucune stratégie de concurrence ne doit être introduite sans vérifier ces contraintes.

---

# 134. Pseudo-code général

```text
class GrampsTimelineView:

    initialize():
        create_ui()
        connect_events()
        state = ViewState()
        set_initial_root()
        rebuild_timeline()
        fit_initial_view()
        request_redraw()

    on_root_changed(new_root):
        state.root_person_handle = new_root
        invalidate(MODEL)
        rebuild_timeline()
        fit_initial_view()
        request_redraw()

    on_mouse_wheel(event):

        if event.ctrl_pressed:
            apply_temporal_zoom(
                state.viewport_transform,
                event.position,
                event.delta
            )
        else:
            apply_uniform_zoom(
                state.viewport_transform,
                event.position,
                event.delta
            )

        request_redraw()

    on_drag(delta):
        pan(
            state.viewport_transform,
            delta
        )
        request_redraw()

    on_click(position):

        logical_position =
            inverse_transform(position)

        target =
            hit_tester.find_object_at(
                logical_position,
                state.current_layout
            )

        handle_target(target)

    on_draw(context):

        renderer.render(
            state.current_layout,
            context,
            state.render_options,
            state.viewport_transform
        )

    on_database_changed():
        invalidate(MODEL)
        schedule_rebuild()

    on_export(format):
        export_service.export(
            state.current_layout,
            format,
            export_options
        )
```

---

# 135. Exemple de cycle utilisateur

## Étape 1 — Ouverture

```text
personne active Gramps
        │
        ▼
root_person_handle
        │
        ▼
construction complète
        │
        ▼
TimelineLayout
        │
        ▼
affichage
```

## Étape 2 — Navigation générale

```text
Zoom A
        │
        ▼
zoom_x + zoom_y
        │
        ▼
redessin uniquement
```

## Étape 3 — Analyse temporelle

```text
Zoom B
        │
        ▼
zoom_x uniquement
        │
        ▼
redessin uniquement
```

## Étape 4 — Référence de branche

L'utilisateur clique sur :

```text
Descendance déjà représentée plus haut
```

La vue centre le viewport sur la branche cible.

Aucun calcul généalogique n'est relancé.

## Étape 5 — Modification dans Gramps

```text
MODEL invalid
        │
        ▼
reconstruction
        │
        ▼
nouveau layout
        │
        ▼
redessin
```

---

# 136. Invariants de l'interface

## UI-INV001

La couche `ui/` ne contient aucune règle d'inférence temporelle.

## UI-INV002

La couche `ui/` ne décide jamais de l'ordre DFS.

## UI-INV003

La couche `ui/` ne calcule jamais les coordonnées logiques des objets généalogiques.

## UI-INV004

Un événement de dessin ne déclenche pas de reconstruction complète.

## UI-INV005

Le Zoom A et le Zoom B ne modifient jamais le `TimelineLayout`.

## UI-INV006

Le déplacement ne modifie jamais le `TimelineLayout`.

## UI-INV007

Une interaction avec une personne ou une famille utilise le handle de l'objet Gramps existant.

## UI-INV008

La couche `ui/` ne crée jamais une personne fictive.

## UI-INV009

Une commande d'export utilise le layout et non le viewport interactif.

## UI-INV010

Un Zoom B actif ne modifie pas les proportions du document exporté.

## UI-INV011

Une modification pertinente de la base Gramps invalide au minimum le modèle courant.

## UI-INV012

La fermeture de la vue ne modifie aucune donnée généalogique.

## UI-INV013

Une infobulle ne déclenche aucune nouvelle inférence.

## UI-INV014

Une référence de branche peut déplacer la vue sans relancer le DFS.

## UI-INV015

Les dépendances spécifiques au toolkit graphique restent confinées à la couche d'intégration et de rendu adaptée.

---

# 137. Complexité

Les interactions suivantes sont normalement en temps constant ou proche :

```text
zoom
déplacement
changement de sélection
```

Le hit testing naïf peut être :

```text
O(N)
```

Une structure d'index spatial pourra être ajoutée si nécessaire.

Le changement de racine ou une modification de la base peut déclencher la chaîne complète.

---

# 138. Points à tester

Les tests devront couvrir au minimum :

1. ouverture de la vue ;
2. absence de personne active ;
3. sélection d'une racine ;
4. changement de racine ;
5. premier affichage ;
6. redessin sans recalcul ;
7. Zoom A avant ;
8. Zoom A arrière ;
9. Zoom B avant ;
10. Zoom B arrière ;
11. Zoom B sans déplacement vertical ;
12. déplacement horizontal ;
13. déplacement vertical ;
14. clic sur une personne ;
15. clic sur une famille ;
16. clic sur une référence de branche ;
17. survol d'une personne ;
18. infobulle d'une valeur inférée ;
19. infobulle d'un diagnostic ;
20. modification de Gramps ;
21. reconstruction après modification ;
22. export SVG ;
23. export PDF ;
24. export PNG ;
25. export pendant un Zoom B ;
26. erreur de reconstruction ;
27. erreur d'export ;
28. fermeture de la vue ;
29. très grande descendance ;
30. stabilité après plusieurs zooms et déplacements.

---

# 139. Décisions reportées

Les points suivants restent à préciser lors de l'intégration réelle :

- API exacte de création d'une vue Gramps ;
- toolkit graphique et classes exactes disponibles dans la version cible ;
- événements exacts de changement de personne active ;
- événements exacts de modification de la base ;
- mécanisme d'ouverture d'une fiche Personne ;
- mécanisme d'ouverture d'une fiche Famille ;
- raccourcis définitifs souris et clavier ;
- curseurs de souris ;
- style des infobulles ;
- stratégie de sélection ;
- stratégie de chargement pour les très grandes descendances ;
- possibilité d'annuler un calcul ;
- éventuelle persistance des préférences de vue ;
- accessibilité clavier ;
- index spatial éventuel pour le hit testing.

Ces points relèvent de l'intégration avec l'API réelle de Gramps et devront être confirmés lors de l'implémentation.

---

# 140. Conclusion générale de `03_Algorithms.md`

Le projet est organisé comme une chaîne de transformations explicites.

```text
Base Gramps
      │
      ▼
GrampsDataAdapter
      │
      ▼
RawGenealogyData
      │
      ▼
construction de la descendance
      │
      ▼
moteur d'inférence temporelle
      │
      ▼
TimelineModel
      │
      ▼
parcours DFS
      │
      ▼
TraversalResult
      │
      ▼
LayoutEngine
      │
      ▼
TimelineLayout
      │
      ├──────────────► ExportService
      │                    │
      │                    ├── SVG
      │                    ├── PDF
      │                    └── PNG
      │
      ▼
ui/
      │
      ▼
ViewportTransform
      │
      ▼
Renderer
      │
      ▼
Vue Gramps
```

Chaque étape possède une responsabilité distincte.

Le projet sépare notamment :

```text
les données
la preuve
l'inférence
l'ordre
la géométrie
le rendu
l'interaction
l'export
```

Cette séparation permet de garantir les principes fondateurs du projet :

- respecter les données de Gramps ;
- ne modifier aucune donnée généalogique ;
- ne pas créer de personne fictive ;
- conserver la justification des inférences ;
- distinguer une donnée prouvée d'une valeur calculée non prouvée ;
- distinguer une estimation temporelle d'une simple position graphique ;
- produire un parcours déterministe ;
- produire une géométrie déterministe ;
- permettre une exploration interactive sans modifier le modèle ;
- produire des exports cohérents avec la représentation.

Le principe général peut être résumé ainsi :

> **Chaque moteur transforme une représentation en une autre, sans empiéter sur la responsabilité du moteur précédent ou suivant.**

Cette organisation doit permettre au code d'évoluer sans remettre en cause les concepts fondamentaux du projet.

`03_Algorithms.md` fournit désormais la description algorithmique nécessaire pour commencer l'implémentation de manière progressive, testable et conforme aux spécifications et à l'architecture.

