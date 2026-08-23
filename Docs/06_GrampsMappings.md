# Gramps Descendants Timeline

## GrampsMappings
**Version :** 0.2  
**Statut :** Brouillon  
**Document :** `06_GrampsMappings.md`

---

# Table des matières

1. Objet du document
2. Principes de traduction
3. Codes utilisés par GRAMPS
4. Points à examiner

---

# 1. Objet du document

Le présent document liste les codes utilisés par GRAMPS pour les attributs des objets utiles au greffon et précise leur traduction vers le modèle interne de **Gramps Descendants Timeline**.

Le `GrampsDataAdapter` est responsable de cette traduction. Les codes numériques propres à GRAMPS ne doivent pas se propager dans le modèle métier du greffon.

---

# 2. Principes de traduction

- Les codes GRAMPS sont des données de source.
- Le `GrampsDataAdapter` les traduit vers les énumérations du modèle lorsque le concept est utilisé par le greffon.
- Une valeur GRAMPS non utilisée par le greffon ne doit pas être interprétée artificiellement.
- Les valeurs `CUSTOM` doivent être distinguées des valeurs `UNKNOWN` : une valeur personnalisée n'est pas une valeur inconnue.
- Lorsqu'un libellé personnalisé GRAMPS est utile, il devra être conservé séparément du sens normalisé.
- Les valeurs listées ci-dessous devront être couvertes par des tests du `GrampsDataAdapter` lorsqu'elles sont utilisées par le greffon.

---

# 3. Codes utilisés par GRAMPS

## 3.1 Gramps EventType

| Code | Sens GRAMPS | EventSemantic | Utilisé par le greffon |
|---:|---|---|:---:|
| -1 | Inconnu | `EventSemantic.UNKNOWN` | à confirmer |
| 0 | Personnalisé | à définir | à examiner |
| 1 | Mariage | `EventSemantic.MARRIAGE` | oui |
| 7 | Divorce | `EventSemantic.DIVORCE` | oui |
| 12 | Naissance | `EventSemantic.BIRTH` | oui |
| 13 | Décès | `EventSemantic.DEATH` | oui |
| 15 | Baptême | `EventSemantic.BAPTISM` | oui |
| 19 | Inhumation | `EventSemantic.BURIAL` | oui |

GRAMPS définit de nombreux autres types d'événements standards. Ils ne sont pas tous nécessaires au modèle actuel. Certains pourront toutefois devenir utiles au moteur d'inférence temporelle.

---

## 3.2 Gramps EventRoleType

| Code | Sens GRAMPS | EventRoleSemantic | Utilisé par le greffon |
|---:|---|---|:---:|
| -1 | Inconnu | `EventRoleSemantic.UNKNOWN` | à confirmer |
| 0 | Personnalisé | à définir | à examiner |
| 1 | Principal | `EventRoleSemantic.PRINCIPAL` | oui |
| 7 | Témoin | `EventRoleSemantic.WITNESS` | oui |
| 8 | Famille | `FamilyRoleSemantic.FAMILY` | oui |
| 9 | Déclarant | `EventRoleSemantic.INFORMANT` | oui |

**Important :** `FAMILY` est un rôle d'événement GRAMPS (`EventRoleType.FAMILY`) de code **8**. Il ne correspond pas au code 0.

GRAMPS possède d'autres rôles standards (clergé, célébrant, époux, épouse, etc.). Les rôles non retenus par notre modèle seront traduits selon la politique définie pour `EventRoleSemantic.UNKNOWN`, sans confondre une valeur standard non retenue avec une valeur GRAMPS explicitement inconnue.

---

## 3.3 Gramps ChildRef relation

| Code | Sens GRAMPS | ChildRelation | Inclusion DFS par défaut |
|---:|---|---|:---:|
| 0 | Aucun | `ChildRelation.NONE` | non |
| 1 | Naissance | `ChildRelation.BIRTH` | oui |
| 2 | Adopté | `ChildRelation.ADOPTED` | mode étendu |
| 3 | Enfant du conjoint | `ChildRelation.STEPCHILD` | non |
| 4 | Parrainé | `ChildRelation.SPONSORED` | mode étendu |
| 5 | En nourrice | `ChildRelation.FOSTER` | non |
| 6 | Inconnu | `ChildRelation.UNKNOWN` | non |
| 7 | Personnalisé | à définir (`CUSTOM`) | à examiner |

`UNKNOWN` a ici une signification métier particulière : GRAMPS indique explicitement que la relation enfant-parent est inconnue. Cette valeur ne doit donc pas être utilisée comme simple valeur de repli pour `CUSTOM` ou pour une valeur non prise en charge.

---

## 3.4 Gramps Date calendar

| Code | Sens GRAMPS |
|---:|---|
| 0 | Grégorien |
| 1 | Julien |
| 2 | Hébreu |
| 3 | Républicain français |
| 4 | Persan |
| 5 | Islamique |
| 6 | Suédois |

