import requests
import pymorphy2
import re

from rdflib import Graph
from rdf.generator import TextToRDF


class WrapperDuplicate(TextToRDF):

    def __init__(self):
        super(WrapperDuplicate, self).__init__()

        self.morph = pymorphy2.MorphAnalyzer()

        self.namespace = {
            "ki": self.schema.ki,
            "KI": self.schema.KI
        }

        self.re_inflect = re.compile(r'\|([.\w ]+)\|')

        self.duplicate = {
            'ki:patrol': 0,
            'ki:stop': 1,
            'ki:move_dir': 2,
            'ki:rotate_dir': 3,
            'ki:move_on': 4,
            'ki:rotate_on': 5,
            'ki:move_to': 6,
            'ki:find': 7,
            'ki:go_around': 8,
            'ki:monitor': 9,
            'ki:rotate_to': 10,
            'ki:pause': 11,
            'ki:continue': 12,
            'ki:analyze': 13,

            'ki:house': 1,
            'ki:tree': 2,
            'ki:broken_tree': 3,
            'ki:forest': 4,
            'ki:pit': 5,
            'ki:human': 6,
            'ki:hill': 7,
            'ki:fissure': 8,
            'ki:man_lay': 9,
            'ki:rock': 10,
            'ki:butte': 11,
            'ki:barrier': 12,
            'ki:lamp_post': 13,
            'ki:car': 14,

            '_ki:near': 1,
            '_ki:behind_of': 2,
            '_ki:in_front_of': 3,
            '_ki:to_left_from': 4,
            '_ki:to_right_from': 5,

            'ki:behind_of': 1,
            'ki:in_front_of': 2,
            'ki:to_left_from': 3,
            'ki:to_right_from': 4,

            'ki:dir_forward': 1,
            'ki:dir_backward': 2,
            'ki:dir_right': 3,
            'ki:dir_left': 4,
            'ki:dir_north': 5,
            'ki:dir_south': 6,
            'ki:dir_east': 7,
            'ki:dir_west': 8,

            'KI:F0': 0,
            'KI:F1': 1,
            'KI:F2': 2,
            'KI:F3': 3,

            'ki:circle': 15,
            'ki:route': 16,

            None: 0
        }

        self.rus = {
            'action': {0: 'патрулирую', 1:'останавливаюсь', 2: 'двигаюсь', 3: 'поворачиваю', 4: 'двигаюсь',
                       5: 'поворачиваю', 6: 'двигаюсь к |.datv|', 7: 'ищу |.accs|', 8: 'объезжаю |.accs|',
                       9: 'осматриваю |.accs|', 10: 'поворачиваю к |.datv|', 11: 'прерываюсь', 12: 'продолжаю',
                       13: 'анализирую |.accs|'},
            'direction': {0: '', 1: 'вперед', 2: 'назад', 3: 'направо', 4: 'налево', 5: 'на север', 6: 'на юг',
                          7: 'на восток', 8: 'на запад'},
            'meters': [0],
            'degshours': [0],
            'object1': {0: '', 1: '|дом|', 2: '|дерево|', 3: '|сломанное дерево|', 4: '|лес|', 5: '|яма|', 6: '|человек|',
                        7: '|холм|', 8: '|трещина|', 9: '|лежащий человек|', 10: '|камень|', 11: '|останец|', 12: '|барьер|',
                        13: '|фонарь|', 14: '|машина|', 15: 'по кругу радиусом', 16: 'по маршруту'},
            'nearest': {0: '', 1: '|ближайший|'},
            'relation1': {0: '', 1: 'около |.gent|', 2: 'позади |.gent|', 3: 'перед |.ablt|', 4: 'слева от |.gent|',
                          5: 'справа от |.gent|'},
            'object2': {0: '', 1: '|дом|', 2: '|дерево|', 3: '|сломанное дерево|', 4: '|лес|', 5: '|яма|', 6: '|человек|',
                        7: '|холм|', 8: '|трещина|', 9: '|лежащий человек|', 10: '|камень|', 11: '|останец|', 12: '|барьер|',
                        13: '|фонарь|', 14: '|машина|'},
            'relation2': {0: '', 1: 'около |.gent|', 2: 'позади |.gent|', 3: 'перед |.ablt|', 4: 'слева от |.gent|',
                          5: 'справа от |.gent|'},
            'object3': {0: '', 1: '|дом|', 2: '|дерево|', 3: '|сломанное дерево|', 4: '|лес|', 5: '|яма|', 6: '|человек|',
                        7: '|холм|', 8: '|трещина|', 9: '|лежащий человек|', 10: '|камень|', 11: '|останец|', 12: '|барьер|',
                        13: '|фонарь|', 14: '|машина|'},
            'self': {0: '', 1: 'позади меня', 2: 'передо мной', 3: 'слева от меня', 4: 'справа от меня'},
            'gaze': {0: '', 1: 'по направлению взгляда'},
            'delayed': {0: '', 1: '', 2: '', 3: ''},
        }

    def rdf_query(self, rdf):
        """

        """
        attr = []
        result = []

        dec = bytes.decode(rdf) if type(rdf) != str else rdf
        dec = '\n'.join(list(sorted(dec.split('\n'))))

        g = Graph()
        g.parse(data=dec, format='nt')
        query = g.query(self.schema.parser, initNs=self.namespace, use_store_provided=True)

        for row in query:
            attr.append({row.a: row.action})
            if row.o:
                attr.append({row.o: row.object})
            if row.d:
                attr.append({row.d: row.direction})
            if row.dm:
                attr.append({row.dm: row.num})
            if row.n:
                attr.append({row.n: row.near})
            if row.s:
                attr.append({row.s: row.self})
            if row.gaze:
                attr.append({row.go: row.gaze})
            if row.relation:
                attr.append((row.r1, row.relation, row.r2))

        attr = [i for n, i in enumerate(attr) if i not in attr[:n]]

        if len(attr) > 1:
            for tup in attr:
                if type(tup) == tuple:
                    entity_1, entity_0, entity_2 = tup
                    relation = []
                    for dic in attr:
                        if type(dic) == dict:
                            try:
                                relation.append(dic[entity_1])
                            except KeyError:
                                pass
                    for dic in attr:
                        if type(dic) == dict:
                            try:
                                relation.append(dic[entity_2])
                            except KeyError:
                                pass

                    try:
                        if entity_0.toPython() != 'ki:patient':
                            relation.insert(1, '_' + entity_0)
                            relation.append(entity_1)
                            relation.append(entity_2)
                        else:
                            relation.insert(0, entity_1)
                            relation.append(entity_2)
                    except AttributeError:
                        pass

                    result.append(relation)
        else:
            for dic in attr:
                if type(dic) == dict:
                    result.append(list(*dic.items()))

        return result

    def rdf_to_vector(self, rdf):
        """

        """
        translated = []
        compx = []

        result = self.rdf_query(rdf)

        for cell in result:
            celled = []
            for key in cell:
                celled.append(key.toPython())

            translated.append(celled)

        parsed = list(sorted(translated))

        for act_num in ['KI:F0', 'KI:F1', 'KI:F2']:

            object1, label1 = None, None
            object2, label2 = None, None
            adds, action = None, None
            relation1, action_num = None, None
            direction, meters = None, None
            degshours, nearest = None, None
            relation2, object3 = None, None
            sf, gaze = None, None

            cp = parsed.copy()
            for line in parsed:
                if act_num in line:
                    action_num, action = line[:2]
                    attrs = line[2:]

                    if action in ['ki:move_on', 'ki:rotate_on']:
                        attrs = list(sorted(attrs))

                        object1 = attrs[-1]
                        label1 = attrs[1]
                        adds = attrs[0]

                    else:
                        if attrs:
                            object1 = attrs[0]
                            label1 = attrs[-1]

                            attrs.remove(object1)
                            attrs.remove(label1)

                        if attrs:
                            adds = attrs[0]

                    cp.remove(line)

            ccp = cp.copy()
            for line in cp:
                if object1 in line and label1 in line:
                    edit = line.copy()
                    edit.remove(object1)
                    edit.remove(label1)
                    for element in edit:
                        if '_ki:' in element:
                            relation1 = element
                            edit.remove(relation1)
                    object2 = edit[0]
                    label2 = edit[1]

                    ccp.remove(line)

            del cp
            for line in ccp:
                if object2 in line and label2 in line:
                    edit = line.copy()
                    edit.remove(object2)
                    for element in edit:
                        if '_ki:' in element:
                            relation2 = element
                            edit.remove(relation2)
                    object3 = edit[0]

            del ccp

            if adds and (action == 'ki:move_on' or action == 'ki:patrol'):
                meters = adds
            elif adds and action == 'ki:rotate_on':
                degshours = adds

            elif adds and adds != 'ki:has_gaze_focus_on' and adds != 'ki:nearest_from_type' and adds != 'ki:by_gaze_line':
                sf = adds

            elif adds == 'ki:nearest_from_type':
                nearest = 1

            elif adds == 'ki:has_gaze_focus_on':
                gaze = 1

            elif adds == 'ki:by_gaze_line':
                gaze = 1

            if not relation1 and action in ['ki:move_dir', 'ki:rotate_dir', 'ki:move_on', 'ki:rotate_on', ]:
                direction = object1
                object1 = None

            if object1 == 'ki:has_gaze_focus_on':
                gaze = 1
                object1 = None

            elif object1 == 'ki:by_gaze_line':
                gaze = 1
                object1 = None

            delayed = action_num

            vec = [
                self.duplicate[action],
                self.duplicate[direction],
                int(meters) if meters else 0,
                int(degshours) if degshours else 0,
                self.duplicate[object1],
                int(nearest) if nearest else 0,
                self.duplicate[relation1],
                self.duplicate[object2],
                self.duplicate[relation2],
                self.duplicate[object3],
                self.duplicate[sf],
                int(gaze) if gaze else 0,
                self.duplicate[delayed],
            ]

            compx.append(vec)

        return compx

    def vector_to_rus(self, vector):
        """

        """
        result = []
        gender = ''
        animacy = ''
        near = ''
        for cmd in range(len(vector)):
            vector_dict = dict(zip(self.schema.keys, vector[cmd]))
            cmd_text = []

            if (vector_dict['delayed'] != 0 and cmd != 0) or cmd == 0:
                for key, item in vector_dict.items():
                    try:
                        if self.rus[key][item]:
                            if key == 'object1':
                                tags = self.morph.parse(self.rus[key][item].replace('|', ''))[0].tag
                                gender = tags.gender
                                animacy = tags.animacy
                            else:
                                pass

                            if key == 'object1' and (vector_dict['object1'] == 15 or vector_dict['object1'] == 16):
                                cmd_text.insert(1, self.rus[key][item])
                            elif key == 'nearest':
                                n = self.rus[key][item].replace('|', '')
                                near = '|' + self.morph.parse(n)[0].inflect({gender}).word + '|'
                                cmd_text.insert(1, near)
                            else:
                                cmd_text.append(self.rus[key][item])
                    except IndexError:
                        if key == 'meters':
                            if vector_dict['action'] != 0:
                                m = f'на {str(item)} м'
                            elif vector_dict['action'] == 0 and vector_dict['object1'] == 16:
                                m = f'номер {str(item)}'
                            else:
                                m = f'{str(item)} м'
                            cmd_text.append(m)
                        elif key == 'degshours':
                            d = f'на {str(item)}\u00b0'
                            cmd_text.append(d)

            morph_text = self.text_inflect(cmd_text, gender, animacy, near)

            result.append(morph_text)

        return result

    def text_inflect(self, text, gender, animacy, near):
        """

        """
        if text:
            data = ' '.join(text)
            re_st = self.re_inflect.findall(data)

            for word in re_st:
                if '.' in word:
                    rep = f'|{word}|'
                    case = word[1:]
                    data = data.replace(rep, '', 1)
                else:
                    rep = f'|{word}|'
                    wds = []
                    for w in word.split(' '):
                        if near and gender == 'masc' and animacy == 'inan' and case != 'datv':
                            st = w
                        else:
                            st = self.morph.parse(w)[0].inflect({case}).word
                        wds.append(st)
                    wds = ' '.join(wds)
                    data = data.replace(rep, wds, 1)

            return ' '.join(data.split())
        else:
            return ''


