# Gramps Descendants Timeline

## InferenceEngine

**Version :** 0.2\
**Statut :** Brouillon de conception\
**Document :** `07_InferenceEngine.md`\
**Milestone :** 4 --- `TemporalInferenceEngine`

------------------------------------------------------------------------

# Table des matières

1.  Objet du document
2.  Méthode de travail
3.  Principes généraux du moteur
4.  Cas d'exécution d'un calcul d'inférence
5.  Chaîne conceptuelle
6.  `TemporalTarget`
7.  `TemporalEvidence`
8.  `Rule`
9.  `TemporalConstraint`
10. `RuleContext`
11. Contradictions et diagnostics
12. Résultat du moteur
13. Stratégie d'implémentation progressive

------------------------------------------------------------------------

# 1. Objet du document

Le présent document décrit et justifie la conception du
`TemporalInferenceEngine` (Milestone 4).

Le moteur d'inférence temporelle doit exploiter les informations
généalogiques disponibles pour :

-   compléter certaines informations temporelles incomplètes ;
-   resserrer des bornes temporelles existantes lorsque cela est
    autorisé ;
-   utiliser certains événements comme preuves temporelles pour d'autres
    événements ;
-   produire une date représentative lorsque les contraintes permettent
    de le faire ;
-   conserver la provenance et la justification du raisonnement ;
-   détecter et expliquer les contradictions ;
-   ne jamais modifier les données sources Gramps.

------------------------------------------------------------------------

# 2. Méthode de travail

## 2.1 Définir la sortie du moteur

Il faut déterminer :

-   quel objet représente une date inférée ;
-   comment conserver `minimum`, `maximum` et `representative_value` ;
-   comment stocker les justifications ;
-   comment conserver les règles ayant participé au calcul.

## 2.2 Définir les preuves utilisées par le moteur

Une preuve temporelle doit permettre de conserver notamment :

-   l'objet auquel l'événement est rattaché ;
-   l'événement source ;
-   le rôle porté par la référence ;
-   la date utilisée ;
-   la provenance nécessaire aux diagnostics.

Cette responsabilité est portée par `TemporalEvidence`.

## 2.3 Définir les règles élémentaires

Une règle doit avoir une responsabilité très petite.

Exemples :

``` python
BirthBeforeDeathRule
MarriageAfterBirthRule
ParentBeforeChildBirthRule
BirthOrderRule
```

## 2.4 Construire `InferenceEngine`

Le moteur reçoit :

``` python
RawGenealogyData
```

et produit un résultat temporel enrichi, sans modifier les objets
sources.

## 2.5 Commencer avec des cas extrêmement simples

Avant les règles complexes, on teste par exemple :

``` text
naissance inconnue
+
décès connu
+
mariage connu
→ bornes temporelles simples
```

## 2.6 Augmenter progressivement la difficulté

Les étapes suivantes pourront introduire :

-   ordre des frères et sœurs ;
-   dates des enfants ;
-   âge biologique des parents ;
-   mariages ;
-   décès ;
-   plusieurs preuves convergentes ;
-   preuves contradictoires ;
-   impossibilité de conclure → `representative_value = None`.

------------------------------------------------------------------------

# 3. Principes généraux du moteur

## 3.1 La donnée Gramps est souveraine

Le moteur ne modifie jamais silencieusement une donnée saisie dans
Gramps.

Si le généalogiste a saisi le modifier `ABOUT`, il exprime une
estimation humaine qu'il souhaite conserver. Le moteur ne doit donc pas
tenter de remplacer cette estimation.

Conceptuellement :

``` text
date vide
→ « essaie de trouver quelque chose »

vers 1740
→ « j'ai choisi mon estimation, n'essaie pas de la modifier »

avant 1740
→ « je connais cette limite ; essaie de préciser »
```

## 3.2 Une preuve n'est pas une contrainte

Un événement ou une référence à un événement constitue une information
source.

Cette information devient un `TemporalEvidence`.

Une `Rule` interprète ensuite cette preuve et peut produire une ou
plusieurs `TemporalConstraint`.

``` text
donnée Gramps
      ↓
TemporalEvidence
      ↓
Rule
      ↓
TemporalConstraint
```

## 3.3 Une contrainte n'est pas nécessairement une estimation

Une contrainte peut uniquement éliminer des dates impossibles ou
permettre de détecter une contradiction.

Elle n'a pas nécessairement besoin de produire une date représentative.

## 3.4 Traçabilité

Toute contrainte produite doit conserver suffisamment de provenance pour
permettre de répondre à la question :

> Pourquoi le moteur a-t-il produit cette borne ?

Cette traçabilité doit également permettre d'identifier les événements
Gramps impliqués dans une contradiction.

## 3.5 Cardinalité des événements principaux

La présence de plusieurs `TemporalEvidence` principales de même sémantique
n'est pas toujours une incohérence.

La cardinalité dépend de la sémantique de l'événement.

| EventSemantic | Principal | Cardinalité attendue |
|---|---|---|
| `BIRTH` | PERSON | 0..1 par personne |
| `DEATH` | PERSON | 0..1 par personne |
| `BAPTISM` | PERSON | plusieurs possibles |
| `BURIAL` | PERSON | plusieurs possibles |
| `CENSUS` | PERSON | plusieurs possibles |
| `MARRIAGE` | FAMILY | plusieurs possibles |
| `DIVORCE` | FAMILY | plusieurs possibles |

Pour `BIRTH` et `DEATH`, plusieurs événements principaux utilisables pour la
même personne indiquent une incohérence de données.

Pour `BAPTISM`, `BURIAL`, `CENSUS`, `MARRIAGE` et `DIVORCE`, plusieurs événements
principaux peuvent être légitimes et doivent être conservés comme preuves
distinctes.

------------------------------------------------------------------------

# 4. Cas d'exécution d'un calcul d'inférence

## 4.1 Deux usages des informations temporelles

Le moteur réalise deux opérations différentes.

### A --- Compléter une information temporelle

``` text
BIRTH : avant 1765
        ↓
autres contraintes
        ↓
resserrement éventuel de la borne
```

### B --- Extraire des contraintes d'une preuve

``` text
Prisonnier : 1916–1918
        ↓
preuve d'existence
        ↓
BIRTH ≤ 1916
DEATH ≥ 1918
```

## 4.2 Comportement selon le modifier Gramps

### 1. Valeur à respecter

``` text
NONE
ABOUT
```

→ pas d'inférence sur la date elle-même.

### 2. Contrainte sur une date ponctuelle à compléter

``` text
BEFORE
AFTER
RANGE
```

→ l'inférence peut resserrer les bornes.

### 3. Information temporelle utilisable comme preuve

``` text
SPAN
FROM
TO
```

→ ne provoque pas nécessairement l'inférence sur l'événement lui-même ;\
→ peut produire des contraintes sur `BIRTH` / `DEATH`.

### 4. Valeur non interprétable automatiquement

``` text
TEXTONLY
```

### 5. Aucune valeur

→ inférence complète autorisée.

## 4.3 Synthèse

  -----------------------------------------------------------------------
  Modifier             Compléter la date de cet   Utilisable comme preuve
                                      événement  pour d'autres événements
  ------------------- ------------------------- -------------------------
  `NONE`                                    Non                       Oui

  `BEFORE`                                  Oui                       Oui

  `AFTER`                                   Oui                       Oui

  `ABOUT`                                   Non                       Oui

  `RANGE`                                   Oui                       Oui

  `SPAN`                                    Non                       Oui

  `TEXTONLY`                                Non       Non automatiquement

  `FROM`                               Non pour                       Oui
                           BIRTH/MARRIAGE/DEATH 

  `TO`                                 Non pour                       Oui
                           BIRTH/MARRIAGE/DEATH 
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Chaîne conceptuelle

L'architecture générale est :

