from descendants_timeline.gramps.json_adapter import JsonGrampsAdapter
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceTraversal,
    TraversalOptions,
    DescendanceMode,
)

root_person_id = "I0000"

data = JsonGrampsAdapter().load(
    "MatriceJSON.json",
    root_person_id=root_person_id,
)

options = TraversalOptions(
    mode=DescendanceMode.EXTENDED
)

result = DescendanceTraversal().traverse(
    data,
    root_person_id,
    options,
)

# caractéristiques du résultat du DFS
print("Nombre de lignes :", len(result.rows))
print("Nombre d'occurrences de familles :", len(result.family_occurrences))

# affichage du DFS
for index, row in enumerate(result.rows):
    person = data.persons[row.person_id]

    print(
        index,
        row.generation,
        row.role,
        row.person_id,
        person.display_name,
    )