# Gramps Descendants Timeline

## Traversal — Programme DFS
**Version :** 0.1  
**Statut :** Brouillon
**Document :** `04_Traversal.md`

---

# Table des matières

1. Objet du document
2. Responsabilités
3. Rappel du pipeline
4. Programme
5. Déroulé manuel du programme

---

# 1. Objet du document

Le présent document décrit le programme de parcours en profondeur des descendants d'une
personne racine DescendanceTraversal.

---

# 2. Responsabilités

Le programme reçoit les données :
   RawGenealogyData
   root_person_id
   TraversalOptions

et retourne un TraversalResult qui contient deux tuples :
   rows
      qui contient l’ordre logique des personnes à afficher. Chaque TraversalRow indique
      notamment :
      ```python
      person_id
      generation
      role = ROOT / DESCENDANT / SPOUSE
      family_id
      spouse_of_person_id
      ```
   family_occurrences
      qui contient l’état de chaque famille rencontrée dans le parcours, avec notamment :
      ```python
      family_id
      descendant_person_id
      descendant_row_index
      spouse_person_id
      spouse_row_index
      state = EXPLORED / ALREADY_DESCRIBED
      referenced_row_index
      ```

---


# 3. Rappel du pipeline

(RawGenealogyData)
        ↓
(TemporalInferenceEngine)
        ↓
(TemporalData enrichi)


(RawGenealogyData)
        ↓
DescendanceTraversal
        ↓
TraversalResult


(TemporalData + TraversalResult)
        ↓
(LayoutEngine)
        ↓
(LayoutRows)


(LayoutRows)
        ↓
(Renderer)
   

---

# 4. Programme