``` text
DONNÉES GRAMPS
      ↓
RawGenealogyData
        ↓
EventReferenceIndex
        ↓
TemporalEvidenceBuilder
        ↓
TemporalEvidence
        ↓
Rule
 ├── applicability
 ├── contextual parameters
 ├── strength (HARD / SOFT)
 └── production
      ↓
TemporalConstraint
 ├── target
 ├── operator
 ├── bound
 ├── rule_id
 ├── strength
 └── provenance
      ↓
Constraint Engine
        ↓
intersection / propagation
        ↓
coherent temporal bounds
        ↓
Inference
        ↓
representative_value
certainty
justifications
```

Les trois objets centraux sont :

``` text
TemporalTarget
    → ce que l'on cherche à borner
    → BIRTH / MARRIAGE / DEATH seulement

TemporalEvidence
    → fait temporel utilisé comme preuve
    → beaucoup plus de EventSemantic possibles
    → rôle pris en compte

TemporalConstraint
    → borne concrète produite par une Rule
      pour une TemporalTarget
```

------------------------------------------------------------------------

# 6. `TemporalTarget`

## 6.1 Rôle

`TemporalTarget` représente ce que le moteur cherche à borner.

Dans le modèle :

-   une naissance appartient à une `Person` ;
-   un décès appartient à une `Person` ;
-   un mariage appartient à une `Family`.

Cette distinction est indispensable pour représenter correctement
plusieurs mariages d'une même personne.

## 6.2 Définition conceptuelle

``` python
class TemporalOwnerType(str, Enum):
    PERSON = "PERSON"
    FAMILY = "FAMILY"


class TargetSemantic(str, Enum):
    BIRTH = "BIRTH"
    MARRIAGE = "MARRIAGE"
    DEATH = "DEATH"


@dataclass(frozen=True, slots=True)
class TemporalTarget:
    owner_type: TemporalOwnerType
    owner_id: str
    semantic: TargetSemantic
```

## 6.3 Combinaisons valides

  `owner_type`   `owner_id`   `semantic`   Signification
  -------------- ------------ ------------ -----------------------
  `PERSON`       `I0100`      `BIRTH`      naissance de Jean
  `PERSON`       `I0100`      `DEATH`      décès de Jean
  `FAMILY`       `F0020`      `MARRIAGE`   mariage Jean × Marie
  `FAMILY`       `F0047`      `MARRIAGE`   autre mariage de Jean

`owner_type` est le type du propriétaire de la cible temporelle.

## 6.4 Exemples

Pour la naissance de Jean :

``` python
TemporalTarget(
    owner_type=TemporalOwnerType.PERSON,
    owner_id="I0100",
    semantic=TargetSemantic.BIRTH,
)
```

Pour le mariage de Jean et Marie :

``` python
TemporalTarget(
    owner_type=TemporalOwnerType.FAMILY,
    owner_id="F0020",
    semantic=TargetSemantic.MARRIAGE,
)
```

------------------------------------------------------------------------

# 7. `TemporalEvidence`

## 7.1 Rôle

`TemporalEvidence` représente un fait temporel utilisé comme preuve par
une règle.

Il existe deux catégories de références sources :

``` text
PersonEventRef
→ une PERSONNE participe à un événement
→ PRINCIPAL, WITNESS, INFORMANT, etc.

FamilyEventRef
→ une FAMILLE est rattachée à un événement
→ FAMILY
```

Le moteur doit gérer les deux.

``` python
class EvidenceOwnerType(str, Enum):
    PERSON = "PERSON"
    FAMILY = "FAMILY"
```
## 7.2 Construction de TemporalEvidence

`TemporalEvidence` n'est pas construit directement à partir d'un objet
isolé de `RawGenealogyData`.

Sa construction repose sur deux composants intermédiaires :

1. `EventReferenceIndex`
2. `TemporalEvidenceBuilder`

La chaîne de construction est :

RawGenealogyData
    ↓
EventReferenceIndex
    ↓
TemporalEvidenceBuilder
    ↓
TemporalEvidence

#### EventReferenceIndex

`EventReferenceIndex` constitue une vue inversée des références
d'événements contenues dans `RawGenealogyData`.

À partir d'un `event_id`, il permet de retrouver les personnes et les
familles qui référencent cet événement ainsi que leur rôle.

Il n'effectue aucune interprétation généalogique ou temporelle.
Il conserve notamment les rôles `UNKNOWN`.

Il ne produit ni `TemporalEvidence`, ni `TemporalConstraint`.

#### TemporalEvidenceBuilder

`TemporalEvidenceBuilder` utilise `RawGenealogyData` et
`EventReferenceIndex` pour construire les objets `TemporalEvidence`.

Contrairement à `EventReferenceIndex`, il effectue une interprétation
contrôlée des références d'événements.

Il détermine notamment :

- si l'événement peut produire une preuve temporelle ;
- si sa date est utilisable comme preuve ;
- quelle référence constitue le propriétaire (`owner`) de la preuve ;
- quel objet est le propriétaire principal (`principal_owner`) de
  l'événement ;
- quelles références ou quels rôles doivent être exclus de la
  construction d'une preuve.

Un même événement peut produire plusieurs objets `TemporalEvidence`.

`TemporalEvidenceBuilder` ne produit aucune `TemporalConstraint`.
L'exploitation d'une preuve pour un `TemporalTarget` appartient aux
`Rule`.

#### TEB001 — Naissance avec personne principale

Pour un événement `BIRTH` possédant une date utilisable et une
référence `PERSON / PRINCIPAL`, `TemporalEvidenceBuilder` produit une
`TemporalEvidence` dont cette personne est :

- le propriétaire de la référence (`owner`) ;
- le propriétaire principal de l'événement (`principal_owner`).

Ainsi, pour la naissance `E1234` de `I_JOSEPH` :

owner_type = PERSON
owner_id = I_JOSEPH
principal_owner_type = PERSON
principal_owner_id = I_JOSEPH


#### TEB002 — Référence secondaire à un événement principal

Lorsqu'une personne référence, avec un rôle admissible tel que `WITNESS`, 
un événement dont une autre personne a été identifiée comme propriétaire 
principal, `TemporalEvidenceBuilder` peut produire une `TemporalEvidence` 
pour cette référence.

`owner_id` désigne la personne qui porte la référence ; 
`principal_owner_id` désigne la personne à laquelle l'événement se 
rapporte principalement.

#### TEB003 — Détermination du propriétaire principal par le rôle

Pour un événement référencé par des personnes, une référence dont le rôle est `PRINCIPAL` désigne le `principal_owner` de l’événement.

Le  `principal_owner_type` est alors `PERSON` et le `principal_owner_id` est l’identifiant de cette personne.

#### TEB004 — Propriétaire principal d’un événement de famille

Pour un événement `MARRIAGE` possédant une `FamilyEventRef` de rôle `FAMILY`, cette famille est le `principal_owner` de l’événement.

`principal_owner_type = FAMILY`
et `principal_owner_id = family_id`.

#### TEB005 — Absence de propriétaire principal suffisamment établi
Si `TemporalEvidenceBuilder` ne peut pas déterminer un `principal_owner` à partir des références explicites de l’événement, il ne construit pas de `TemporalEvidence` nécessitant ce propriétaire principal. Il ne déduit ni ne reconstruit implicitement cette information à partir de la structure généalogique. Le cas pourra être signalé par un diagnostic afin que l’utilisateur vérifie ou corrige les données dans Gramps.

#### TEB006 — Rôles secondaires d’existence
Une référence `WITNESS` ou `INFORMANT`, lorsqu’elle est associée à un événement temporellement exploitable et suffisamment qualifié, peut produire une `TemporalEvidence` attestant que la personne était vivante à la date de l’événement.
Aucune autre propriété, notamment liée à l’âge, à la majorité ou à la capacité juridique, n’est déduite du seul rôle.

