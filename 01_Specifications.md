# Gramps Descendants Timeline

## Spécifications fonctionnelles

**Version :** 1.0  
**Statut :** Validée – Référence du projet

**Projet :** Gramps Descendants Timeline

**Auteur du projet :** Philippe

**Conception fonctionnelle :**
- idée originale ;
- cahier de conception ;
- définition des règles métier ;
- validation fonctionnelle.

**Architecture logicielle et développement :**

Projet développé avec l'assistance de ChatGPT (OpenAI), qui contribue à :

- l'architecture logicielle ;
- la conception des algorithmes ;
- la documentation technique ;
- la génération du code Python ;
- les tests ;
- la documentation utilisateur.

---

# Table des matières

1. Présentation
2. Objectifs
3. Principes de conception
4. Définitions
5. Règles métier (R)
6. Règles de placement (L)
7. Règles graphiques (G)
8. Règles des événements (E)
9. Règles de performance (P)
10. Cas particuliers (C)
11. Fonctionnalités futures
12. Historique du document

---

# 1. Présentation

## 1.1 Objet du projet

Gramps Descendants Timeline est un greffon destiné à Gramps 6.x.

Il propose une représentation graphique chronologique de la descendance d'un individu à partir d'une véritable échelle du temps.

Contrairement aux arbres généalogiques classiques, qui privilégient les liens de parenté, cette vue met en évidence la dimension temporelle des événements familiaux.

Le greffon représente simultanément :

- les durées de vie ;
- les générations ;
- les unions ;
- les remariages ;
- les filiations ;
- les périodes de coexistence entre individus.

L'objectif est d'offrir une lecture chronologique intuitive de familles comportant un grand nombre de générations.

---

## 1.2 Public visé

Le greffon est destiné :

- aux utilisateurs de Gramps ;
- aux généalogistes amateurs ;
- aux associations de généalogie ;
- aux développeurs souhaitant faire évoluer le projet.

---

## 1.3 Compatibilité

Le projet est développé pour :

- Gramps 6.0.x
- Python 3
- GTK 3

Les versions futures pourront être adaptées aux évolutions de Gramps.

---

# 2. Objectifs

Le projet poursuit plusieurs objectifs.

## O001 — Représentation chronologique

Afficher la descendance sur une véritable échelle du temps.

---

## O002 — Lisibilité

Permettre une lecture rapide des générations et des liens familiaux.

---

## O003 — Fidélité généalogique

Respecter les données présentes dans la base Gramps sans les modifier.

---

## O004 — Gestion des situations complexes

Prendre en charge notamment :

- les remariages ;
- les unions multiples ;
- les dates incomplètes ;
- les événements absents ;
- les familles nombreuses.

---

## O005 — Modularité

Séparer :

- le calcul du modèle ;
- le placement des objets ;
- le rendu graphique ;
- les exports.

Cette séparation facilite les évolutions futures.

---

# 3. Principes de conception

Les principes suivants guident tout le développement.

## PDC001 — La spécification prévaut

En cas de divergence entre le code et le présent document, la spécification fait référence.

---

## PDC002 — Numérotation permanente

Les identifiants des règles sont définitifs.

Une règle supprimée reste réservée et n'est jamais réutilisée.

---

## PDC003 — Séparation des responsabilités

Le logiciel est organisé en modules indépendants.

Le moteur de calcul ne dépend pas du rendu graphique.

Le rendu graphique ne dépend pas du support d'affichage.

---

## PDC004 — Indépendance des exports

Les exports PDF, SVG et PNG utilisent les mêmes données de placement.

Ils ne recalculent jamais le layout.

---

## PDC005 — Évolutivité

Toute nouvelle fonctionnalité doit pouvoir être ajoutée sans remettre en cause l'architecture générale.

---

## PDC006 — Traçabilité

Chaque fonctionnalité implémentée doit pouvoir être reliée à une règle des présentes spécifications.

---

## PDC007 — Respect de l'ordre des données

Le greffon respecte l'ordre des objets tel qu'il est défini dans la base Gramps.

Aucun réordonnancement automatique n'est effectué, sauf si une option explicite de l'utilisateur le demande.

---

## PDC008 — Explications des résultats

Privilégier l'explicabilité des résultats plutôt que la complexité des algorithmes.

Le raisonnement du moteur d'inférence temporelle doit être facilement compréhensible par l'utilisateur.

---

# 4. Définitions

Les termes suivants sont utilisés dans l'ensemble du projet.

## D001 — Personne

Objet `Person` de Gramps représentant un individu.

---

## D002 — Descendant

Toute personne appartenant à la descendance de la personne racine.

---