```python
"""Parcours DFS de la descendance.

Le module travaille uniquement sur ``RawGenealogyData``. Il ne réalise
aucune inférence temporelle et aucun calcul graphique.

Deux sorties complémentaires sont produites :
- ``rows`` : ordre logique des personnes à afficher ;
- ``family_occurrences`` : état de chaque famille rencontrée dans le parcours.

Cette séparation permet notamment de représenter correctement une personne
ayant plusieurs familles, dont certaines ont déjà été développées et
d'autres non.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from descendants_timeline.model.child_ref import ChildRelation
from descendants_timeline.model.genealogy import RawGenealogyData


class DescendanceMode(str, Enum):
    """Politique d'inclusion des relations enfant-parent dans le DFS."""

    BIOLOGICAL_ONLY = "BIOLOGICAL_ONLY"
    EXTENDED = "EXTENDED"


@dataclass(frozen=True, slots=True)
class TraversalOptions:
    """Options du parcours de descendance."""

    mode: DescendanceMode = DescendanceMode.BIOLOGICAL_ONLY

    def __post_init__(self) -> None:
        if not isinstance(self.mode, DescendanceMode):
            raise TypeError("mode must be a DescendanceMode")


class TraversalRole(str, Enum):
    """Rôle d'une ligne-personne dans le résultat du parcours."""

    ROOT = "ROOT"
    DESCENDANT = "DESCENDANT"
    SPOUSE = "SPOUSE"


class FamilyTraversalState(str, Enum):
    """État d'une occurrence de famille dans le DFS."""

    EXPLORED = "EXPLORED"
    ALREADY_DESCRIBED = "ALREADY_DESCRIBED"


@dataclass(frozen=True, slots=True)
class TraversalRow:
    """Une ligne logique représentant une personne.

    ``generation`` appartient à l'occurrence dans le parcours et non à
    l'objet Person. Une même personne peut donc apparaître avec des
    générations différentes selon la branche parcourue.
    """

    person_id: str
    generation: int
    role: TraversalRole
    family_id: str | None
    spouse_of_person_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.person_id, str) or not self.person_id.strip():
            raise ValueError("person_id must be a non-empty string")

        if not isinstance(self.generation, int) or self.generation < 1:
            raise ValueError("generation must be an integer >= 1")

        if not isinstance(self.role, TraversalRole):
            raise TypeError("role must be a TraversalRole")

        if self.family_id is not None:
            if not isinstance(self.family_id, str) or not self.family_id.strip():
                raise ValueError("family_id must be a non-empty string or None")

        if self.spouse_of_person_id is not None:
            if (
                not isinstance(self.spouse_of_person_id, str)
                or not self.spouse_of_person_id.strip()
            ):
                raise ValueError(
                    "spouse_of_person_id must be a non-empty string or None"
                )

        if self.role is TraversalRole.SPOUSE:
            if self.family_id is None:
                raise ValueError("a SPOUSE row must reference a family_id")
            if self.spouse_of_person_id is None:
                raise ValueError(
                    "a SPOUSE row must reference spouse_of_person_id"
                )


@dataclass(frozen=True, slots=True)
class TraversalFamilyOccurrence:
    """Décrit une famille telle qu'elle est rencontrée dans le parcours.

    ``referenced_row_index`` est un index Python (base 0) vers la ligne du
    descendant qui avait développé cette famille lors de sa première
    occurrence. Il vaut ``None`` pour une famille explorée pour la première fois.
    """

    family_id: str
    descendant_person_id: str
    descendant_row_index: int
    spouse_person_id: str | None
    spouse_row_index: int | None
    state: FamilyTraversalState
    referenced_row_index: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.family_id, str) or not self.family_id.strip():
            raise ValueError("family_id must be a non-empty string")

        if (
            not isinstance(self.descendant_person_id, str)
            or not self.descendant_person_id.strip()
        ):
            raise ValueError("descendant_person_id must be a non-empty string")

        if (
            not isinstance(self.descendant_row_index, int)
            or self.descendant_row_index < 0
        ):
            raise ValueError("descendant_row_index must be an integer >= 0")

        if self.spouse_person_id is None:
            if self.spouse_row_index is not None:
                raise ValueError(
                    "spouse_row_index must be None when spouse_person_id is None"
                )
        else:
            if (
                not isinstance(self.spouse_person_id, str)
                or not self.spouse_person_id.strip()
            ):
                raise ValueError(
                    "spouse_person_id must be a non-empty string or None"
                )
            if (
                not isinstance(self.spouse_row_index, int)
                or self.spouse_row_index < 0
            ):
                raise ValueError(
                    "spouse_row_index must be an integer >= 0 when a spouse exists"
                )

        if not isinstance(self.state, FamilyTraversalState):
            raise TypeError("state must be a FamilyTraversalState")

        if self.state is FamilyTraversalState.EXPLORED:
            if self.referenced_row_index is not None:
                raise ValueError(
                    "an EXPLORED family must not have referenced_row_index"
                )

        if self.state is FamilyTraversalState.ALREADY_DESCRIBED:
            if (
                not isinstance(self.referenced_row_index, int)
                or self.referenced_row_index < 0
            ):
                raise ValueError(
                    "an ALREADY_DESCRIBED family must reference a previous row"
                )


@dataclass(frozen=True, slots=True)
class TraversalResult:
    """Résultat immuable du parcours DFS."""

    root_person_id: str
    rows: tuple[TraversalRow, ...]
    family_occurrences: tuple[TraversalFamilyOccurrence, ...]


class DescendanceTraversal:
    """Construit l'ordre logique d'une descendance par parcours DFS."""

    def traverse(
        self,
        data: RawGenealogyData,
        root_person_id: str,
        options: TraversalOptions | None = None,
    ) -> TraversalResult:
        if not isinstance(data, RawGenealogyData):
            raise TypeError("data must be RawGenealogyData")

        if not isinstance(root_person_id, str) or not root_person_id.strip():
            raise ValueError("root_person_id must be a non-empty string")

        if root_person_id not in data.persons:
            raise ValueError("root_person_id must reference a person present in data")

        if options is None:
            options = TraversalOptions()

        if not isinstance(options, TraversalOptions):
            raise TypeError("options must be TraversalOptions")

        rows: list[TraversalRow] = []
        occurrences: list[TraversalFamilyOccurrence] = []

        # family_id -> index de la ligne descendant ayant développé
        # cette famille lors de sa première rencontre.
        first_family_row: dict[str, int] = {}

        def visit_person(
            person_id: str,
            generation: int,
            role: TraversalRole,
            parent_family_id: str | None,
        ) -> None:
            person = data.persons[person_id]

            descendant_row_index = len(rows)
            rows.append(
                TraversalRow(
                    person_id=person_id,
                    generation=generation,
                    role=role,
                    family_id=parent_family_id,
                    spouse_of_person_id=None,
                )
            )

            for family_id in person.family_ids:
                family = data.families[family_id]

                if family.parent1_id == person_id:
                    spouse_id = family.parent2_id
                    parent_position = 1
                elif family.parent2_id == person_id:
                    spouse_id = family.parent1_id
                    parent_position = 2
                else:
                    raise ValueError(
                        f"Person {person_id} references family {family_id} "
                        "but is not one of its parents"
                    )

                spouse_row_index: int | None = None

                # Même pour une famille déjà développée, le conjoint est affiché
                # afin de conserver la structure du couple dans la vue.
                if spouse_id is not None:
                    spouse_row_index = len(rows)
                    rows.append(
                        TraversalRow(
                            person_id=spouse_id,
                            generation=generation,
                            role=TraversalRole.SPOUSE,
                            family_id=family_id,
                            spouse_of_person_id=person_id,
                        )
                    )

                if family_id in first_family_row:
                    occurrences.append(
                        TraversalFamilyOccurrence(
                            family_id=family_id,
                            descendant_person_id=person_id,
                            descendant_row_index=descendant_row_index,
                            spouse_person_id=spouse_id,
                            spouse_row_index=spouse_row_index,
                            state=FamilyTraversalState.ALREADY_DESCRIBED,
                            referenced_row_index=first_family_row[family_id],
                        )
                    )
                    continue

                first_family_row[family_id] = descendant_row_index

                occurrences.append(
                    TraversalFamilyOccurrence(
                        family_id=family_id,
                        descendant_person_id=person_id,
                        descendant_row_index=descendant_row_index,
                        spouse_person_id=spouse_id,
                        spouse_row_index=spouse_row_index,
                        state=FamilyTraversalState.EXPLORED,
                        referenced_row_index=None,
                    )
                )

                for child_ref in family.child_refs:
                    relation = (
                        child_ref.relation_to_parent1
                        if parent_position == 1
                        else child_ref.relation_to_parent2
                    )

                    if self._include_relation(relation, options.mode):
                        visit_person(
                            person_id=child_ref.person_id,
                            generation=generation + 1,
                            role=TraversalRole.DESCENDANT,
                            parent_family_id=family_id,
                        )

        visit_person(
            person_id=root_person_id,
            generation=1,
            role=TraversalRole.ROOT,
            parent_family_id=None,
        )

        return TraversalResult(
            root_person_id=root_person_id,
            rows=tuple(rows),
            family_occurrences=tuple(occurrences),
        )

    @staticmethod
    def _include_relation(
        relation: ChildRelation,
        mode: DescendanceMode,
    ) -> bool:
        if mode is DescendanceMode.BIOLOGICAL_ONLY:
            return relation is ChildRelation.BIRTH

        if mode is DescendanceMode.EXTENDED:
            return relation in {
                ChildRelation.BIRTH,
                ChildRelation.ADOPTED,
                ChildRelation.SPONSORED,
            }

        raise ValueError(f"Unsupported DescendanceMode: {mode}")
```

