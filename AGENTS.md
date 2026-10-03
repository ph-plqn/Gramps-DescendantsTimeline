# Instructions de développement

## Méthode de travail

Ce projet est développé de manière incrémentale et pilotée par les tests.

Pour toute nouvelle fonctionnalité ou nouveau comportement :

1. Traiter un seul comportement à la fois.
2. Écrire d'abord un seul test correspondant à ce comportement.
3. Exécuter ce test avant de modifier l'implémentation.
4. Vérifier que le test échoue pour la raison attendue.
5. Ne modifier ensuite que le minimum de code nécessaire pour faire passer ce test.
6. Réexécuter le test concerné.
7. Ne passer au comportement suivant qu'après validation explicite de l'utilisateur.
8. Ne pas ajouter spontanément plusieurs tests ou plusieurs comportements en une seule étape.

## Architecture

- Respecter l'architecture existante et les responsabilités des modules.
- Ne pas effectuer de refactoring non demandé.
- Ne pas déplacer, renommer ou réorganiser des fichiers sans demande explicite.
- Ne pas introduire de nouvelle abstraction tant qu'un besoin concret ne la justifie pas.
- Ne pas dupliquer des informations déjà disponibles dans le modèle.
- Le LayoutEngine calcule des coordonnées logiques ; il ne dessine rien.
- Le zoom et le pan ne doivent pas modifier les coordonnées logiques du layout.
- Les décisions temporelles doivent provenir du moteur d'inférence et non être réinventées par le LayoutEngine.

## Données Gramps

- Le greffon ne doit jamais modifier les données Gramps.
- L'ordre des enfants est l'ordre fourni par Gramps.
- L'ordre des familles d'une personne est l'ordre fourni par Gramps.
- Ne pas inventer de personne fictive pour une famille monoparentale.
- Ne pas inventer de date de relation ou de mariage absente des données ou de l'inférence.

## Tests

La suite complète peut être exécutée sous PowerShell avec :

$env:PYTHONPATH = (Join-Path (Get-Location).Path 'Src'); python -B -m unittest discover -s Tests -p 'test_*.py'

Au moment de la création de ce fichier, la référence du projet est :
704 tests, OK.
