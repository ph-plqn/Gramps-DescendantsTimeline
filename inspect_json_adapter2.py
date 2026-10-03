from descendants_timeline.gramps.json_adapter import JsonGrampsAdapter

data = JsonGrampsAdapter().load(
    "4665.json",
    root_person_id="I0001",  # mettre un identifiant présent dans ton fichier
)

person_id="I1575"
person=(data.persons[person_id])
print("Evénements propres à",person.display_name,":")
for event in person.event_refs:
        dataevent=(data.events[event.event_id])
        print("   ",event.event_id,dataevent.semantic,event.semantic_role)
print("Familles de",person.display_name,":")
for family in person.family_ids:
        print("   ",family)
        family=(data.families[family])
        print("    Evénements propres à cette famille :")
        for eventfam in family.event_refs:
            dataevent=(data.events[eventfam.event_id])
            print("      ",eventfam.event_id,dataevent.semantic)