---


# 6. Déroulement manuel du programme

## 6.1 Données GRAMPS :

Individu	
Id	NOM
I0001	Paul ABA
I0002	Edgard ABA
I0004	Anne ECE
I0008	Pierre ABA
I0010	Jean ABA
I0011	ALine ABA
I0022	Jeanne ABA
I0023	René ABA
I0044	Marie IDI
I0055	Claire YHY
I0087	Eric ABA
I0110	Léon OFO
I0194	Sophie OFO
I0196	Luc ABA
I0198	Basile OFO
I0199	Odile ABA
I0361	Jeanne BAB
I0778	Rémi BAB
I0779	Rose UZU

Famille		
Family_id	Mari	Femme
F0003		I0001	I0004
F0014		I0001	I0055
F0290		I0010	I0011
F0300		I0198	I0361
F0317		I0010	I0044
F0333		I0087	I0194
F0400			I0199
F0770		I0778	I0779
		
Famille		
Id	Enfant de Family_id	
I0001		
I0002	F0003	
I0004		
I0008	F0014	
I0010	F0003	
I0011	F0003	
I0022	F0400	
I0023	F0400	
I0044		
I0055		
I0087	F0290	
I0110		
I0194	F0300	
I0196	F0333	
I0198	F0290	
I0199	F0333	
I0361	F0770	

