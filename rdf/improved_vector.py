import requests

from rdflib import Graph, Literal
from rdf.wrapper_duplicate import WrapperDuplicate


class ImpVector(WrapperDuplicate):

    def __init__(self):
        super(ImpVector, self).__init__()

    def action(self, act_type, act_num):
        """
        RDF шаблон действия
        """
        cmd_num = f'F{act_num}'
        a = Graph()

        if act_num == 0:
            a.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = f'F{act_num - 1}'
            a.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            a.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        a.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        a.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act_type]))

        return a.serialize(format='nt')

    def direction(self, dir_type, act_num):
        """
        RDF шаблон направления движения
        """
        cmd_num = f'F{act_num}'
        cmd_dir = f'F{act_num}_V0'
        d = Graph()

        d.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_dir]))
        d.add((self.schema.KI[cmd_dir], self.schema.ki.type, self.schema.ki.direction))
        d.add((self.schema.KI[cmd_dir], self.schema.ki.value, self.schema.ki[dir_type]))

        return d.serialize(format='nt')

    def value(self, val_type, act_num):
        """
        RDF шаблон для числовых значений
        """
        cmd_mtr = f'F{act_num}_V0'
        m = Graph()

        m.add((self.schema.KI[cmd_mtr], self.schema.ki.numeric_value, Literal(val_type)))

        return m.serialize(format='nt')

    def object1(self, obj_type, act_num):
        """
        RDF шаблон для объекта, связанного с действием
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V0'
        o1 = Graph()

        if obj_type not in ['route', 'circle']:
            o1.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj]))
            o1.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki.object))
            o1.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki[obj_type]))
        else:
            o1.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj]))
            o1.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki[obj_type]))

        return o1.serialize(format='nt')

    def nearest(self, obj_type, act_num):
        """
        RDF шаблон для ближнего к роботу объекта
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V0'
        n = Graph()

        n.add((self.schema.KI[cmd_obj], self.schema.ki.nearest_from_type, self.schema.ki[obj_type]))

        return n.serialize(format='nt')

    def relation1(self, rel_type, act_num):
        """
        RDF шаблон для отношения первой степени
        """
        cmd_num = f'F{act_num}'
        cmd_obj1 = f'F{act_num}_V0'
        cmd_obj2 = f'F{act_num}_V1'
        r1 = Graph()

        r1.add((self.schema.KI[cmd_obj1], self.schema.ki[rel_type], self.schema.KI[cmd_obj2]))

        return r1.serialize(format='nt')

    def object2(self, obj_type, act_num):
        """
        RDF шаблон для объекта, связанного отношением первой степени
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V1'
        o2 = Graph()

        o2.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki.object))
        o2.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki[obj_type]))

        return o2.serialize(format='nt')

    def relation2(self, rel_type, act_num):
        """
        RDF шаблон для отношения второй степени
        """
        cmd_num = f'F{act_num}'
        cmd_obj1 = f'F{act_num}_V1'
        cmd_obj2 = f'F{act_num}_V2'
        r2 = Graph()

        r2.add((self.schema.KI[cmd_obj1], self.schema.ki[rel_type], self.schema.KI[cmd_obj2]))

        return r2.serialize(format='nt')

    def object3(self, obj_type, act_num):
        """
        RDF шаблон для объекта, связанного отношением второй степени
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V2'
        o3 = Graph()

        o3.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki.object))
        o3.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki[obj_type]))

        return o3.serialize(format='nt')

    def slf(self, self_type, act_num):
        """
        RDF шаблон для отношения объекта относительно робота
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V0'
        s = Graph()

        s.add((self.schema.KI[cmd_obj], self.schema.ki[self_type], self.schema.ki.me))

        return s.serialize(format='nt')

    def gaze(self, obj_type, act_num):
        """
        RDF шаблон для учета направления взгляда
        """
        cmd_num = f'F{act_num}'
        cmd_obj = f'F{act_num}_V0'
        g = Graph()

        if not obj_type:
            g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj]))
            g.add((self.schema.KI[cmd_obj], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.ki.me, self.schema.ki.by_gaze_line, self.schema.KI[cmd_obj]))

        return g.serialize(format='nt')

    def nn_to_rdf(self, jsn):
        """
        Улучшенная версия восстановления RDF из вектора
        """
        commands = []
        keys = self.schema.keys

        for action_num, cmd in enumerate(jsn['parse_result']):

            values = ['' for _ in range(len(keys))]
            result = dict(zip(keys, values))

            for key, value, _ in cmd:
                result[key] = value

            one = ''
            for key, value, in result.items():

                if value:
                    if key == 'action':
                        one += self.action(act_type=value, act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'direction':
                        one += self.direction(dir_type=value, act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'meters' or key == 'degshours':
                        one += self.value(val_type=value, act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'object1':
                        one += self.object1(obj_type=value, act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'nearest':
                        one += self.nearest(obj_type=result['object1'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'relation1':
                        one += self.relation1(rel_type=result['relation1'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'object2':
                        one += self.object2(obj_type=result['object2'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'relation2':
                        one += self.relation2(rel_type=result['relation2'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'object3':
                        one += self.object3(obj_type=result['object3'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'self':
                        one += self.slf(self_type=result['self'], act_num=action_num).decode().strip()
                        one += '\n'
                    if key == 'gaze':
                        one += self.gaze(obj_type=result['object1'], act_num=action_num).decode().strip()
                        one += '\n'

            one += '\n'
            commands.append(one)

        return '\n'.join(commands)


if __name__ == '__main__':
    gen = ImpVector()

    text = [
        # 'патрулируй', 'иди вперед', 'поверни направо',
        # 'патрулируй, потом иди вперед, затем поверни направо',
        # 'шагай вперед 5 метров', 'поверни на 1.5 часа', 'поверни налево на 30 градусов',
        # 'двигайся вперед 5 метров, потом направо на 3 часа и налево на 45 градусов',
        # 'иди к дому', 'найди дерево', 'объезжай человека', 'осмотри камень', 'анализируй яму', 'поверни к лампе',
        # 'иди к дому, потом найди дерево, далее объезжай человека, затем осмотри камень, после анализируй яму, наконец поверни к лампе',
        # 'патрулируй по 2 маршруту', 'патрулируй по кругу радиуса 1 м',
        # 'патрулируй по 2 маршруту, а потом патрулируй по кругу радиуса 1 м',
        # 'иди к ближайшему дому', 'найди ближайешее дерево', 'объезжай ближайшего человека',
        # 'осмотри ближайший камень', 'анализируй ближайшую яму', 'поверни к ближайшей лампе'
        # 'иди к ближайшему дому, потом найди ближайешее дерево, далее объезжай ближайшего человека, затем осмотри ближайший камень, после анализируй ближайшую яму и поверни к ближайшей лампе',
        # 'иди к дому около дерева', 'найди забор перед человеком', 'объедь фонарь справа от леса',
        # 'осмотри машину слева от камня', 'анализируй яму позади трещины', 'поверни к горе рядом с домом'
        # 'иди к дому около дерева, после найди забор перед человеком, объедь фонарь справа от леса, затем осмотри машину слева от камня, потом анализируй яму позади трещины поверни к горе рядом с домом',
        # 'иди к дому около человека перед камнем', 'найди дерево рядом с каменем около дома',
        # 'обходи лес за домом который слева от человека', 'осматривай камень слева от дерева, которое слева от дома',
        # 'иди к дому около человека перед камнем найди дерево рядом с каменем около дома',
        # 'иди к дому слева от тебя', 'обойди человека справа', 'анализируй камень впереди',
        # 'иди к дому слева от тебя обойди человека справа анализируй камень впереди',
        # 'иди туда', 'иди к этому дереву',
        'двигайся направо'
    ]

    for t in text:
        # print(t)
        response = requests.post('http://192.168.1.34:8891/parse_long', json={'command': t})
        labels = response.json()
        print(labels)
        rdf = gen.nn_to_rdf(labels)
        # print(rdf)
        # vector = gen.rdf_to_vector(rdf)
        # # print(vector)
        # rus = gen.vector_to_rus(vector)
        # print(rus)
        # print('-'*50)