#### TEB007 — Événement DEATH
Pour un événement `DEATH` suffisamment qualifié et dont la date est utilisable, une référence `PERSON / PRINCIPAL` permet d'identifier cette personne comme principal_owner. Les références admissibles `WITNESS` et `INFORMANT` au même événement peuvent également produire des `TemporalEvidence`, en conservant comme `principal_owner` la personne identifiée par la référence `PRINCIPAL`.

#### TEB008 — Unicité du propriétaire principal d'un événement individuel
Pour un événement individuel `BIRTH`, `BAPTISM`, `DEATH` ou `BURIAL`, `TemporalEvidenceBuilder` exige exactement une référence `PERSON / PRINCIPAL`.

0 référence `PRINCIPAL` → événement rejeté pour la construction de `TemporalEvidence` ;
1 référence `PRINCIPAL` → situation nominale ;
plusieurs références `PRINCIPAL` → événement rejeté.

Le Builder ne tente ni de choisir un principal parmi plusieurs, ni de reconstruire un principal manquant à partir d’autres données de `RawGenealogyData`.

#### TEB009 — Unicité du propriétaire principal d’un événement familial
Pour un événement familial `MARRIAGE` ou `DIVORCE`, `TemporalEvidenceBuilder` exige exactement une référence `FAMILY / FAMILY`.

0 référence F`FAMILY / FAMILY` → événement rejeté pour la construction de TemporalEvidence ;
1 référence `FAMILY / FAMILY` → situation nominale ;
plusieurs références `FAMILY / FAMILY` → événement rejeté.

Le Builder ne tente ni de choisir une famille parmi plusieurs, ni de reconstruire une famille principale à partir des seules références de personnes ou de la structure généalogique.

#### TEB010 — Validation préalable du propriétaire principal
`TemporalEvidenceBuilder` ne construit aucune `TemporalEvidence` à partir d’un événement tant que son `principal_owner` n’a pas été déterminé de manière unique et conforme au type de l’événement.

Pour un événement individuel, cela signifie exactement une référence `PERSON / PRINCIPAL`.
Pour un événement familial, cela signifie exactement une référence `FAMILY / FAMILY`.

Si cette condition n’est pas satisfaite, l’événement entier est écarté de la construction des TemporalEvidence, y compris ses références secondaires `WITNESS`, `INFORMANT` ou autres rôles admissibles.

#### TEB011 — Conservation de la sémantique de l'événement
`TemporalEvidenceBuilder` conserve la sémantique exacte de l'événement source. Il ne transforme pas un événement indirect (`BAPTISM`, `BURIAL`, etc.) en événement cible (`BIRTH`, `DEATH`). Toute relation temporelle entre deux sémantiques appartient aux `Rule`.

#### TEB012 — Classification des événements pris en charge
`TemporalEvidenceBuilder` distingue les événements individuels (`BIRTH`, `BAPTISM`, `DEATH`, `BURIAL`) et les événements familiaux (`MARRIAGE`, `DIVORCE`).
Les premiers exigent un `principal_owner` de type `PERSON`, les seconds un `principal_owner` de type `FAMILY`.

Algorithme du TemporalEvidenceBuilder
```text
BUILD(data)

index = EventReferenceIndex.from_data(data)

evidences = []

pour chaque event :

    si semantic non supporté :
        continuer

    si date non utilisable :
        continuer

    refs = index.get(event_id)

    si event individuel :
        principals =
            PERSON / PRINCIPAL

    sinon si event familial :
        principals =
            FAMILY / FAMILY

    si nombre de principals != 1 :
        continuer

    principal = l'unique principal

    pour chaque ref :

        si rôle non admissible :
            continuer

        construire TemporalEvidence
        ajouter à evidences

retourner tuple(evidences)
```

## 7.3 Définition conceptuelle

``` python
@dataclass(frozen=True, slots=True)
class TemporalEvidence:
    owner_type: EvidenceOwnerType
    owner_id: str
    event_id: str
    semantic: EventSemantic
    role: EventRoleSemantic | FamilyRoleSemantic
    date: TemporalValue
    principal_owner_type: TemporalOwnerType
    principal_owner_id: str
```

## 7.4 Exemple --- preuve issue d'une personne

``` python
TemporalEvidence(
    owner_type=EvidenceOwnerType.PERSON,
    owner_id="I0100",
    event_id="E0200",
    semantic=EventSemantic.MARRIAGE,
    role=EventRoleSemantic.WITNESS,
    date=...,
)
```

Cela signifie par exemple que Jean est attesté comme témoin d'un
événement de mariage.

## 7.5 Exemple --- preuve issue d'une famille

``` python
TemporalEvidence(
    owner_type=EvidenceOwnerType.FAMILY,
    owner_id="F0032",
    event_id="E0205",
    semantic=EventSemantic.MARRIAGE,
    role=FamilyRoleSemantic.FAMILY,
    date=...,
)
```

Un événement `MARRIAGE` associé à une famille peut ainsi servir de
preuve temporelle pour les individus qui composent cette famille.

## 7.6 Un événement peut produire plusieurs preuves

Un même `Event` peut produire plusieurs `TemporalEvidence`.

Chaque `TemporalEvidence` peut ensuite produire plusieurs
`TemporalConstraint`.

Exemple :

``` text
Preuve :
Jean WITNESS de E1234 le 12/05/1804

Règle :
WITNESS_AT_EVENT_IMPLIES_ALIVE

Contraintes produites :
Birth(Jean) <= 12/05/1804
Death(Jean) >= 12/05/1804
```

## 7.7 Indépendance des preuves

Des `TemporalEvidence` peuvent être liées entre elles, par exemple
lorsqu'elles proviennent du même `Event`.

Leur accumulation ne doit pas provoquer un renforcement artificiel de la
certitude.

La provenance doit donc être conservée afin que le moteur puisse
distinguer plusieurs références à une même source de plusieurs preuves
réellement indépendantes.

## 7.8 Un événement peut ne pas produire de preuve

La présence d’un EventRef pour une personne ne constitue pas, à elle 
seule, une preuve que cette personne était vivante à la date de l’Event. 
La capacité d’un événement à produire une preuve d’existence dépend de 
sa sémantique, du rôle de la personne et de la règle qui l’interprète. 
Certains types d’événements, notamment OCCUPATION, ne sont volontairement 
pas utilisés comme preuves temporelles par le moteur.

## 7.9 Sélection des événements utilisables comme preuves temporelles

Le `TemporalEvidenceBuilder` ne construit une `TemporalEvidence` qu'à partir 
d'un événement et d'une référence satisfaisant les conditions minimales 
permettant de constituer une preuve temporelle valide. Les événements non 
reconnus (`EventSemantic.UNKNOWN`), les rôles `UNKNOWN`, les dates non 
utilisables comme preuve et les données incomplètes sont exclus à ce stade.

La construction d'une `TemporalEvidence` ne signifie cependant pas que 
cette preuve est pertinente pour une `TemporalTarget` donnée. Cette 
pertinence est déterminée ultérieurement par les Rule. Une 
`TemporalEvidence` valide peut donc ne produire aucune `TemporalConstraint`.

## 7.10 Limites du moteur

Le moteur n’a pas pour responsabilité de corriger une mauvaise saisie 
Gramps. Lorsqu’un ensemble de données interprétables produit des 
contraintes incompatibles, `InferenceEngine` signale une contradiction 
et conserve la provenance permettant à l’utilisateur d’identifier les 
données concernées.