---

## 6.2 RawGenealogyData :

persons			
Clé	Personne	parent_family_ids	family_ids
I0001	Paul ABA	()			(F0003,F0014)
I0002	Edgard ABA	(F0003)			()
I0004	Anne ECE	()			(F0003)
I0008	Pierre ABA	(F0014)			()
I0010	Jean ABA	(F0003)			(F0317)
I0011	ALine ABA	(F0003)			(F0290)
I0022	Jeanne ABA	(F0400)			()
I0023	René ABA	(F0400)			()
I0044	Marie IDI	()			(F0317)
I0055	Claire YHY	()			(F0014)
I0087	Eric ABA	(F0317)			(F0333)
I0110	Léon OFO	()			(F0290)
I0194	Sophie OFO	(F0300)			(F0333)
I0196	Luc ABA		(F0333)			()
I0198	Basile OFO	(F0290)			(F0300)
I0199	Odile ABA	(F0333)			(F0400)
I0361	Jeanne BAB	(F0770)			(F0300)
I0778	Rémi BAB	()			(F0770)
I0779	Rose UZU	()			(F0770)
			
families			
Clé	Parent1	Parent2	enfants
F0003	I0001	I0004	(I0010,I0011,I0002)
F0014	I0001	I0055	(I0008)
F0290	I0011	I0110	(I0198)
F0300	I0198	I0361	(I0194)
F0317	I0010	I0044	(I0087)
F0333	I0087	I0194	(I0196,I0199)
F0400		I0199	(I0022,I0023)
F0770	I0778	I0779	(I0361)

---

## 6.3 DFS (parcours) :