if __name__ == '__main__':
    translate = WrapperDuplicate()

    print('NEURAL NETWORK')

    # text = ['исследуй камень', 'найди ближайший камень и анализируй камень', 'найди ближайший камень потом анализируй камень',
    #         'иди вперед 5 м, поверни направо на 30 градусов',
    #         'иди вперед 4 м потом иди к дому', 'найди ближайший дом', 'патрулируй', 'иди вперед', 'иди вперед 4 м',
    #         'поверни направо', 'поверни направо на 30 градусов', 'обходи камень', 'осмотри дом около дерева',
    #         'найди дом рядом с человеком позади леса', 'иди к тому дереву', 'иди туда', 'обойди дом слева',
    #         'патрулируй по кругу радиуса 4 м', 'иди по 2 маршруту', 'анализируй недалекую рощу',
    #         'анализируй то дерево', 'продолжай патрулировать по 2 маршруту']

    text = ['продолжай', 'пауза', 'найди камень и осмотри его', 'иди к тому дереву']

    # # from nn
    # for t in text:
    #     print(t)
    #     response = requests.post('http://192.168.1.34:8891/parse_long', json={'command': t})
    #     labels = response.json()
    #     print(labels)
    #     rdf = translate.nn_to_rdf(labels)
    #     # print(rdf)
    #     vector = translate.rdf_to_vector(rdf)
    #     # print(vector)
    #     rus = translate.vector_to_rus(vector)
    #     print(rus)
    #     print('-'*50)

    print('SEMANTIC')

    # Semantic Service
    # external - http://synt.f2robot.com:5001/
    # openvpn - http://10.8.0.34:5001/
    # text = ['патрулируй по 2 маршруту', 'анализируй дерево', 'продолжай', 'подойди к человеку', 'повернись к машине',
    #         'обойди машину', 'иди к тому дереву']

    for t in text:
        try:
            response = requests.post('http://syntax.rrcki.ru:5001/', data=t.encode('utf-8'), timeout=2.0)
            s_rdf = response.text
            print(s_rdf)
            vector = translate.rdf_to_vector(s_rdf)
            # print(vector)
            rus = translate.vector_to_rus(vector)
            print(rus)
        except requests.exceptions.ReadTimeout:
            print('семантический сервис не успел обработать команду')