## D003 — Conjoint

Personne liée à un descendant par une famille (`Family`) mais ne faisant pas elle-même partie de la descendance représentée.

Les conjoints sont affichés avec un style graphique spécifique.

---

## D004 — Famille

Objet `Family` de Gramps reliant deux conjoints et leurs enfants.

Une personne peut appartenir à plusieurs familles.

---

## D005 — Mariage

Événement de type `Marriage` associé à une famille.

Le mariage est représenté par un nœud de mariage placé sur la timeline à sa date.

---

## D006 — Remariage

Situation dans laquelle une personne appartient successivement à plusieurs familles.

Les cercles représentant les mariages successifs d'une même personne sont reliés par un segment vertical placé à la date de chaque remariage avec le nouveau conjoint.

---

## D007 — Génération

Ensemble des descendants situés à une même distance généalogique de la personne racine.

Chaque génération possède une couleur spécifique.

---

## D008 — Timeline

Axe horizontal représentant le temps.

Toutes les dates sont positionnées sur cet axe.

---

## D009 — Layout

Résultat du calcul de position de tous les objets graphiques avant leur dessin.

---

## D010 — Renderer

Composant chargé de dessiner la représentation graphique à partir du layout calculé.

Le renderer ne modifie jamais les positions calculées.

---

## D011 — Personne racine

Individu choisi par l'utilisateur comme origine de la représentation.

Toutes les générations sont calculées à partir de cette personne.

---

## D012 — Barre de vie

Segment horizontal représentant la durée de vie d'une personne.

La barre s'étend de la naissance jusqu'au décès ou jusqu'à la date actuelle lorsque la personne est vivante.

---

## D013 — Nœud de mariage

Élément graphique représenté par un cercle positionné sur la timeline à la date d'un mariage.

Il relie les deux conjoints et constitue le point d'ancrage des enfants issus de cette union.

---

*La suite de ce document décrit les règles fonctionnelles qui devront être respectées par toute implémentation du projet.*

# 5. Règles métier (R)

Les règles métier définissent les informations généalogiques représentées par le greffon.

Elles sont indépendantes de toute considération graphique.

---

## R001 — Personne racine

La représentation est construite à partir d'une personne racine choisie par l'utilisateur.

Seuls les descendants de cette personne sont représentés.

Les ascendants ne sont pas affichés.

---

## R002 — Descendance

Tous les descendants de la personne racine sont représentés.

La profondeur de la descendance peut être limitée par les préférences utilisateur.

---

## R003 — Conjoints

Les conjoints des descendants sont représentés.

Ils permettent de comprendre la structure familiale mais ne sont jamais considérés comme appartenant à la descendance.

---

## R004 — Familles

Chaque famille Gramps est représentée par un nœud de mariage.

Les enfants sont rattachés exclusivement à la famille dont ils sont issus.

---

## R005 — Mariages

Chaque mariage est représenté par un nœud positionné à la date du mariage.

Le mariage relie graphiquement les deux conjoints.

---

## R006 — Remariages

Une personne peut appartenir successivement à plusieurs familles.

Chaque mariage possède son propre nœud.

Les nœuds des mariages successifs sont reliés conformément à D006.

---

## R007 — Chronologie

Toutes les personnes et tous les événements sont positionnés selon leurs dates.

La timeline constitue la seule référence temporelle.

---

## R008 — Générations

Chaque descendant appartient à une génération calculée à partir de la personne racine.

Les conjoints ne modifient jamais la numérotation des générations.

---

## R009 — Intégrité des données

Le greffon ne modifie jamais la base Gramps.

Toutes les données utilisées sont uniquement lues.

---

# 6. Règles de placement (L)

Les règles de placement définissent la position des objets graphiques.

---

## L001 — Axe temporel

L'axe horizontal représente le temps.

Les années croissent de gauche à droite.

---

## L002 — Barre de vie

La barre de vie est positionnée entre la naissance et le décès.

Pour une personne vivante, la barre se termine à la date actuelle.

---

## L003 — Position du nœud de mariage

Le nœud de mariage est placé exactement à la date du mariage.

Il est toujours situé entre les deux conjoints.

---

## L004 — Conjoints

Les deux conjoints sont reliés au même nœud de mariage.

Le descendant conserve la couleur de sa génération.

Le conjoint est représenté en gris.

---

## L005 — Enfants

Les enfants sont rattachés au nœud de mariage de leurs parents.

Ils sont situés sous le nœud de mariage de la famille à laquelle ils sont rattachés.

---

## L006 — Générations

Les descendants sont placés selon un parcours en profondeur de l'arbre de descendance.
Chaque branche est représentée jusqu'à son dernier descendant avant de revenir au frère ou à la sœur suivante.

