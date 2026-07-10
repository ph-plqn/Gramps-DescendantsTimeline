# Gramps Descendants Timeline

# Philosophie

Les principes qui ont guidé la conception de ce projet sont :

- respecter les données de Gramps ;
- privilégier une représentation déterministe ;
- transformer des données en perception visuelle ;
- conserver la justification des inférences ;
- séparer les concepts de leurs implémentations.

Ces principes conduisent aux règles suivantes :

- le greffon ne modifie jamais les données de la base Gramps ;
- le greffon n'invente jamais d'informations généalogiques ;
- le greffon représente fidèlement les données présentes dans la base ;
- les estimations, contraintes et diagnostics sont calculés uniquement en mémoire et ne sont jamais enregistrés dans la base Gramps ;
- toute estimation est justifiée par les contraintes qui ont conduit à son calcul ;
- chaque estimation est accompagnée d'un niveau de certitude.