## 7.11 Ebauche de l'algorithme
```text
BUILD(data)

1. Vérifier que data est un RawGenealogyData.

2. Construire :
   reference_index = EventReferenceIndex.from_data(data)

3. Initialiser :
   evidences = []

4. Pour chaque event dans data.events.values():

   4.1. Vérifier que event.semantic est admissible :
        BIRTH
        BAPTISM
        MARRIAGE
        DIVORCE
        DEATH
        BURIAL
        CENSUS

        Sinon :
        → ignorer l'événement

   4.2. Vérifier que event.date est utilisable comme preuve.

        Sinon :
        → ignorer l'événement

   4.3. Récupérer :
        references = reference_index.get(event.event_id)

   4.4. Déterminer la catégorie de l'événement :

        A. Événement individuel :
           BIRTH
           BAPTISM
           DEATH
           BURIAL

           → principal attendu :
             exactement 1 PERSON / PRINCIPAL

        B. Événement familial :
           MARRIAGE
           DIVORCE

           → principal attendu :
             exactement 1 FAMILY / FAMILY

        C. Événement d'existence individuelle :
           CENSUS

           → principal attendu :
             exactement 1 PERSON / PRINCIPAL

   4.5. Rechercher les candidats principal_owner.

   4.6. Exiger exactement un principal_owner.

        Si 0 :
        → rejeter l'événement

        Si > 1 :
        → rejeter l'événement

        Si 1 :
        → mémoriser principal_owner_type
          et principal_owner_id

   4.7. Examiner chaque référence de l'événement.

        Pour BIRTH / BAPTISM / DEATH / BURIAL :
        → accepter PERSON / PRINCIPAL
        → accepter PERSON / WITNESS
        → accepter PERSON / INFORMANT

        Pour MARRIAGE / DIVORCE :
        → accepter FAMILY / FAMILY
        → accepter PERSON / PRINCIPAL
        → accepter PERSON / WITNESS
        → accepter PERSON / INFORMANT

        Pour CENSUS :
        → accepter uniquement PERSON / PRINCIPAL

        Tous les autres rôles :
        → ignorer

   4.8. Pour chaque référence admissible :
        construire un TemporalEvidence avec :

        owner_type
        owner_id
        event_id
        semantic
        role
        date
        principal_owner_type
        principal_owner_id

        puis ajouter à evidences.

5. Retourner :
   tuple(evidences)
```

------------------------------------------------------------------------

# 8. `Rule`

## 8.1 Rôle

Une `Rule` transforme des informations disponibles dans le contexte en
une ou plusieurs contraintes temporelles.

Une règle doit avoir une responsabilité limitée et être testable
isolément.

## 8.2 Les trois responsabilités d'une règle

Une règle doit répondre à trois questions différentes :

1.  À qui ou dans quel contexte cette règle s'applique-t-elle ?\
    → `applicability`

2.  Si elle s'applique, quelle contrainte produit-elle ?\
    → `inference logic`

3.  Quelle force logique accorder à cette contrainte ?\
    → `strength = HARD / SOFT`

## 8.3 Applicabilité

Une règle non applicable ne produit aucune contrainte.

Exemple conceptuel :

``` text
MaternalRule

Applicabilité :
    person.gender == FEMALE
    relation_to_child == BIRTH

Production :
    contraintes temporelles
```

Une règle sur la maternité n'est donc pas une règle « faible »
lorsqu'elle est appliquée à une personne pour laquelle elle n'a pas de
sens : elle est simplement `NOT_APPLICABLE`.

## 8.4 Contexte et paramètres

L'applicabilité et le paramétrage contextuel sont deux notions
différentes.

``` text
Applicabilité
    ↓
La règle est-elle utilisable ?

Contexte
    ↓
Avec quels paramètres doit-elle être utilisée ?
```

Exemple :

``` text
LifeExpectancyRule

Jean
gender = MALE
époque = XVIIIe siècle
→ profil A

Marie
gender = FEMALE
époque = XVIIIe siècle
→ profil B

Paul
gender = MALE
époque = XXe siècle
→ profil C
```

Les paramètres contextuels ne doivent pas être confondus avec la force
de la règle.

Ils devront également conserver une provenance suffisante lorsque leur
utilisation influence le résultat.

## 8.5 `RuleContext`

`RuleContext`rassemble ce dont une règle peut avoir besoin, sans obliger 
chaque règle à reconstruire des index ou à aller chercher des données.

``` python
@dataclass(frozen=True, slots=True)
class RuleContext:
    data: RawGenealogyData
    evidences: tuple[TemporalEvidence, ...]
```

## 8.6 Interface conceptuelle

``` python
class Rule:
    rule_id: str
    strength: ConstraintStrength

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        ...

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:
        ...
```

Flux :

``` text
Rule
 │
 ├── is_applicable(...) == False
 │       ↓
 │   aucune contrainte
 │
 └── is_applicable(...) == True
         ↓
      evaluate(...)
         ↓
 TemporalConstraint
```

`RuleContext` contient les données nécessaires aux règles ;
`Rule.is_applicable()` dit seulement si la règle peut s’appliquer 
au `target` ;
`Rule.evaluate()` produit zéro, une ou plusieurs `TemporalConstraint` ;
une `Rule` ne modifie jamais `RawGenealogyData`, `TemporalEvidence` 
ni `TemporalValue`.
```python
from dataclasses import dataclass

from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.temporal_evidence import TemporalEvidence


@dataclass(frozen=True, slots=True)
class RuleContext:
    data: RawGenealogyData
    evidences: tuple[TemporalEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.data, RawGenealogyData):
            raise TypeError("data must be a RawGenealogyData")

        if not isinstance(self.evidences, tuple):
            raise TypeError("evidences must be a tuple")

        if not all(
            isinstance(evidence, TemporalEvidence)
            for evidence in self.evidences
        ):
            raise TypeError(
                "evidences must contain only TemporalEvidence objects"
            )
```

## 8.7 Force d'une règle

``` python
class ConstraintStrength(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
```

`HARD` représente une condition nécessaire de cohérence.

`SOFT` représente une condition de plausibilité.

La nature `HARD` ou `SOFT` appartient d'abord à la `Rule`, parce que la
règle porte le sens logique du raisonnement.

La contrainte produite hérite ensuite de cette force.

## 8.8 Groupes de preuves

Plusieurs règles peuvent reposer sur des hypothèses apparentées. Leur
accumulation ne doit pas renforcer artificiellement la certitude.

Une `Rule` pourra donc être associée à un groupe conceptuel, par exemple
:

``` python
evidence_group
```

Exemples :

``` text
MaternalAgeRule
    group = BIOLOGICAL_PLAUSIBILITY

PaternalAgeRule
    group = BIOLOGICAL_PLAUSIBILITY

LifeExpectancyRule
    group = DEMOGRAPHIC_PLAUSIBILITY
```

La manière exacte dont `evidence_group` interviendra dans le calcul de
certitude sera définie ultérieurement.

## 8.9 Règles modulaires

Les règles doivent rester indépendantes, testables, activables et
désactivables.

Une règle qui conduit à des résultats incorrects ou absurdes doit
pouvoir être corrigée ou supprimée sans remettre en cause l'architecture
générale du moteur.

## 8.10 Règle `BIRTH_BEFORE_DEATH`

```text
                    BIRTH_BEFORE_DEATH
                           HARD
                             │
              ┌──────────────┴──────────────┐
              │                             │
       target = BIRTH                target = DEATH
              │                             │
       chercher DEATH                chercher BIRTH
       PRINCIPAL de P                PRINCIPAL de P
              │                             │
       ┌──────┼──────┐               ┌──────┼──────┐
       │      │      │               │      │      │
       0      1     >1               0      1     >1
       │      │      │               │      │      │
       ()     │   erreur             ()     │   erreur
              │   données                   │   données
              ▼                             ▼
       BIRTH <= Dmax                 DEATH >= Bmin
              │                             │
              ▼                             ▼
     BEFORE_OR_EQUAL                AFTER_OR_EQUAL
```

