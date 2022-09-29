import requests

from rdflib import Graph, Namespace, Literal


class Schema:
    
    ki = Namespace("ki:")
    KI = Namespace("KI:")
    
    keys = ['action', 'direction', 'meters', 'degshours', 'object1', 'nearest',
            'relation1', 'object2', 'relation2', 'object3', 'self', 'gaze',
            'delayed']

    vector = {'action': {'patrol': 0, 'stop': 1, 'move_dir': 2, 'rotate_dir': 3,
                         'move_on': 4, 'rotate_on': 5, 'move_to': 6, 'find': 7,
                         'go_around': 8, 'monitor': 9, 'rotate_to': 10, 'pause': 11,
                         'continue': 12, 'analyze': 13},
              'direction': {'': 0, 'dir_forward': 1, 'dir_backward': 2,
                            'dir_right': 3, 'dir_left': 4, 'dir_north': 5,
                            'dir_south': 6, 'dir_east': 7, 'dir_west': 8},
              'meters': {'': 0, '1': 1, '2': 2, '5': 3, '7': 4, '10': 5,
                         '15': 6, '20': 7, '25': 8, '35': 9, '50': 10, '75': 11,
                         '100': 12},
              'degshours': {'': 0, '15': 1, '30': 2, '45': 3, '60': 4, '75': 5,
                            '90': 6, '105': 7, '120': 8, '135': 9, '150': 10,
                            '165': 11, '180': 12, '195': 13, '210': 14,
                            '225': 15, '240': 16, '255': 17, '270': 18,
                            '285': 19, '300': 20, '315': 21, '330': 22,
                            '345': 23, '360': 24},
              'object1': {'': 0, 'house': 1, 'tree': 2, 'broken_tree': 3,
                          'forest': 4, 'pit': 5, 'human': 6, 'hill': 7,
                          'fissure': 8, 'man_lay': 9, 'rock': 10, 'butte': 11,
                          'barrier': 12, 'lamp_post': 13, 'car': 14, 'circle': 15,
                          'route': 16},
              'nearest': {'': 0, 'nearest_from_type': 1},
              'relation1': {'': 0, 'near': 1, 'behind_of': 2, 'in_front_of': 3,
                            'to_left_from': 4, 'to_right_from': 5},
              'object2': {'': 0, 'house': 1, 'tree': 2, 'broken_tree': 3,
                          'forest': 4, 'pit': 5, 'human': 6, 'hill': 7,
                          'fissure': 8, 'man_lay': 9, 'rock': 10, 'butte': 11,
                          'barrier': 12, 'lamp_post': 13, 'car': 14},
              'relation2': {'': 0, 'near': 1, 'behind_of': 2, 'in_front_of': 3,
                            'to_left_from': 4, 'to_right_from': 5},
              'object3': {'': 0, 'house': 1, 'tree': 2, 'broken_tree': 3,
                          'forest': 4, 'pit': 5, 'human': 6, 'hill': 7,
                          'fissure': 8, 'man_lay': 9, 'rock': 10, 'butte': 11,
                          'barrier': 12, 'lamp_post': 13, 'car': 14},
              'self': {'': 0, 'behind_of': 1, 'in_front_of': 2, 'to_left_from': 3,
                       'to_right_from': 4},
              'gaze': {'': 0, 'has_gaze_focus_on': 1},
              'delayed': {0: 0, 1: 1, 2: 2}}

    parser = """
    SELECT *
    WHERE {
            {?a ki:action_type ?action .
                
                OPTIONAL {?r1 ?relation ?r2 .
                            FILTER (
                                    (str(?relation) = str(ki:patient) ||
                                     str(?relation) = str(ki:near) ||
                                     str(?relation) = str(ki:behind_of) ||
                                     str(?relation) = str(ki:in_front_of) ||
                                     str(?relation) = str(ki:to_left_from) ||
                                     str(?relation) = str(ki:to_right_from)) &&
                                     str(?r2) != str(ki:me)
                        
                                    )
                         }
                
                OPTIONAL {?o ki:type ?object .
                            FILTER (
                                    str(?object) != str(ki:object) &&
                                    str(?object) != str(ki:action) &&
                                    str(?object) != str(ki:direction) &&
                                    str(?object) != str(ki:delayed_action)
                                   )
                         }
                         
                OPTIONAL {?d ki:value ?direction .}
                
                OPTIONAL {?dm ki:numeric_value ?num .}
                
                OPTIONAL {?n ?near ?nn .
                            FILTER (
                                    str(?near) = str(ki:nearest_from_type)
                                   )
                         }
                         
                OPTIONAL {?s ?self ki:me .
                            FILTER (
                                    str(?self) != str(ki:actor) &&
                                    str(?self) != str(ki:subject)
                                   )   
                         }
                         
                OPTIONAL {?g ?gaze ?go .
                            FILTER (
                                    str(?gaze) = str(ki:has_gaze_focus_on) ||
                                    str(?gaze) = str(ki:by_gaze_line)
                                   )
                         }
            }
        
          }
    """


