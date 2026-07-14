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