Etape 001
Action                   Valeur                 Résultat                                              Pourquoi                                         Pile récursive 
lire I0001.family_ids    ("F0003","F0014")      sélection de F0003                                    première famille de Paul                         I0001/F0003    
chercher F0003           data.families["F0003"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0003 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0003 → 0              dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0004                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0010                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 002                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0010.family_ids    ("F0317")              sélection de F0317                                    famille de Jean                                  I0010/F0317    
chercher F0317           data.families["F0317"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0317 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0317 → 2              dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0044                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0087                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 003                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0087.family_ids    ("F0333")              sélection de F0333                                    famille de Eric                                  I0087/F0333    
chercher F0333           data.families["F0333"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0333 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0333 → 4              dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0194                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0196                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 004                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0196.family_ids    ()                     retour à la lecture de la liste des enfants de F0333  fin de la lignée                                 I0196|         
lire le deuxième enfant  I0199                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 005                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0199.family_ids    ("F0400")              sélection de F0400                                    famille de Odile                                 I0199/F0400    
chercher F0400           data.families["F0400"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0400 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0400 → 7              dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         ()                     pas de ligne                                          parent inconnu                                                  
lire le premier enfant   I0022                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 006                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0022.family_ids    ()                     retour à la lecture de la liste des enfants de F0400  fin de la lignée                                 I0022|         
lire le deuxième enfant  I0023                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 007                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0023.family_ids    ()                     retour à la lecture de la liste des enfants de F0400  fin de la lignée                                 0023|          
lire le troisième enfant ()                     retour à la lecture de la liste des enfants de F0333  fin de la lignée                                 F0400|         
lire le troisième enfant ()                     retour à la lecture de la liste des enfants de F0317  fin de la lignée                                 F0333|         
lire le deuxième enfant  I0011                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 008                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0011.family_ids    ("F0290")              sélection de F0290                                    famille de Aline                                 I0011/F0290    
chercher F0290           data.families["F0290"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0290 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0290 → 10             dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0110                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0198                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 009                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0198.family_ids    ("F0300")              sélection de F0300                                    famille de Basile                                I0198/F0300    
chercher F0300           data.families["F0300"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0300 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0300 → 12             dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0361                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0194                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 010                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0194.family_ids    ("F0333")              sélection de F0333                                    famille de Sophie                                I0194/F0333    
chercher F0333           data.families["F0333"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0333 présent          renvoi du row                                         famille déjà décrite                                            
lire le conjoint         I0087                  ligne SPOUSE                                          afficher le couple, même si famille déjà décrite                
lire le deuxième enfant  ()                     retour à la lecture de la liste des enfants de F0290  fin de la lignée                                 F0300|         
lire le troisième enfant I0002                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 011                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0002.family_ids    ()                     retour à la lecture de la liste des enfants de F0003  fin de la lignée                                 I0002|         
lire le quatrième enfant ()                     retour à la lecture de la liste des familles de I0001 fin de la lignée                                 F0003|         
                                                                                                                                                                      
Etape 012                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0001.family_ids    ("F0003","F0014")      sélection de F0014                                    deuxième famille de Paul                         I0001/F0014    
chercher F0014           data.families["F0014"] objet Family                                          passage Person → Family                                         
tester first_family_row  F0014 absent           nouvelle famille                                      jamais développée                                               
mémoriser                F0014 → 0              dictionnaire modifié                                  permettre un futur renvoi                                       
lire le conjoint         I0055                  ligne SPOUSE                                          conserver le couple                                             
lire le premier enfant   I0008                  nouvel appel visit_person()                           poursuite du DFS                                                
                                                                                                                                                                      
Etape 013                                                                                                                                                             
Action                   Valeur                 Résultat                                              Pourquoi                                                        
lire I0008.family_ids    ()                     retour à la lecture de la liste des enfants de F0014  fin de la lignée                                 I0008|         
lire le deuxième enfant  ()                     retour à la lecture de la liste des enfants de F0003  fin de la lignée                                 F0014|         
lire le cinquième enfant ()                     fin des familles de I0001                             fin de la descendance                            F0003|         
     
---

## 6.4 DFS (résultat) :
                                                                                                               
Etape 001                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0001                                                                                                              
generation                                                                 1                                                                                                                  
role                                                                       ROOT                                                                                                               
parent_family_id                                                           ()                                                                                                                 
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,}                                                                                                                                                                                  
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0003                                                                      I0001                0                    I0004            1                EXPLORED                               
                                                                                                                                                                                             
Etape 002                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0010                                                                                                              
generation                                                                 2                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0003                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,}                                                                                                                                                                        
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0317                                                                      I0010                2                    I0044            3                EXPLORED                               
                                                                                                                                                                                             
Etape 003                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0087                                                                                                              
generation                                                                 3                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0317                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,}                                                                                                                                                              
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0333                                                                      I0087                4                    I0194            5                EXPLORED                               
                                                                                                                                                                                             
Etape 004                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0087                                                                                                              
generation                                                                 3                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0317                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,}                                                                                                                                                              
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
                                                                                                                                                                                             
                                                                                                                                                                                             
Etape 005                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0199                                                                                                              
generation                                                                 4                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0333                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,}                                                                                                                                                    
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0400                                                                      I0199                7                                                      EXPLORED                               
                                                                                                                                                                                             
Etape 006                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0199                                                                                                              
generation                                                                 4                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0333                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,}                                                                                                                                                    
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
                                                                                                                                                                                             
                                                                                                                                                                                             
Etape 007                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0199                                                                                                              
generation                                                                 4                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0333                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,}                                                                                                                                                    
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
                                                                                                                                                                                             
                                                                                                                                                                                             
Etape 008                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0011                                                                                                              
generation                                                                 2                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0003                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,}                                                                                                                                         
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0290                                                                      I0011                10                   I0110            11               EXPLORED                               
                                                                                                                                                                                             