class TextToRDF:

    def __init__(self):
        self.schema = Schema()

        g = Graph()
        g.query(self.schema.parser,
                initNs={"ki": self.schema.ki,
                        "KI": self.schema.KI},
                use_store_provided=True)

    @staticmethod
    def _get_key(d, val):
        """
        Получение ключа словаря по значению
        Args:
            d: словарь
            val: значение

        Returns:
            ключ словаря
        """
        for k, v in d.items():
            if v == val:
                if k:
                    return k

    def nn_to_rdf(self, jsn):
        """
        Расшифровывает векторное представление в RDF формат
        Args:
            jsn: закодированный RDF
        Returns:
            RDF
        """
        commands = []
        for action_num, cmd in enumerate(jsn['parse_result']):

            values = [0 for _ in range(len(self.schema.keys))]
            result = dict(zip(self.schema.keys, values))

            for key in cmd:
                result[key[0]] = self.schema.vector[key[0]][key[1]]

            key_words = []
            for i, val in enumerate(list(result.values())):
                key_schema = self.schema.keys[i]
                type_of = self.schema.vector[key_schema]

                key_words.append(self._get_key(type_of, val))

            result = dict(zip(self.schema.keys, key_words))

            if (result['action']) and \
                    (not result['direction']) and \
                    (not result['object1']) and \
                    (not result['meters']) and \
                    (not result['gaze']):

                commands.append(self.move_simple(n=action_num, act=result['action']).decode())
                continue

            elif (result['direction']) and \
                    (not result['meters']) and \
                    (not result['degshours']):

                commands.append(self.move_direction(n=action_num, act=result['action'],
                                                    direct=result['direction']).decode())
                continue

            elif (result['meters']) and \
                    (result['direction']):

                commands.append(self.move_direction_numeric(n=action_num, direct=result['direction'],
                                                            num=result['meters']).decode())
                continue

            elif result['degshours']:

                commands.append(self.rotate_direction_numeric(n=action_num, direct=result['direction'],
                                                              num=result['degshours']).decode())
                continue

            elif (result['object1']) and \
                    (not result['nearest']) and \
                    (not result['object2']) and \
                    (not result['self']) and \
                    (not result['gaze']) and \
                    (not result['meters']):

                commands.append(self.move_to_object(n=action_num, act=result['action'],
                                                    obj1=result['object1']).decode())
                continue

            elif result['nearest']:

                commands.append(self.move_to_nearest_object(n=action_num, act=result['action'],
                                                            obj1=result['object1']).decode())
                continue

            elif (result['object2']) and \
                    (not result['object3']):

                commands.append(self.move_to_object_relation1(n=action_num, act=result['action'],
                                                              obj1=result['object1'],
                                                              rel1=result['relation1'],
                                                              obj2=result['object2']).decode())
                continue

            elif result['object3']:

                commands.append(self.move_to_object_relation2(n=action_num, act=result['action'],
                                                              obj1=result['object1'],
                                                              rel1=result['relation1'], obj2=result['object2'],
                                                              rel2=result['relation2'],
                                                              obj3=result['object3']).decode())
                continue

            elif result['object1'] == 'circle':

                commands.append(self.patrol_circle(n=action_num, num=result['meters']).decode())
                continue

            elif result['object1'] == 'route':

                commands.append(self.patrol_on_route(route=result['meters']).decode())
                continue

            elif result['self']:

                commands.append(self.move_selfrelation_object(n=action_num, act=result['action'],
                                                              obj1=result['object1'], selfrel=result['self']).decode())
                continue

            elif result['gaze']:

                commands.append(self.move_gaze_focus_on(n=action_num, act=result['action'],
                                                        obj1=result['object1']).decode())
                continue

        text = ''.join(commands)

        return text

    def move_simple(self, n=0, act='ACTION'):
        """
        Шаблон для простых команд
        Пример: патрулируй, остановись
        Args:
            n: порядок действия, для составных команд
            act: возможные действия (patrol, stop)
        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))

        return g.serialize(format='nt')

    def move_direction(self, n=0, act='ACTION', direct='DIRECTION'):
        """
        Шаблон для команды движения/поворота в направлении
        Пример: двигайся вперед, поверни направо
        Args:
            n: порядок действия, для составных команд
            act: возможные действия (move_dir, rotote_dir)
            direct: направление движения (dir_forward, dir_north..)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.direction))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.value, self.schema.ki[direct]))

        return g.serialize(format='nt')

    def move_direction_numeric(self, n=0, direct='DIRECTION', num='NUMERIC'):
        """
        Шаблон для команды движения в направлении на расстояние
        Пример: двигайся вперед 2 метра
        Args:
            n: порядок действия, для составных команд
            direct: направление движения (dir_forward, dir_north...)
            num: числовое значение (метры)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki.move_on))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.direction))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.value, self.schema.ki[direct]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.numeric_value, Literal(num)))

        return g.serialize(format='nt')

    def rotate_direction_numeric(self, n=0, direct='DIRECTION', num='NUMERIC'):
        """
        Шаблон для команды поворота в направлении на угол
        Пример: поверни направо на 30 градусов
        Args:
            n: порядок действия, для составных команд
            direct: направление движения (dir_forward, dir_north...)
            num: числовое значение (градусы, часы)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki.rotate_on))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.direction))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.value, self.schema.ki[direct]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.numeric_value, Literal(num)))

        return g.serialize(format='nt')

    def move_to_object(self, n=0, act='ACTION', obj1='OBJECT1'):
        """
        Шаблон для команды движения к объекту
        Пример: двигайся к дому
        Args:
            n: порядок действия, для составных команд
            act: тип действия, искать/идти к/объезжать/осматривать (move_to, find, go_around, monitor)
            obj1: объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))

        return g.serialize(format='nt')

    def move_to_nearest_object(self, n=0, act='move_to', obj1='OBJECT1'):
        """
        Шаблон для команды движения к ближайшему объекту
        Пример: двигайся к к ближайшему дому
        Args:
            n: порядок действия, для составных команд
            act: выбор действия (move_to, find, go_around, monitor)
            obj1: объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.nearest_from_type, self.schema.ki[obj1]))

        return g.serialize(format='nt')

    def move_to_object_relation1(self, n=0, act='move_to', obj1='OBJECT1', rel1='RELATION1', obj2='OBJECT2'):
        """
        Шаблон для команды движения с одним отношением
        Пример: двигайся к дому около дерева
        Args:
            n: порядок действия, для составных команд
            act: выбор действия (move_to, find, go_around, monitor)
            obj1: целевой объект мира (house, human...)
            rel1: отношение между объектами (near, behind_of...)
            obj2: зависимый объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        cmd_obj2 = cmd_num + '_V1'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki[rel1], self.schema.KI[cmd_obj2]))
        g.add((self.schema.KI[cmd_obj2], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj2], self.schema.ki.type, self.schema.ki[obj2]))

        return g.serialize(format='nt')

    def move_to_object_relation2(self, n=0, act='move_to', obj1='OBJECT1', rel1='RELATION1', obj2='OBJECT2', rel2='RELATION2', obj3='OBJECT3'):
        """
        Шаблон для команды движения с двумя отношениями
        Пример: двигайся к дому около дерева рядом с камнем
        Args:
            n: порядок действия, для составных команд
            act: выбор действия (move_to, find, go_around, monitor)
            obj1: целевой объект мира (house, human...)
            rel1: отношение между объектами (near, behind_of...)
            obj2: зависимый объект мира (house, human...)
            rel2: отношение между объектами (near, behind_of...)
            obj3: зависимый объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        cmd_obj2 = cmd_num + '_V1'
        cmd_obj3 = cmd_num + '_V2'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki[rel1], self.schema.KI[cmd_obj2]))
        g.add((self.schema.KI[cmd_obj2], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj2], self.schema.ki.type, self.schema.ki[obj2]))
        g.add((self.schema.KI[cmd_obj2], self.schema.ki[rel2], self.schema.KI[cmd_obj3]))
        g.add((self.schema.KI[cmd_obj3], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj3], self.schema.ki.type, self.schema.ki[obj3]))

        return g.serialize(format='nt')

    def patrol_circle(self, n=0, num='NUMERIC'):
        """
        Шаблон для команды патрулирования по кругу с заданным радиусом
        Args:
            n: порядок действия для составных команд
            num: числовое значения радиуса в метрах

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki.patrol))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.circle))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.numeric_value, Literal(num)))

        return g.serialize(format='nt')

    def move_selfrelation_object(self, n=0, act='ACTION', obj1='OBJECT1', selfrel='SELFRELATION'):
        """
        Шаблон для команды движения/поиска/осмотра/объезда объекта относительно робота
        Args:
            n: порядок действия для составных команд
            act: тип действия, искать/идти к/объезжать/осматривать (move_to, find, go_around, monitor)
            obj1: целевой объект мира (house, human...)
            selfrel: относительно робота

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki[selfrel], self.schema.ki.me))

        return g.serialize(format='nt')

    def move_gaze_focus_on(self, n=0, act='move_to', obj1=None):
        """
        Шаблон для команды движения по направлению взгляда
        Args:
            n: порядок действия для составных команд
            act: выбор действия (move_to, find, go_around, monitor)
            obj1: целевой объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki[act]))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.object))
        # g.add((self.schema.ki.me, self.schema.ki.has_gaze_focus_on, self.schema.KI[cmd_obj1]))
        g.add((self.schema.ki.me, self.schema.ki.by_gaze_line, self.schema.KI[cmd_obj1]))

        if obj1:
            g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki[obj1]))

        return g.serialize(format='nt')

    def patrol_on_route(self, route, n=0):
        """

        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.action))
        else:
            prev_num = 'F' + str(n - 1)
            g.add((self.schema.KI[cmd_num], self.schema.ki.after, self.schema.KI[prev_num]))
            g.add((self.schema.KI[cmd_num], self.schema.ki.type, self.schema.ki.delayed_action))
        g.add((self.schema.KI[cmd_num], self.schema.ki.actor, self.schema.ki.me))
        g.add((self.schema.KI[cmd_num], self.schema.ki.action_type, self.schema.ki.patrol))
        g.add((self.schema.KI[cmd_num], self.schema.ki.patient, self.schema.KI[cmd_obj1]))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.type, self.schema.ki.route))
        g.add((self.schema.KI[cmd_obj1], self.schema.ki.numeric_value, Literal(route)))

        return g.serialize(format='nt')


if __name__ == '__main__':
    gen = TextToRDF()
    schema = Schema()

    print('иди к дому около дерева позади человека')

    print('\n\n')

    # from generate
    rdf = gen.move_to_object_relation2(act='move_to', obj1='house', rel1='near', obj2='tree', rel2='behind_of', obj3='human')
    print(bytes.decode(rdf))
    parser_1, parser_2 = gen.rdf_to_dict(rdf)
    print(parser_1, parser_2, sep='---')

    print('\n\n')

    # Semantic Service
    semantic_addr = 'http://10.8.0.34:5001/'  # http://synt.f2robot.com:5001/ http://10.8.0.34:5001/
    command_text_init = 'иди к дому около дерева позади человека'
    response = requests.post(semantic_addr, data=command_text_init.encode('utf-8'), timeout=10.0)
    rdf = response.text
    print(rdf)
    parser_1, parser_2 = gen.rdf_to_dict(rdf)
    print(parser_1, parser_2, sep='---')




