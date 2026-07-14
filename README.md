# Gramps Descendants Timeline

Gramps Descendants Timeline est un greffon destiné à Gramps 6.x.

Ce projet est développé pour les généalogistes. Il est élaboré comme un vrai projet d'ingénierie logicielle à l'aide de ChatGPT (OpenAI).

C'est un outil qui transforme des données généalogiques en connaissance visuelle.

Principe fondateur
Le greffon s'appuie sur les capacités complémentaires de l'ordinateur et de l'utilisateur. L'ordinateur calcule, vérifie et déduit les informations chronologiques. La représentation graphique permet ensuite au généalogiste de percevoir immédiatement les durées de vie, les successions de générations, les écarts temporels et les incohérences éventuelles.

Contrairement aux arbres généalogiques classiques, il représente la descendance sur une véritable échelle du temps.
Chaque branche de descendance n'est représentée qu'une seule fois, même en présence de mariages entre cousins.

Le greffon repose sur trois principes fondamentaux :

- un moteur d'inférence temporelle déduit, justifie et explique les dates estimées ;
- les descendants sont représentés selon un parcours en profondeur (Depth-First Search, DFS) ;
- aucune donnée de la base Gramps n'est jamais modifiée.

Cette représentation met immédiatement en évidence :

- les durées de vie ;
- les générations ;
- les mariages ;
- les remariages.

L'architecture du projet repose sur trois moteurs complémentaires :

- Le moteur d'inférence temporelle : il exploite les données normalisées extraites de Gramps, évalue les preuves, déduit des contraintes temporelles, détermine les intervalles possibles des événements inconnus et calcule, lorsque cela est justifié, une valeur représentative. Il fournit les justifications associées et attribue un niveau de certitude pour chaque calcul. 
Il répond au besoin des généalogistes d'avoir une estimation justifiée de la date d'un évènement en l'absence de preuve directe.
	
- Le moteur de parcours de la descendance : il construit la structure de la descendance selon le DFS, en évitant les redondances en cas de descendants apparentés.
Il répond au besoin des généalogistes d'extraire d'une base de données importantes le sous-ensemble des données nécessaires à la présentation des descendants d'une personne racine.

- Le moteur de représentation graphique : il transforme ces informations en une timeline lisible.
Il répond au besoin des généalogistes de transformer les données d'une base Gramps en connaissance visuelle.

Schéma conceptuel :

	Base Gramps
      		│
      		▼
	GrampsDataAdapter
      		│
      		▼
	RawGenealogyData
      		│
      		▼
	TemporalInferenceEngine
      		│
      		▼
	TimelineModel
      		│
      		▼
	LayoutEngine (DFS)
      		│
      		▼
	Renderer
      		│
      		▼
	Vue interactive / PDF / SVG

État du projet

Version : 0.1
Statut : En développement

Remerciements

Idée originale, cahier de conception et validation fonctionnelle : Philippe
Architecture logicielle, formalisation des concepts, documentation technique et assistance au développement réalisées avec ChatGPT (OpenAI).