from lxml import etree
import copy
OVAL_file = 'rhel-8.oval.xml'
file_input = open(OVAL_file, 'rb')

namespace = {'oval': 'http://oval.mitre.org/XMLSchema/oval-definitions-5'}

def find_comment(elem, value, refs: list, refs_neighbors: list):
    for child in elem.iterchildren():
        if 'comment' in child.attrib and value in child.attrib['comment']:
            ref = child.attrib['test_ref']
            ref_neighbor = child.getparent().getchildren()[0].attrib['test_ref']
            elem.remove(child)
            refs.append(ref)
            refs_neighbors.append(ref_neighbor)
        else:
            find_comment(child, value, refs, refs_neighbors)


tree = etree.parse(file_input)
root = tree.getroot()

definitions = root.xpath("//oval:definitions/oval:definition[position() <= 3]", namespaces=namespace)
generator = root.xpath("//oval:generator", namespaces=namespace)
all_tests = root.xpath("//oval:tests/*", namespaces=namespace)
all_states = root.xpath("//oval:states/*", namespaces=namespace)
all_objects = root.xpath("//oval:objects/*", namespaces=namespace)
variables = root.xpath("//oval:variables", namespaces=namespace)

new_root = etree.Element("oval_definitions")

new_generator = etree.SubElement(new_root, "generator")
new_definitions = etree.SubElement(new_root, "definitions")
new_tests = etree.SubElement(new_root, "tests")
new_objects = etree.SubElement(new_root, "objects")
new_states = etree.SubElement(new_root, "states")
new_variables = etree.SubElement(new_root, "variables")

#добавление генератора к новому дереву
new_generator.extend(generator)

refs = []
refs_neighbors = []
#удаление критериев на подпись, сбор ссылок на их тесты и соседних критериев; добавление описаний
for definition in definitions:
    find_comment(definition, 'is signed with Red Hat redhatrelease2 key', refs, refs_neighbors)
    new_definitions.append(definition)

tests_refs = []
#добавление нужных тестов; получение ссылок на состояния после проверок на версию ("соседних")
for test in all_tests:
    if test.attrib['id'] in refs:
        continue
    elif test.attrib['id'] in refs_neighbors:
        tests_refs.append(test.getchildren()[1].attrib['state_ref'])
    new_tests.append(test)

key_state = all_states[1].getchildren()[0]
new_objects.extend(all_objects)

#добавление нужных состояний; в каждое состояние версии добавить параметр наличия подписи
for state in all_states:
    if state.attrib['id'] in tests_refs:
        key_state_copy = copy.deepcopy(key_state)
        state.append(key_state_copy)
    new_states.append(state)

#добавление переменных
new_variables.extend(variables)

with open("output.xml", "wb") as output_file:
    output_file.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))