Matrice des règles
```text
| Evidence ↓ / Target → | BIRTH                              | MARRIAGE                        | DIVORCE             | DEATH                      |
| --------------------- | ---------------------------------- | ------------------------------- | ------------------- | -------------------------- |
| **BIRTH**             | —                                  | ✓ `M ≥ B` HARD + âges à étudier | — redondant         | ✓ `D ≥ B` HARD + longévité |
| **BAPTISM**           | ✓ `B ≤ Bapt.` HARD                 | —                               | —                   | ✓ `D ≥ Bapt.` HARD         |
| **MARRIAGE**          | ✓ `B ≤ M` HARD + âges à étudier    | —                               | ✓ `Div ≥ M` HARD    | ✓ `D ≥ M` HARD             |
| **DIVORCE**           | ✓ `B ≤ Div` HARD                   | ✓ `M ≤ Div` HARD, même famille  | —                   | ✓ `D ≥ Div` HARD           |
| **CENSUS**            | ✓ `B ≤ C` HARD + longévité         | —                               | —                   | ✓ `D ≥ C` HARD             |
| **DEATH**             | ✓ `B ≤ D` HARD + longévité         | ✓ `M ≤ D` HARD                  | ✓ `Div ≤ D` HARD    | —                          |
| **BURIAL**            | ✓ `B ≤ Bur.` HARD + limite usuelle | ✓ `M ≤ Bur.` HARD               | ✓ `Div ≤ Bur.` HARD | ✓ `D ≤ Bur.` HARD          |
```

------------------------------------------------------------------------

# 9. `TemporalConstraint`

## 9.1 Définition

Une contrainte temporelle est une condition portant sur une valeur
temporelle qui doit être respectée pour que les données restent
cohérentes ou, pour une contrainte `SOFT`, pour satisfaire une hypothèse
de plausibilité.

La combinaison des contraintes peut :

-   resserrer un intervalle ;
-   contribuer au calcul d'une date représentative ;
-   détecter une contradiction ;
-   signaler une incompatibilité avec une hypothèse souple.

## 9.2 Principe retenu

La relation générale peut être exprimée conceptuellement comme :

``` text
Birth(Jean) <= Death(Jean)
```

mais cette relation appartient à la logique de la `Rule`.

Lorsqu'une preuve exploitable est disponible, la règle produit une
contrainte concrète contenant une borne déjà résolue :

``` text
BIRTH(I0100) <= 17/01/1788
```

Le `ConstraintResolver` travaille ainsi sur des bornes concrètes.

## 9.3 Éléments fondamentaux

``` text
TemporalConstraint
├── target
├── operator
├── bound
├── rule_id
├── strength
└── evidences
```

### `target`

C'est ce que l'on cherche à contraindre.

### `operator`

Pour commencer, deux opérateurs suffisent :

``` python
class ConstraintOperator(str, Enum):
    BEFORE_OR_EQUAL = "BEFORE_OR_EQUAL"
    AFTER_OR_EQUAL = "AFTER_OR_EQUAL"
```

### `bound`

La contrainte contient une borne déjà résolue :

``` python
bound: date
```

La représentation exacte des bornes provenant de dates étendues ou
d'intervalles sera précisée lors de l'implémentation.

### `rule_id`

Identifie la règle ayant produit la contrainte.

### `strength`

La force est définie par la `Rule` puis recopiée dans la contrainte.

### `evidences`

La contrainte conserve les preuves qui ont participé à sa production.

## 9.4 Définition conceptuelle

``` python
@dataclass(frozen=True, slots=True)
class TemporalConstraint:
    target: TemporalTarget
    operator: ConstraintOperator
    bound: date
    rule_id: str
    strength: ConstraintStrength
    evidences: tuple[TemporalEvidence, ...]
```

## 9.5 Autonomie de la contrainte

Chaque `TemporalConstraint` conserve une copie de la force de sa règle
afin de rester autonome lors :

-   de la résolution ;
-   du calcul de certitude ;
-   de la production des diagnostics.

Principe architectural :

> La `Rule` décide, la `TemporalConstraint` transporte, le moteur
> interprète.

## 9.6 Explication utilisateur

Le texte explicatif ne doit pas être stocké directement comme texte
libre dans `TemporalConstraint`.

Il devra être produit ultérieurement à partir des objets structurés et
de leur provenance, afin de faciliter :

-   les tests ;
-   la traduction ;
-   les changements de formulation ;
-   les diagnostics détaillés.


## 9.7 Sémantique de `TemporalConstraint`

Une `TemporalConstraint` représente une borne temporelle déduite par une règle
pour un `TemporalTarget` précis.

Structure :

```python
@dataclass(frozen=True, slots=True)
class TemporalConstraint:
    target: TemporalTarget
    operator: ConstraintOperator
    bound: date
    rule_id: str
    strength: ConstraintStrength
    evidences: tuple[TemporalEvidence, ...]
```

`target` désigne la valeur temporelle sur laquelle porte directement la
contrainte.

Exemples :
```text
PERSON I001 / BIRTH
PERSON I001 / DEATH
FAMILY F001 / MARRIAGE
```

`operator`

Deux opérateurs sont initialement définis :
```python
class ConstraintOperator(str, Enum):
    BEFORE_OR_EQUAL = "BEFORE_OR_EQUAL"
    AFTER_OR_EQUAL = "AFTER_OR_EQUAL"
```
Ils sont toujours interprétés relativement au `target`.

`bound` est la date limite produite par la règle.

Il s'agit d'une date normalisée dans le calendrier interne du moteur,
c'est-à-dire le calendrier grégorien proleptique utilisé par le modèle.

La borne ne constitue pas nécessairement une estimation de la date du `target`.

`rule_id` identifie la règle ayant produit la contrainte.

`strength` indique la nature logique de la contrainte :
``python
ConstraintStrength.HARD
ConstraintStrength.SOFT
```
Une contrainte `HARD` représente une relation considérée comme nécessaire par
le moteur.

Une contrainte `SOFT` représente une relation heuristique ou de plausibilité.

La force est définie par la `Rule` qui produit la contrainte.

`evidences` contient exactement les `TemporalEvidence` ayant servi à produire
la contrainte.

Cela permet au moteur de conserver la justification complète de la déduction.

## 9.8 Utilisation d'une preuve temporelle définie par un intervalle


Une `TemporalEvidence` peut contenir une date ponctuelle ou un intervalle
temporel :

```text
[normalized_minimum, normalized_maximum]

```text
Pour une TemporalEvidence définie par un intervalle [minimum, maximum] :

BEFORE_OR_EQUAL
    → utiliser normalized_maximum

AFTER_OR_EQUAL
    → utiliser normalized_minimum
```

------------------------------------------------------------------------

# 10.  RuleContext

`RuleContext` regroupe les données dont une règle temporelle peut avoir besoin
pour déterminer son applicabilité et produire des contraintes.

Il ne contient aucune logique d'inférence.

Version minimale :

```python
@dataclass(frozen=True, slots=True)
class RuleContext:
    data: RawGenealogyData
    evidences: tuple[TemporalEvidence, ...]
``` 

Interface conceptuelle :

```python
class Rule:
    rule_id: str
    strength: ConstraintStrength

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        ...

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:
        ...
```

`is_applicable()` indique si une règle peut être considérée pour un
`TemporalTarget` donné.

`evaluate()` examine le RuleContext et produit zéro, une ou plusieurs
TemporalConstraint.
```python
def evaluate(
    self,
    target: TemporalTarget,
    context: RuleContext,
) -> tuple[TemporalConstraint, ...]:
    ...
```

------------------------------------------------------------------------

# 11. Contradictions et diagnostics

## 11.1 Contradiction entre événements différents

En cas de contradiction, le moteur doit conserver les preuves
responsables afin que l'utilisateur puisse identifier les données Gramps
incompatibles.

Exemple :

