# Gramps Descendants Timeline

## InferenceEngine
**Version :** 0.1  
**Statut :** Brouillon  
**Document :** `07_InferenceEngine.md`

---

# Table des matières

1. Objet du document
2. Etapes de travail
3. Exemple de donnée de sortie
4. Cas d'exécution d'un calcul d'inférence

---

# 1. Objet du document

Le présent document justifie la réalisation du TemporalInferenceEngine
(Milestone 4)

---

# 2. Etapes de travail

## 2.1 Définir la sortie du moteur

quel objet représente une date inférée ;
comment conserver minimum, maximum, representative_value ;
comment stocker les justifications ;
comment conserver les règles ayant participé au calcul.

---

## 2.2 Définir une classe de justification

Par exemple quelque chose comme :
```python
InferenceEvidence
```
qui pourrait dire
```python
source_person_id
source_event_id
rule_id
borne produite
niveau de certitude
texte explicatif
```

---

## 2.3 Définir les règles élémentaires

Une règle = une responsabilité très petite.

Par exemple :
```python
BirthBeforeDeathRule
MarriageAfterBirthRule
ParentBeforeChildBirthRule
BirthOrderRule
```

---

## 2.4 Construire InferenceEngine

Il recevra

```python
RawGenealogyData
```
et produira un résultat temporel enrichi, sans modifier les objets sources.

---

## 2.5 Commencer avec des cas extrêmement simples

Avant les règles complexes, on pourrait tester :
```python
naissance inconnue
+
décès connu
+
mariage connu
→ bornes temporelles simples
```

---

## 2.6 Puis augmenter progressivement la difficulté :

ordre des frères et sœurs ;
dates des enfants ;
âge biologique des parents ;
mariages ;
décès ;
plusieurs preuves convergentes ;
preuves contradictoires ;
impossibilité de conclure → representative_value = None.

---

# 3. Exemples de donnée de sortie

Le moteur d'inférence temporelle fournit
   - soit une date représentative et sa justification si le calcul aboutit,
   - soit un diagnostic si le calcul conduit à une contradiction.

Par exemple, une sortie pourrait ressembler conceptuellement à :
```python
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

ou
```python
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

---


# 4. Cas d'exécution d'un calcul d'inférence

Règle 1 : Le moteur fera à la fois :
```python
A — COMPLÉTER UNE INFORMATION TEMPORELLE

BIRTH : avant 1765
        ↓
autres contraintes
        ↓
resserrement éventuel de la borne
```
et :
```python
B — EXTRAIRE DES CONTRAINTES D'UNE PREUVE

Prisonnier : 1916–1918
        ↓
preuve d'existence
        ↓
BIRTH ≤ 1916
DEATH ≥ 1918
```

Règle 2 : Le moteur exécute ces actions selon la nature du GRAMPS modifier :
```python
1. VALEUR À RESPECTER
   NONE
   ABOUT

   → pas d'inférence sur la date elle-même


2. CONTRAINTE SUR UNE DATE PONCTUELLE À COMPLÉTER
   BEFORE
   AFTER
   RANGE

   → l'inférence peut resserrer les bornes


3. INFORMATION TEMPORELLE UTILISABLE COMME PREUVE
   SPAN
   FROM
   TO

   → ne provoque pas nécessairement l'inférence
     sur l'événement lui-même
   → peut produire des contraintes sur BIRTH/DEATH


4. VALEUR NON INTERPRÉTABLE AUTOMATIQUEMENT
   TEXTONLY


5. AUCUNE VALEUR
   → inférence complète autorisée
`

Règle 3 : « La donnée GRAMPS est souveraine »
Si le généalogiste a saisi le modifier ABOUT pour la date d'un événement, c'est qu'il 
souhaite conserver cette date telle qu'elle. Il ne demande pas de calcul d'inférence.
C'est une sorte de verrou humain implicite.
```python
date vide
→ "essaie de trouver quelque chose"

vers 1740
→ "j'ai choisi mon estimation, n'essaie pas de la modifier"

avant 1740
→ "je connais cette limite ; essaie de préciser"
```

Synthèse des règles 1 à 3 :

| Modifier   | Compléter la date de cet événement | Utilisable comme preuve pour d’autres événements |
| ---------- | ---------------------------------: | -----------------------------------------------: |
| `NONE`     |                                Non |                                              Oui |
| `BEFORE`   |                                Oui |                                              Oui |
| `AFTER`    |                                Oui |                                              Oui |
| `ABOUT`    |                                Non |                                              Oui |
| `RANGE`    |                                Oui |                                              Oui |
| `SPAN`     |                                Non |                                              Oui |
| `TEXTONLY` |                                Non |                              Non automatiquement |
| `FROM`     |      Non pour BIRTH/MARRIAGE/DEATH |                                              Oui |
| `TO`       |      Non pour BIRTH/MARRIAGE/DEATH |                                              Oui |


---
