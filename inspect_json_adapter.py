from descendants_timeline.gramps.json_adapter import JsonGrampsAdapter

data = JsonGrampsAdapter().load(
    "4665.json",
    root_person_id="I0001",  # mettre un identifiant présent dans ton fichier
)

for person_id, person in data.persons.items():
    print(
        person_id,
        "|",
        person.display_name,
        "|",
        person.gender,
        "| parents:",
        person.parent_family_ids,
        "| familles:",
        person.family_ids,
    )