---

## L007 — Ordre des enfants

Les enfants d'une même famille sont représentés dans l'ordre défini par la famille correspondante dans Gramps.
Le greffon ne modifie jamais cet ordre.

---

## L008 — Remariages

Les nœuds représentant les mariages successifs d'une même personne sont reliés par un segment vertical.

Ce segment est placé à la date du remariage.

---

## L009 — Ordre chronologique

Les mariages successifs d'une personne apparaissent dans l'ordre chronologique.

---

## L010 — Stabilité

À données identiques, le placement doit produire exactement le même résultat.

---

## L011 — Déterminisme

Le calcul du layout est entièrement déterministe.

Deux exécutions successives produisent un affichage identique.

---

# 7. Règles graphiques (G)

Les règles graphiques définissent la représentation visuelle des objets de la timeline.

Elles garantissent une représentation homogène, indépendante du support de sortie (écran, PDF, SVG, PNG).

---

## G001 — Barre de vie

Chaque personne est représentée par une barre de vie horizontale.

La barre débute à la date de naissance et se termine à la date du décès.

Pour une personne vivante, elle se termine à la date courante.

---

## G002 — Couleur des générations

Chaque génération de descendants possède une couleur spécifique.

Tous les descendants d'une même génération utilisent cette couleur.

Les couleurs sont définies par le thème graphique.

---

## G003 — Couleur des conjoints

Les conjoints n'appartenant pas à la descendance sont représentés en gris.

Cette représentation permet de distinguer immédiatement les descendants des conjoints.

---

## G004 — Nœud de mariage

Chaque mariage est représenté par un nœud de mariage.

Le nœud est dessiné sous la forme d'un cercle.

Il est positionné :

- horizontalement à la date du mariage sur la timeline ;
- verticalement entre le bord inférieur de la barre de vie du descendant et le bord supérieur de la barre de vie de son conjoint.

---

## G005 — Liaison des conjoints

Les deux conjoints sont reliés au nœud de mariage.

Cette liaison matérialise graphiquement l'union.

---

## G006 — Position des enfants

Les enfants sont représentés sous le nœud de mariage de la famille à laquelle ils appartiennent.

Aucun segment graphique ne relie les enfants à leurs parents.

La filiation est déduite de leur position sous le nœud de mariage et du changement de couleur entre les générations.

---

## G007 — Représentation des remariages

Les nœuds correspondant aux mariages successifs d'une même personne sont reliés par un segment vertical.

Ce segment est positionné à la date du remariage avec le nouveau conjoint.

---

## G008 — Cohérence temporelle

Tous les éléments graphiques sont positionnés selon la même échelle temporelle.

Deux événements ayant la même date sont alignés verticalement.

---

## G009 — Lisibilité

Le rendu graphique doit privilégier la lisibilité.

Les éléments ne doivent pas se masquer mutuellement.

Les recouvrements sont évités autant que possible.

---

## G010 — Homogénéité

Les conventions graphiques sont identiques sur tous les supports d'export.

Une même base Gramps produit une représentation identique, quel que soit le format de sortie.

---

## G011 — Expression graphique des relations

Les relations familiales sont exprimées par la combinaison :

- de la position des personnes ;
- des nœuds de mariage ;
- des couleurs des générations.

Le greffon n'utilise pas de segments reliant directement les parents à leurs enfants.

---

# 8. Règles des événements (E)

Les événements constituent les références temporelles utilisées par le moteur.

---

## E001 — Naissance

La naissance détermine le début de la barre de vie.

---

## E002 — Décès

Le décès détermine la fin de la barre de vie.

Pour une personne vivante, la barre se termine à la date courante.

---

## E003 — Mariage

Le mariage détermine la position du nœud de mariage.

Lorsqu'une date de mariage est inconnue, le moteur peut utiliser les autres informations disponibles pour proposer une estimation.

---

## E004 — Chronologie

Les événements sont toujours représentés dans leur ordre chronologique.

Le moteur ne produit jamais une chronologie incohérente.

---

## E005 — Estimation à partir de l'ordre des enfants

Lorsque la date de naissance d'un enfant est inconnue, le moteur peut utiliser l'ordre des enfants défini dans la famille Gramps pour en déduire un intervalle de naissance compatible avec les dates connues des frères et sœurs.

Toute estimation doit conserver les contraintes ayant conduit à cette déduction.

---

## E006 — Traçabilité des estimations

Toute date estimée doit pouvoir être expliquée.

Le moteur d'inférence conserve les règles, contraintes et événements ayant permis d'établir cette estimation.