``` text
CONTRADICTION TEMPORELLE

Cible :
    BIRTH de I0100 — Jean PARIS

Preuve 1 :
    Event E0205
    type : MARRIAGE
    propriétaire : Family F0032
    date : 14/02/1780

Preuve 2 :
    Event E0310
    type : DEATH
    propriétaire : Person I0100
    rôle : PRINCIPAL
    date : 12/01/1779

Résultat :
    les contraintes produites sont incompatibles.

Conclusion :
    Jean ne peut pas participer à un mariage après son décès.
```

Le moteur ne corrige pas automatiquement les données. Il permet à
l'utilisateur de retrouver les événements concernés dans Gramps.

## 11.2 Incohérence entre références d'un même événement

Un même `Event` peut produire plusieurs `TemporalEvidence`.

Si deux preuves issues du même `event_id` conduisent à des contraintes
incompatibles, le diagnostic doit distinguer ce cas d'une contradiction
entre deux événements différents.

Exemple :

``` text
INCOHÉRENCE ENTRE LES RÉFÉRENCES ASSOCIÉES À L'ÉVÉNEMENT

Event : E0205
Type : MARRIAGE
Date : 14/02/1780

TemporalEvidence 1
    propriétaire : Family F0032
    rôle : FAMILY
    → contrainte A

TemporalEvidence 2
    propriétaire : Person I0100
    rôle : WITNESS
    → contrainte B

Résultat :
    les contraintes A et B sont incompatibles.

Conclusion :
    les preuves temporelles dérivées de l'événement E0205
    sont incompatibles via ses rattachements dans Gramps.
```

Cette formulation évite d'affirmer que l'`Event` lui-même est
nécessairement incorrect : l'incohérence peut provenir de ses
références.

## 11.3 Niveaux de conflit selon la force

Conceptuellement :

``` text
HARD + HARD
→ contradiction logique potentiellement bloquante

HARD + SOFT
→ hypothèse de plausibilité non satisfaite

SOFT + SOFT
→ incompatibilité entre heuristiques à diagnostiquer
```

La politique exacte de résolution de ces cas sera définie lors de la
conception du `ConstraintResolver`.

------------------------------------------------------------------------

# 12. Résultat du moteur

## 12.1 Résultat temporel

Le moteur fournit :

-   soit une date représentative et sa justification si le calcul
    aboutit ;
-   soit un diagnostic si le calcul conduit à une contradiction ;
-   soit l'absence de valeur représentative si les informations sont
    insuffisantes.

Exemple :

``` text
Personne : I0234
Événement : BIRTH

TemporalValue
    minimum = 1782
    maximum = 1786
    representative_value = 1784
    value_origin = INFERRED
    certainty = PROBABLE

Justifications
    - mariage en 1804
    - premier enfant en 1807
    - frère aîné né en 1781
```

## 12.2 Exemple de contradiction avec une borne Gramps

``` text
CONTRADICTION TEMPORELLE

Date Gramps :
    naissance entre 1735 et 1745

Contrainte déduite :
    naissance après 1748

Règle :
    ...

Conclusion :
    aucune date ne satisfait simultanément
    les données et la règle.
```

## 12.3 Absence de conclusion

Si les contraintes ne permettent pas de choisir une valeur
représentative justifiable :

``` python
representative_value = None
```

Le moteur ne doit jamais inventer arbitrairement une date.

------------------------------------------------------------------------

# 13. Stratégie d'implémentation progressive

## 13.1 Principe

Le moteur est construit progressivement à partir de règles
indépendantes.

Chaque règle doit pouvoir être :

-   testée isolément ;
-   activée ou désactivée ;
-   corrigée ;
-   supprimée sans modifier les autres règles.

Une nouvelle règle n'est intégrée qu'après validation sur des cas
simples puis sur des données Gramps réelles.

## 13.2 Cycle de validation d'une règle

``` text
1. Définir une règle
        ↓
2. Définir précisément son applicabilité
        ↓
3. Définir sa force HARD / SOFT
        ↓
4. Définir les TemporalEvidence qu'elle utilise
        ↓
5. Définir les TemporalConstraint qu'elle produit
        ↓
6. Tester des cas unitaires simples
        ↓
7. Tester les contradictions
        ↓
8. Tester sur de vraies généalogies
        ↓
9. Valider, corriger ou supprimer la règle
```

## 13.3 Premières règles recommandées

La première implémentation doit privilégier des règles `HARD` simples et
faciles à vérifier.

Exemples :

``` text
BIRTH <= DEATH
```

et :

``` text
Personne attestée à la date D
→ BIRTH <= D
→ DEATH >= D
```

Ces règles permettront de tester toute la chaîne :

``` text
Event
↓
PersonEventRef / FamilyEventRef
↓
TemporalEvidence
↓
Rule
↓
TemporalConstraint
↓
ConstraintResolver
↓
Inference / Diagnostic
```

## 13.4 Règles plus complexes reportées

Après validation de cette chaîne pourront être introduites
progressivement :

-   âge au mariage ;
-   âge maternel ou paternel ;
-   ordre des enfants ;
-   espérance de vie ;
-   règles démographiques contextuelles ;
-   combinaisons de règles `SOFT`.

Ces règles nécessiteront une attention particulière à :

-   l'applicabilité ;
-   la provenance des paramètres ;
-   l'indépendance des preuves ;
-   la prévention des renforcements artificiels ;
-   la détection des dépendances circulaires.

------------------------------------------------------------------------

# État de conception

À ce stade, les concepts suivants sont identifiés :

``` text
TemporalTarget
TemporalEvidence
Rule
RuleContext
ConstraintStrength
ConstraintOperator
TemporalConstraint
ConstraintResolver
```

Les structures Python définitives ne sont pas encore figées. Elles
seront validées progressivement avant implémentation.

---

`TemporalEvidence`

```python
@dataclass(frozen=True, slots=True)
class TemporalEvidence:
    owner_type: EvidenceOwnerType
    owner_id: str

    event_id: str
    semantic: EventSemantic
    role: EventRoleSemantic | FamilyRoleSemantic
    date: TemporalValue

    principal_owner_type: TemporalOwnerType
    principal_owner_id: str
```
```text
TemporalEvidence
├── qui fournit la preuve ?
│   ├── owner_type
│   └── owner_id
│
├── à quel événement ?
│   ├── event_id
│   ├── semantic
│   ├── role
│   └── date
│
└── quel est l'objet principal de cet événement ?
    ├── principal_owner_type
    └── principal_owner_id
```

`TemporalConstraint`

```python
@dataclass(frozen=True, slots=True)
class TemporalConstraint:
    target: TemporalTarget
    operator: ConstraintOperator
    bound: date
    rule_id: str
    strength: ConstraintStrength
    evidences: tuple[TemporalEvidence, ...]
```
```text
TemporalConstraint
│
├── target
│      sur QUOI porte la contrainte ?
│      → DEATH(Victor LOUIS)
│
├── operator + bound
│      QUELLE contrainte ?
│      → >= 12/01/1790
│
├── rule_id + strength
│      POURQUOI le moteur a-t-il le droit de la produire ?
│      → WITNESS_AT_EVENT_IMPLIES_ALIVE
│      → HARD
│
└── evidences
       À PARTIR DE QUELLES PREUVES ?
       → Victor LOUIS
         WITNESS
         BIRTH de Joseph PLOU
         12/01/1790
```
Dans la première version du moteur, toute `TemporalConstraint` possède une 
borne absolue de type `date`. Les relations entre deux `TemporalTarget`
appartiennent aux `Rule`, qui les transforment en contraintes datées dès 
que les preuves disponibles le permettent. Une éventuelle représentation 
de contraintes relationnelles pourra être introduite ultérieurement si 
la propagation entre cibles le nécessite.

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TemporalConstraint:
    target: TemporalTarget
    operator: ConstraintOperator
    bound: date
    rule_id: str
    strength: ConstraintStrength
    evidences: tuple[TemporalEvidence, ...]

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")

        if not isinstance(self.evidences, tuple):
            raise TypeError("evidences must be a tuple")

        if not self.evidences:
            raise ValueError(
                "TemporalConstraint must contain at least one evidence"
            )

        if not isinstance(self.bound, date):
            raise TypeError("bound must be a date")