Etape 009                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0198                                                                                                              
generation                                                                 3                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0290                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
12                                                                         I0198                DESCENDANT                                                                                    
13                                                                         I0361                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,"F0300":12,}                                                                                                                              
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0300                                                                      I0198                12                   I0361            13               EXPLORED                               
                                                                                                                                                                                             
Etape 010                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0194                                                                                                              
generation                                                                 4                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0300                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
12                                                                         I0198                DESCENDANT                                                                                    
13                                                                         I0361                SPOUSE                                                                                        
14                                                                         I0194                DESCENDANT                                                                                    
15                                                                         I0087                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,"F0300":12,}                                                                                                                              
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0333                                                                      I0194                14                   I0087            15               ALREADY_DESCRIBED 4                    
                                                                                                                                                                                             
Etape 011                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0002                                                                                                              
generation                                                                 2                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0003                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
12                                                                         I0198                DESCENDANT                                                                                    
13                                                                         I0361                SPOUSE                                                                                        
14                                                                         I0194                DESCENDANT                                                                                    
15                                                                         I0087                SPOUSE                                                                                        
16                                                                         I0002                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,"F0300":12,}                                                                                                                              
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
                                                                                                                                                                                             
                                                                                                                                                                                             
Etape 012                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0001                                                                                                              
generation                                                                 1                                                                                                                  
role                                                                       ROOT                                                                                                               
parent_family_id                                                           ()                                                                                                                 
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
12                                                                         I0198                DESCENDANT                                                                                    
13                                                                         I0361                SPOUSE                                                                                        
14                                                                         I0194                DESCENDANT                                                                                    
15                                                                         I0087                SPOUSE                                                                                        
16                                                                         I0002                DESCENDANT                                                                                    
17                                                                         I0055                SPOUSE                                                                                        
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,"F0300":12,"F0014":0,}                                                                                                                    
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 
F0014                                                                      I0001                0                    I0055            17               EXPLORED                               
                                                                                                                                                                                             
Etape 013                                                                                                                                                                                     
Contexte visit_person                                                                                                                                                                         
person_id                                                                  I0008                                                                                                              
generation                                                                 2                                                                                                                  
role                                                                       DESCENDANT                                                                                                         
parent_family_id                                                           F0014                                                                                                              
                                                                                                                                                                                             
rows                                                                                                                                                                                          
index                                                                      person_id            role                                                                                          
0                                                                          I0001                ROOT                                                                                          
1                                                                          I0004                SPOUSE                                                                                        
2                                                                          I0010                DESCENDANT                                                                                    
3                                                                          I0044                SPOUSE                                                                                        
4                                                                          I0087                DESCENDANT                                                                                    
5                                                                          I0194                SPOUSE                                                                                        
6                                                                          I0196                DESCENDANT                                                                                    
7                                                                          I0199                DESCENDANT                                                                                    
8                                                                          I0022                DESCENDANT                                                                                    
9                                                                          I0023                DESCENDANT                                                                                    
10                                                                         I0011                DESCENDANT                                                                                    
11                                                                         I0110                SPOUSE                                                                                        
12                                                                         I0198                DESCENDANT                                                                                    
13                                                                         I0361                SPOUSE                                                                                        
14                                                                         I0194                DESCENDANT                                                                                    
15                                                                         I0087                SPOUSE                                                                                        
16                                                                         I0002                DESCENDANT                                                                                    
17                                                                         I0055                SPOUSE                                                                                        
18                                                                         I0008                DESCENDANT                                                                                    
                                                                                                                                                                                             
first_family_row                                                                                                                                                                              
{"F0003":0,"F0317":2,"F0333":4,"F0400":7,"F0290":10,"F0300":12,"F0014":0,}                                                                                                                    
                                                                                                                                                                                             
family_occurrence                                                                                                                                                                             
family_id                                                                  descendant_person_id descendant_row_index spouse_person_id spouse_row_index state             referenced_row_index 

---







 