Le calendrier source doit être conservé pour l'explication et la justification des données temporelles. La représentation graphique de la timeline reste convertie en calendrier grégorien conformément aux spécifications du projet.

---

## 3.5 Gramps Date modifier

| Code | Constante GRAMPS | Sens |
|---:|---|---|
| 0 | `MOD_NONE` / normal | Date normale |
| 1 | `MOD_BEFORE` | Avant |
| 2 | `MOD_AFTER` | Après |
| 3 | `MOD_ABOUT` | Vers / date approximative |
| 4 | `MOD_RANGE` | Entre date1 et date2 |
| 5 | `MOD_SPAN` | De date1 à date2 |
| 6 | `MOD_TEXTONLY` | Texte uniquement |
| 7 | `MOD_FROM` | À partir de |
| 8 | `MOD_TO` | Jusqu'à |

Ces modificateurs devront être traduits vers la représentation temporelle du greffon sans perdre la nature de la borne ou de l'intervalle GRAMPS.

---

## 3.6 Gramps Date quality

| Code | Sens GRAMPS | Traitement prévu |
|---:|---|---|
| 0 | Normal | donnée GRAMPS exploitable selon sa date |
| 1 | Estimé(e) | qualité source à conserver |
| 2 | Calculé(e) | donnée `UNPROVEN` tant qu'aucune justification exploitable n'est disponible |

La qualité GRAMPS ne doit pas être confondue avec l'indice de certitude produit par le moteur d'inférence du greffon.

---

## 3.7 Gramps Gender

| Code | Sens GRAMPS | PersonGender |
|---:|---|---|
| 0 | Féminin | `PersonGender.FEMALE` |
| 1 | Masculin | `PersonGender.MALE` |
| 2 | Inconnu | `PersonGender.UNKNOWN` |
| 3 | Autre | `PersonGender.OTHER` |

Les quatre valeurs GRAMPS sont conservées par le modèle.

---

## 3.8 Gramps FamilyRole

Il n'existe pas ici de type GRAMPS distinct à traduire sous le nom `FamilyRole`. Le concept utilisé par notre modèle correspond au rôle d'événement :

| Code | Type GRAMPS | Sens | Modèle |
|---:|---|---|---|
| 8 | `EventRoleType.FAMILY` | Famille | `FamilyRoleSemantic.FAMILY` |

Cette information est donc issue de `EventRoleType` et non d'une table de codes indépendante.

---

## 3.9 Gramps FamilyRelType

| Code | Sens GRAMPS | Utilisé par le modèle actuel |
|---:|---|:---:|
| -1 | Inconnu | non |
| 0 | Personnalisé | non |
| 1 | Mariés | non |
| 2 | Non mariés | non |
| 3 | Union civile | non |
| 4 | Inconnu / autre valeur à vérifier selon la version GRAMPS | non |

**À vérifier avant implémentation :** cette table doit être confirmée directement sur la version GRAMPS ciblée (6.0.8). `FamilyRelType` n'est actuellement pas conservé dans notre classe `Family` et n'est pas nécessaire au DFS.

---

# 4. Points à examiner

## 4.1 Valeurs CUSTOM

Les types GRAMPS héritant de `GrampsType` peuvent contenir une valeur personnalisée. Le greffon doit distinguer :

- une valeur GRAMPS explicitement `UNKNOWN` ;
- une valeur standard GRAMPS que notre modèle ne traite pas ;
- une valeur `CUSTOM` définie par l'utilisateur.

Cette distinction est particulièrement importante pour `ChildRelation`, car `ChildRelation.UNKNOWN` possède déjà une signification métier propre.

Avant d'écrire le `GrampsDataAdapter`, il faudra décider si le modèle doit ajouter explicitement une valeur `CUSTOM` et/ou conserver le libellé source personnalisé.

## 4.2 Événements utilisables par l'inférence

GRAMPS définit des événements de repli autour des événements principaux. Le code GRAMPS considère notamment :

- comme repli de naissance : mort-né, baptême, christening ;
- comme repli de décès : mort-né, inhumation, crémation, cause du décès, probate ;
- comme repli de mariage : fiançailles, mariage alternatif ;
- comme repli de divorce : annulation, dépôt de divorce.

Le greffon ne doit pas nécessairement reproduire automatiquement cette politique. Ces événements constituent toutefois des candidats importants pour les futures règles du moteur d'inférence temporelle.

## 4.3 Version GRAMPS de référence

Les matrices doivent être validées contre la version GRAMPS ciblée par le projet, actuellement **GRAMPS 6.0.8**. Les codes réellement utilisés par le `GrampsDataAdapter` devront être protégés par des tests afin qu'une évolution future de GRAMPS soit détectée explicitement.

---