```

Les événements dont `semantic == EventSemantic.UNKNOWN` sont exclus lors 
de la construction des preuves temporelles. Ils restent intégralement 
conservés dans le modèle, mais ne produisent aucune `TemporalEvidence` et 
ne peuvent donc produire aucune `TemporalConstraint`. Plus généralement, 
l'utilisation d'un événement comme preuve repose sur une autorisation 
explicite de sa sémantique et de son rôle par les règles du moteur.
Ainsi, une `TemporalConstraint` n'existe que lorsqu'une Rule a réellement 
réussi à établir une relation temporelle entre une Evidence et la Target.

## Matrices Target / Event / Role

Les matrices suivantes permettent de visualiser les relations possibles entre :

- la `TemporalTarget` recherchée (`BIRTH`, `MARRIAGE`, `DEATH`) ;
- le type (`EventSemantic`) d'un événement associé à une personne ou une famille ;
- le rôle (`EventRoleSemantic`) de la personne dans cet événement.

Elles ne constituent pas directement l'implémentation des `Rule`.
Elles servent à identifier les situations dans lesquelles une
`TemporalEvidence` peut permettre à une `Rule` de produire une
`TemporalConstraint`.

Principes de lecture :

- **Rule : ...** : une relation temporelle directe existe entre
  l'événement et la Target ; une Rule pourra produire une
  `TemporalConstraint`.
- **Pas de Rule directe** : l'événement peut constituer une
  `TemporalEvidence`, mais cette Evidence ne permet pas de produire
  directement une contrainte pour cette Target.
- **Impossible : c'est la Target** : l'événement correspond directement
  à la Target recherchée. Sa valeur temporelle relève du `TemporalValue`
  de la Target et non d'une `TemporalConstraint` produite par inférence.
- **Exclu** : les événements `EventSemantic.UNKNOWN` ne produisent pas
  de `TemporalEvidence` et sont exclus du raisonnement temporel.


### Target = BIRTH

| Role \ Event | BIRTH | BAPTISM | MARRIAGE | DIVORCE | DEATH | BURIAL | UNKNOWN |
|---|---|---|---|---|---|---|---|
| **PRINCIPAL** | Impossible : c'est la Target | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Exclu |
| **INFORMANT** | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Exclu |
| **WITNESS** | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Rule : Birth avant | Exclu |

Principe général :

Lorsqu'une personne participe de manière temporellement significative
à un événement daté, cette participation peut prouver qu'elle était
déjà née à la date de cet événement.

Exemple :

Victor LOUIS est `WITNESS` à la naissance de Joseph PLOU
le 12/01/1790.

La Rule peut produire :

    BIRTH(Victor LOUIS) <= 12/01/1790

Une Rule SOFT pourra éventuellement produire ultérieurement une borne
plus restrictive selon le contexte, par exemple en utilisant un âge
minimal plausible pour certains rôles.


### Target = MARRIAGE

| Role \ Event | BIRTH | BAPTISM | MARRIAGE | DIVORCE | DEATH | BURIAL | UNKNOWN |
|---|---|---|---|---|---|---|---|
| **PRINCIPAL** | Rule : Marriage après | Rule : Marriage après | Impossible : c'est la Target | Rule : Marriage avant | Rule : Marriage avant | Rule : Marriage avant | Exclu |
| **INFORMANT** | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Exclu |
| **WITNESS** | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Pas de Rule directe | Exclu |

La Target `MARRIAGE` présente une particularité importante.

Une preuve établissant seulement l'existence d'une personne à une date
ne permet généralement pas de situer directement son mariage.

Exemple :

Jean est `WITNESS` à l'enterrement de Simon le 12/01/1790.

Cette participation constitue une `TemporalEvidence` valable pour Jean
et peut notamment permettre de produire :

    BIRTH(Jean) <= 12/01/1790

et :

    DEATH(Jean) >= 12/01/1790

En revanche, elle ne permet pas de déterminer si le mariage de Jean
et Sophie a eu lieu avant ou après le 12/01/1790.

Pour :

    MARRIAGE(Jean, Sophie)

aucune Rule directe n'est donc applicable.

La chaîne de raisonnement s'arrête :

    TemporalEvidence
        ↓
    aucune Rule applicable à cette Target
        ↓
    aucune TemporalConstraint

L'absence de `TemporalConstraint` ne signifie donc pas que la
`TemporalEvidence` est invalide. Elle signifie seulement qu'aucune
relation temporelle directe n'existe entre cette Evidence et la Target
considérée.


### Target = DEATH

| Role \ Event | BIRTH | BAPTISM | MARRIAGE | DIVORCE | DEATH | BURIAL | UNKNOWN |
|---|---|---|---|---|---|---|---|
| **PRINCIPAL** | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Impossible : c'est la Target | Rule : Death avant | Exclu |
| **INFORMANT** | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Exclu |
| **WITNESS** | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Rule : Death après | Exclu |

Principe général :

Lorsqu'une personne participe de manière temporellement significative
à un événement daté, cette participation peut prouver qu'elle était
encore vivante à cette date.

Exemple :

Victor LOUIS est `WITNESS` à la naissance de Joseph PLOU
le 12/01/1790.

La Rule peut produire :

    DEATH(Victor LOUIS) >= 12/01/1790


### Interruption de la chaîne de raisonnement

La création d'une `TemporalConstraint` n'est jamais obligatoire.

Plusieurs niveaux d'arrêt sont possibles :

    PersonEventRef / FamilyEventRef
                ↓
          Event interprétable ?
           NON ───────────────→ STOP
                ↓ OUI
        TemporalEvidence
                ↓
      Rule applicable à cette
      Evidence et cette Target ?
           NON ───────────────→ STOP
                ↓ OUI
       TemporalConstraint

Ainsi :

1. un `EventSemantic.UNKNOWN` ne produit aucune `TemporalEvidence` ;

2. un événement interprétable peut produire une `TemporalEvidence`
   sans qu'aucune Rule ne soit applicable à la Target recherchée ;

3. une `TemporalConstraint` n'est créée que lorsqu'une Rule applicable
   peut effectivement établir une borne temporelle pour la Target.

Par conséquent, il n'existe pas de `TemporalConstraint` « vide » ou
« non valide » destinée à représenter l'absence de résultat.

Toute `TemporalConstraint` existante possède nécessairement :

- une `TemporalTarget` ;
- un `ConstraintOperator` ;
- une borne absolue (`bound`) ;
- la `Rule` qui l'a produite (`rule_id`) ;
- sa force (`HARD` ou `SOFT`) ;
- au moins une `TemporalEvidence` justifiant sa production.

---

Les classes

`TemporalTarget`
```python
"""Cible d'un calcul d'inférence temporelle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TemporalOwnerType(str, Enum):
    """Type d'objet propriétaire d'une cible temporelle."""

    PERSON = "PERSON"
    FAMILY = "FAMILY"


class TargetSemantic(str, Enum):
    """Sémantiques temporelles pouvant être recherchées par le moteur."""

    BIRTH = "BIRTH"
    MARRIAGE = "MARRIAGE"
    DEATH = "DEATH"


@dataclass(frozen=True, slots=True)
class TemporalTarget:
    """Identifie précisément la valeur temporelle recherchée.

    Une naissance et un décès appartiennent à une personne.
    Un mariage appartient à une famille.
    """

    owner_type: TemporalOwnerType
    owner_id: str
    semantic: TargetSemantic

    def __post_init__(self) -> None:
        if not isinstance(self.owner_type, TemporalOwnerType):
            raise TypeError("owner_type must be a TemporalOwnerType")

        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id must be a non-empty string")

        if not isinstance(self.semantic, TargetSemantic):
            raise TypeError("semantic must be a TargetSemantic")

        if self.semantic in (TargetSemantic.BIRTH, TargetSemantic.DEATH):
            if self.owner_type is not TemporalOwnerType.PERSON:
                raise ValueError(
                    "BIRTH and DEATH targets must belong to a PERSON"
                )

        if self.semantic is TargetSemantic.MARRIAGE:
            if self.owner_type is not TemporalOwnerType.FAMILY:
                raise ValueError(
                    "MARRIAGE targets must belong to a FAMILY"
                )
```

`TemporalEvidence`
```python
"""Preuve temporelle utilisable par le moteur d'inférence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .event import EventSemantic
from .family_event_ref import FamilyRoleSemantic
from .person_event_ref import EventRoleSemantic
from .temporal import TemporalValue
from .temporal_target import TemporalOwnerType


