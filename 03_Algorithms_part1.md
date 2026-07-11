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