Ces informations peuvent être utilisées pour l'affichage, le débogage ou l'évolution du logiciel.

---

## E007 — Respect des données Gramps

Les événements présents dans la base Gramps ne sont jamais modifiés.

Les dates estimées sont calculées uniquement en mémoire et restent distinctes des données originales.

---

# 9. Règles de performance (P)

Les règles de performance définissent les qualités attendues du logiciel.

---

## P001 — Déterminisme

À données identiques, le greffon produit toujours le même résultat graphique.

---

## P002 — Temps de calcul

Le temps de génération doit rester compatible avec une utilisation interactive.

---

## P003 — Passage unique

Le parcours de la descendance privilégie un parcours unique de l'arbre généalogique.

Les recalculs inutiles sont évités.

---

## P004 — Modularité

Les calculs sont séparés en plusieurs étapes indépendantes :

- construction du modèle généalogique ;
- inférence temporelle ;
- calcul du layout ;
- rendu graphique.

Cette séparation facilite les tests et les évolutions futures.

---

## P005 — Évolutivité

L'architecture doit permettre l'ajout de nouvelles règles d'inférence ou de nouvelles représentations graphiques sans remettre en cause les composants existants.

---

## P006 — Vérifiabilité

Les résultats produits par le moteur doivent pouvoir être vérifiés.

Les estimations temporelles doivent être accompagnées de leurs justifications.

Cette propriété facilite les tests, le débogage et la validation généalogique.

---

# 10. Cas particuliers et robustesse (C)

Les règles suivantes définissent le comportement du greffon lorsque les données généalogiques sont incomplètes, ambiguës ou incohérentes.

Le moteur doit toujours produire une représentation exploitable sans modifier les données Gramps.

---

## C001 — Date de naissance inconnue

Lorsqu'une date de naissance est inconnue, le moteur d'inférence tente d'estimer un intervalle de naissance à partir des contraintes temporelles disponibles.

Si aucune estimation n'est possible, la personne reste représentée avec une date inconnue.

---

## C002 — Date de décès inconnue

Lorsqu'une date de décès est inconnue, la personne est considérée comme vivante uniquement si Gramps l'indique explicitement.

Dans le cas contraire, la barre de vie peut être interrompue ou prolongée selon les préférences utilisateur.

---

## C003 — Date de mariage inconnue

Lorsqu'une date de mariage est absente, le moteur peut proposer une estimation.

Le nœud de mariage est alors représenté à la date estimée.

Cette estimation reste distincte des données Gramps.

---

## C004 — Personne sans conjoint

Une personne sans conjoint est représentée normalement.

L'absence de mariage n'empêche jamais l'affichage de ses descendants.

---

## C005 — Famille sans enfant

Une famille sans enfant est représentée par ses conjoints et son nœud de mariage.

Aucun espace supplémentaire n'est réservé à une descendance inexistante.

---

## C006 — Enfant unique

Un enfant unique est représenté selon les mêmes règles qu'une fratrie.

Aucun traitement particulier n'est appliqué.

---

## C007 — Remariages multiples

Le nombre de remariages n'est pas limité.

Chaque mariage possède son propre nœud.

Les nœuds successifs sont reliés conformément à G007.

---

## C008 — Dates incohérentes

Lorsqu'une incohérence chronologique est détectée, le moteur conserve les données Gramps.

L'incohérence peut être signalée graphiquement ou dans un rapport.

---

## C009 — Contraintes contradictoires

Lorsque les contraintes temporelles sont incompatibles, aucune estimation n'est produite.

Le moteur conserve les contraintes ayant conduit à cette contradiction.

---

## C010 — Personne sans événement connu

Une personne dépourvue de toute information temporelle reste représentée si elle appartient à la descendance.

Sa position temporelle est déterminée uniquement par les contraintes disponibles.

---

## C011 — Personne racine sans descendant

Si la personne racine ne possède aucun descendant, seule cette personne est représentée.

Le greffon produit néanmoins une timeline valide.

---

## C012 — Dégradation gracieuse

L'absence d'une information ne doit jamais empêcher la génération de la représentation.

Le greffon produit toujours le meilleur résultat possible compte tenu des données disponibles.

---

## C013 — Parent inconnu

Une famille peut comporter un seul parent connu.

Le greffon représente cette famille sans créer de personne fictive.

Le nœud de mariage est représenté uniquement lorsque la famille Gramps comporte deux individus.

---

## C014 — Famille sans relation datée

Lorsqu'une famille Gramps ne comporte qu'un seul individu, le moteur ne cherche pas à estimer une date de relation.

Aucun nœud de mariage n'est représenté.

---