class EvidenceOwnerType(str, Enum):
    """Type d'objet dont une référence à l'évènement fournit la preuve."""

    PERSON = "PERSON"
    FAMILY = "FAMILY"


@dataclass(frozen=True, slots=True)
class TemporalEvidence:
    """Preuve temporelle dérivée d'une référence à un évènement.

    ``owner_id`` identifie la personne ou la famille dont la référence
    constitue la preuve.

    ``principal_owner_id`` identifie la personne ou la famille principalement
    concernée par l'évènement.
    """

    owner_type: EvidenceOwnerType
    owner_id: str

    event_id: str
    semantic: EventSemantic
    role: EventRoleSemantic | FamilyRoleSemantic
    date: TemporalValue

    principal_owner_type: TemporalOwnerType
    principal_owner_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.owner_type, EvidenceOwnerType):
            raise TypeError("owner_type must be an EvidenceOwnerType")

        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id must be a non-empty string")

        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        if not isinstance(self.semantic, EventSemantic):
            raise TypeError("semantic must be an EventSemantic")

        if self.semantic is EventSemantic.UNKNOWN:
            raise ValueError(
                "EventSemantic.UNKNOWN cannot produce a TemporalEvidence"
            )

        if not isinstance(
            self.role,
            (EventRoleSemantic, FamilyRoleSemantic),
        ):
            raise TypeError(
                "role must be an EventRoleSemantic or FamilyRoleSemantic"
            )

        if self.role in (
            EventRoleSemantic.UNKNOWN,
            FamilyRoleSemantic.UNKNOWN,
        ):
            raise ValueError(
                "an UNKNOWN role cannot produce a TemporalEvidence"
            )

        if not isinstance(self.date, TemporalValue):
            raise TypeError("date must be a TemporalValue")

        if not self.date.is_usable_as_evidence:
            raise ValueError(
                "TemporalEvidence requires a TemporalValue usable as evidence"
            )

        if not isinstance(self.principal_owner_type, TemporalOwnerType):
            raise TypeError(
                "principal_owner_type must be a TemporalOwnerType"
            )

        if (
            not isinstance(self.principal_owner_id, str)
            or not self.principal_owner_id.strip()
        ):
            raise ValueError(
                "principal_owner_id must be a non-empty string"
            )
```

`TemporalConstraint`
```python
"""Contrainte temporelle produite par une règle d'inférence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .temporal_evidence import TemporalEvidence
from .temporal_target import TemporalTarget


class ConstraintOperator(str, Enum):
    """Sens d'une borne temporelle absolue."""

    BEFORE_OR_EQUAL = "BEFORE_OR_EQUAL"
    AFTER_OR_EQUAL = "AFTER_OR_EQUAL"


class ConstraintStrength(str, Enum):
    """Force logique de la règle ayant produit la contrainte."""

    HARD = "HARD"
    SOFT = "SOFT"


@dataclass(frozen=True, slots=True)
class TemporalConstraint:
    """Borne temporelle concrète produite par une Rule.

    Une TemporalConstraint ne représente jamais directement une borne
    saisie dans Gramps. Les bornes Gramps restent portées par TemporalValue.
    """

    target: TemporalTarget
    operator: ConstraintOperator
    bound: date
    rule_id: str
    strength: ConstraintStrength
    evidences: tuple[TemporalEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.target, TemporalTarget):
            raise TypeError("target must be a TemporalTarget")

        if not isinstance(self.operator, ConstraintOperator):
            raise TypeError("operator must be a ConstraintOperator")

        if not isinstance(self.bound, date):
            raise TypeError("bound must be a date")

        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")

        if not isinstance(self.strength, ConstraintStrength):
            raise TypeError("strength must be a ConstraintStrength")

        if not isinstance(self.evidences, tuple):
            raise TypeError("evidences must be a tuple")

        if not self.evidences:
            raise ValueError(
                "TemporalConstraint must contain at least one evidence"
            )

        if not all(
            isinstance(evidence, TemporalEvidence)
            for evidence in self.evidences
        ):
            raise TypeError(
                "evidences must contain only TemporalEvidence objects"
            )
```

---

`TemporalEvidenceBuilder`
Le `TemporalEvidenceBuilder` produit toutes les preuves temporelles valides qu'il 
peut dériver des références d'événements disponibles. Il ne détermine pas leur 
pertinence pour une cible donnée. Les `Rule` déterminent ensuite quelles 
`TemporalEvidence` peuvent produire une ou plusieurs `TemporalConstraint` pour 
la `TemporalTarget` étudiée.

Les preuves temporelles peuvent provenir des `PersonEventRef` et des `FamilyEventRef`.
On conserve donc l'attribut `owner_type` dans la classe pour garder ce lien.
```text
RawGenealogyData
│
├── Persons
│     └── PersonEventRef
│            ↓
│      EvidenceOwnerType.PERSON
│
└── Families
      └── FamilyEventRef
             ↓
       EvidenceOwnerType.FAMILY
```
`EventReferenceIndex`
Pour pouvoir trouver tous les individus assocciés à un `event`, il est 
nécessaire de construire un dictionnaire inversé.
A partir de :
```text
RawGenealogyData
│
├── Person
│    └── event_refs
│
└── Family
     └── event_refs
```
on construit
```text
EventReferenceIndex
│
├── E1234
│    ├── PERSON / I_JOSEPH / PRINCIPAL
│    ├── PERSON / I_VICTOR / WITNESS
│    └── PERSON / I_ANNE / INFORMANT
│
└── E5678
     ├── FAMILY / F0010 / FAMILY
     └── ...
```
Ce programme est placé dans la branche `inference`, pas dans `model`, 
car `EventReferenceIndex` est une vue technique dérivée, reconstruisible à 
tout moment à partir de `RawGenealogyData`.
```text
src/descendants_timeline/
│
├── model/
│    ├── temporal_target.py
│    ├── temporal_evidence.py
│    └── temporal_constraint.py
│
└── inference/
     ├── event_reference_index.py
     └── temporal_evidence_builder.py
```

---

`EventReferenceIndex`
`EventReferenceIndex` est une vue inversée, interne au moteur d'inférence, 
des références d'événements contenues dans `RawGenealogyData`. Pour chaque 
`event_id`, il permet de retrouver les personnes et les familles qui 
référencent cet événement ainsi que le rôle porté par chacune de ces 
références.

Il ne contient aucune information généalogique nouvelle, n'interprète aucune 
donnée et ne modifie pas `RawGenealogyData`.
L’ordre des `EventReferenceEntry` dans `EventReferenceIndex` n’a aucune 
signification temporelle, généalogique ou logique. Il est uniquement conservé 
afin d’assurer un traitement déterministe et reproductible.
