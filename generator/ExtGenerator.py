import os
import random
import pymorphy2
import pandas as pd
import json
import math

from generator.Generator import Generator
from rdf.wrapper_duplicate import WrapperDuplicate

PATH = os.path.join(os.path.dirname(__file__), 'dictionary')


class Dictionary:

    @staticmethod
    def file_to_uniq_list(dictionary):
        path = os.path.join(PATH, dictionary)

        with open(path, 'r') as file:
            data_from_file = file.read()
            list_data = data_from_file.split('\n')
            set_data = set(list_data)
            uniq_data = list(set_data)

        return uniq_data

    @staticmethod
    def json_to_dict(dictionary):
        path = os.path.join(PATH, dictionary)

        with open(f"{path}.json", 'r') as file:
            data = json.load(file)

        return data

    def __init__(self):
        self.patrol = self.file_to_uniq_list('patrol')
        self.stop = self.file_to_uniq_list('stop')

        self.move = self.file_to_uniq_list('move')
        self.rotate = self.file_to_uniq_list('rotate')
        self.inf = self.file_to_uniq_list('inf')

        self.dir_forward = self.file_to_uniq_list('dir_forward')
        self.dir_backward = self.file_to_uniq_list('dir_backward')
        self.dir_left = self.file_to_uniq_list('dir_left')
        self.dir_right = self.file_to_uniq_list('dir_right')
        self.dir_north = self.file_to_uniq_list('dir_north')
        self.dir_south = self.file_to_uniq_list('dir_south')
        self.dir_east = self.file_to_uniq_list('dir_east')
        self.dir_west = self.file_to_uniq_list('dir_west')

        self.move_schema = {0: ('move_dir', self.move), 1: ('rotate_dir', self.rotate)}

        self.dir_schema = {0: ('dir_forward', self.dir_forward), 1: ('dir_backward', self.dir_backward),
                           2: ('dir_left', self.dir_left), 3: ('dir_right', self.dir_right),
                           4: ('dir_north', self.dir_north), 5: ('dir_south', self.dir_south),
                           6: ('dir_east', self.dir_east), 7: ('dir_west', self.dir_west)}

        self.find = self.file_to_uniq_list('find')
        self.go_around = self.file_to_uniq_list('go_around')
        self.explore = self.file_to_uniq_list('monitor')
        self.analyze = self.file_to_uniq_list('analyze')
        self.objects = self.json_to_dict('objects')

        self.to_obj_schema = {0: ('move_to', self.move), 1: ('find', self.find), 2: ('go_around', self.go_around),
                              3: ('monitor', self.explore), 4: ('rotate_to', self.rotate), 5: ('analyze', self.analyze)}

        self.nearest = self.file_to_uniq_list('nearest')

        self.relation = self.json_to_dict('relation')
        self.that = self.file_to_uniq_list('that')
        self.participle = self.file_to_uniq_list('participle')

        self.circle = self.file_to_uniq_list('circle')
        self.radius = self.file_to_uniq_list('radius')

        self.robot_rel = self.json_to_dict('self_rel')
        self.robot_name = self.file_to_uniq_list('self_name')

        self.focus = self.file_to_uniq_list('focus')
        self.focus_obj = self.file_to_uniq_list('focus_obj')

        self.needs = self.file_to_uniq_list('needs')

        self.after = self.file_to_uniq_list('after')

        self.turn_around = self.file_to_uniq_list('turn_around')
        self.after_turn_around = self.file_to_uniq_list('after_turn_around')

        self.pause = self.file_to_uniq_list('pause')
        self.cont = self.file_to_uniq_list('continue')

        self.route = self.file_to_uniq_list('route')


def df_dec(method_to_decorate):
    """
    Декоратор, создает таблицу DataFrame из данных генератора
    Удаялет дублирующиеся строки
    Args:
        method_to_decorate: метод, генерирующий шаблоны команд

    Returns:
        DataFrame с уникальными командами
    """
    def wrapper(self, patience, pattern, save=True, n=0, yandex_key=False):
        """

        Args:
            self:
            patience:
            pattern:
            save:
            n:
            yandex_key:

        Returns:

        """

        if yandex_key:
            data = method_to_decorate(self, patience, pattern, save, n, yandex_key)
        else:
            data = method_to_decorate(self, patience, pattern, save, n)

        if save:
            columns = ['x', 'y_name', 'y'] + self.voc.keys + ['type']
            data = pd.DataFrame(data=data, columns=columns)
            uniq_data = data.drop_duplicates().reset_index(drop=True)
            uniq_data.to_csv(os.path.join(os.path.dirname(__file__), 'ext_data', f'{pattern}.csv'), sep=';', index=False)
            return uniq_data
        else:
            return data

    return wrapper


class ExtGenerator(Generator):

    def __init__(self):
        super(ExtGenerator, self).__init__()
        self.dictionary = Dictionary()
        self.morph = pymorphy2.MorphAnalyzer()

        # TODO:
        self.duplicate = WrapperDuplicate()

    def infinitive(self, word):
        """
        Делает из глагола инфинитив
        Args:
            word: глагол в любой форме

        Returns:
            инфинитив
        """
        ws = word.split(' ')
        if len(ws) == 1:
            words = self.morph.parse(word)

            for word in words:
                if word.tag.POS == 'VERB':
                    word = word
                    break

            try:
                return word.inflect({'INFN', 'impf'}).word
            except AttributeError:
                return None
                # try:
                #     return word.inflect({'INFN'}).word
                # except AttributeError:
                #     return word.word

        else:
            words = self.morph.parse(ws[0])

            for word in words:
                if word.tag.POS == 'VERB':
                    word = word
                    break

            try:
                return ' '.join([word.inflect({'INFN', 'impf'}).word] + ws[1:])
            except AttributeError:
                return None
                # return ' '.join(ws)
                # return ' '.join([word.inflect({'INFN'}).word] + ws[1:])

    @df_dec
    def gen_simple(self, patience, pattern, save, n):
        """
        Генератор простых команд "патрулируй" и "стой"
        Args:
            patience:
            pattern:
            save:
            n:
        Returns:

        """
        simple = []
        for cmd in self.dictionary.patrol:
            text = cmd
            rdf = self.move_simple(n=n, act='patrol')
            vector = self.rdf_to_nn(rdf)

            simple.append([text, pattern, 0, *vector, 'generator'])

        for cmd in self.dictionary.stop:
            text = cmd
            rdf = self.move_simple(n=n, act='stop')
            vector = self.rdf_to_nn(rdf)

            simple.append([text, pattern, 0, *vector, 'generator'])

        for cmd in self.dictionary.pause:
            text = cmd
            rdf = self.move_simple(n=n, act='pause')
            vector = self.rdf_to_nn(rdf)

            simple.append([text, pattern, 0, *vector, 'generator'])

        for cmd in self.dictionary.cont:
            text = cmd
            rdf = self.move_simple(n=n, act='continue')
            vector = self.rdf_to_nn(rdf)

            simple.append([text, pattern, 0, *vector, 'generator'])

        if not save:
            simple = (random.choice(simple), '')

        return simple

    @df_dec
    def gen_direction(self, patience, pattern, save, n):
        """
        Генератор команд типа "двигайся вперед" / "поворачивай направо"
        Случайно выбирает слова из словарей
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        direction = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1) # использование вспомогательного глагола
            # coin_verb = random.randint(0, 1) # выбор между движением и поворотом
            coin_verb = random.choice(list(self.dictionary.move_schema.keys()))
            coin_nan = random.randint(0, 10) # использование указания направления

            verb = random.choice(self.dictionary.move_schema[coin_verb][1])

            # если выбран поворот выбираем направления 2-7
            if coin_verb:
                coin_dir = random.randint(2, 7)
                drct = random.choice(self.dictionary.dir_schema[coin_dir][1])
            else:
                coin_dir = random.randint(0, 7)
                drct = random.choice(self.dictionary.dir_schema[coin_dir][1])

            # если выбран вспомогательный глагол, делаем инфинитив
            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            try:
                if coin_nan >= 3:
                    text = ' '.join([inf, verb_inf, drct])
                else:
                    text = ' '.join([inf, verb_inf])
            except TypeError:
                if coin_nan >= 3:
                    text = ' '.join([verb, drct])
                else:
                    text = ' '.join([verb])

            act = self.dictionary.move_schema[coin_verb][0]

            # если >= 3 то используем слова направлений
            if coin_nan >= 3:
                direct = self.dictionary.dir_schema[coin_dir][0]
            # иначе ставим слова направлений в RDF по умолчанию
            else:
                if coin_verb:
                    direct = 'dir_right'
                else:
                    direct = 'dir_forward'

            rdf = self.move_direction(n=n, act=act, direct=direct)
            vector = self.rdf_to_nn(rdf)

            if save:
                direction.append([text, pattern, 1, *vector, 'generator'])
            else:
                direction = ([text, pattern, 1, *vector, 'generator'], '')

        return direction

    @df_dec
    def gen_meter(self, patience, pattern, save, n):
        """
        Генератор команд типа "двигайся вперед на 5 метров"
        Случайно выбирает слова из словарей
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        meter = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            coin_nan = random.randint(0, 10)
            coin_flip = random.randint(0, 1)

            verb = random.choice(self.dictionary.move) # move_on

            coin_dir = random.randint(0, 7)
            drct = random.choice(self.dictionary.dir_schema[coin_dir][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            prefix = random.choice(self.voc.pretext).strip()
            meter_key = random.choice(list(self.voc.meters.keys()))
            num = random.choice(self.voc.meters[meter_key])
            name = random.choice(self.voc.measure['meters'])
            postfix = str(num) + self.agree_with_number(name, num)
            distance = ' '.join([prefix, postfix]).strip()

            try:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([inf, verb_inf, drct, distance])
                    else:
                        text = ' '.join([inf, verb_inf, distance, drct])
                else:
                    text = ' '.join([inf, verb_inf, distance])
            except TypeError:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([verb, drct, distance])
                    else:
                        text = ' '.join([verb, distance, drct])
                else:
                    text = ' '.join([verb, distance])

            if coin_nan >= 3:
                direct = self.dictionary.dir_schema[coin_dir][0]
            else:
                direct = 'dir_forward'

            num = str(meter_key)
            rdf = self.move_direction_numeric(n=n, direct=direct, num=num)
            vector = self.rdf_to_nn(rdf)

            if save:
                meter.append([text, pattern, 2, *vector, 'generator'])
            else:
                meter = ([text, pattern, 2, *vector, 'generator'], '')

        return meter

    @df_dec
    def gen_degree(self, patience, pattern, save, n):
        """
        Генератор команд типа "поворачивай направо на 60 градусов"
        Случайно выбирает слова из словарей
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        degree = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            coin_nan = random.randint(0, 10)
            coin_flip = random.randint(0, 1)

            verb = random.choice(self.dictionary.rotate) # rotate_on

            coin_dir = random.randint(2, 7)
            drct = random.choice(self.dictionary.dir_schema[coin_dir][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            prefix = random.choice(self.voc.pretext).strip()
            degree_key = random.choice(list(self.voc.degrees.keys()))
            num = random.choice(self.voc.degrees[degree_key])
            name = random.choice(self.voc.measure['degrees'])
            postfix = str(num) + self.agree_with_number(name, num)
            distance = ' '.join([prefix, postfix]).strip()

            try:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([inf, verb_inf, drct, distance])
                    else:
                        text = ' '.join([inf, verb_inf, distance, drct])
                else:
                    text = ' '.join([inf, verb_inf, distance])
            except TypeError:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([verb, drct, distance])
                    else:
                        text = ' '.join([verb, distance, drct])
                else:
                    text = ' '.join([verb, distance])

            if coin_nan >= 3:
                direct = self.dictionary.dir_schema[coin_dir][0]
            else:
                direct = 'dir_right'

            num = str(degree_key)
            rdf = self.rotate_direction_numeric(n=n, direct=direct, num=num)
            vector = self.rdf_to_nn(rdf)

            if save:
                degree.append([text, pattern, 3, *vector, 'generator'])
            else:
                degree = ([text, pattern, 3, *vector, 'generator'], '')

        return degree

    @df_dec
    def gen_turn_around(self, patience, pattern, save, n=0):
        """

        Args:
            patience:
            pattern:
            save:
            n:

        Returns:

        """
        turn_around = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            verb = random.choice(self.dictionary.turn_around)
            after = random.choice(self.dictionary.after_turn_around)

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            try:
                text = ' '.join([inf, verb_inf, after])
            except TypeError:
                text = ' '.join([verb, after])

            rdf = self.rotate_direction_numeric(n=n, direct='dir_left', num='180')
            vector = self.rdf_to_nn(rdf)

            if save:
                turn_around.append([text, pattern, 3, *vector, 'generator'])
            else:
                turn_around = ([text, pattern, 3, *vector, 'generator'], '')

        return turn_around

    @df_dec
    def gen_hour(self, patience, pattern, save=True, n=0, yandex_key=False):
        """
        Генератор команд типа "поворачивай направо на 6:00"
        Случайно выбирает слова из словарей
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        hour = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            coin_nan = random.randint(0, 10)
            coin_flip = random.randint(0, 1)

            verb = random.choice(self.dictionary.rotate)  # rotate_on

            coin_dir = random.randint(2, 7)
            drct = random.choice(self.dictionary.dir_schema[coin_dir][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            prefix = random.choice(self.voc.pretext).strip()

            if yandex_key:
                hour_key = random.choice(list(self.voc.hours_yandex.keys()))
                num = random.choice(self.voc.hours_yandex[hour_key])
            else:
                hour_key = random.choice(list(self.voc.hours.keys()))
                num = random.choice(self.voc.hours[hour_key])

            distance = ' '.join([prefix, num]).strip()

            try:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([inf, verb_inf, drct, distance])
                    else:
                        text = ' '.join([inf, verb_inf, distance, drct])
                else:
                    text = ' '.join([inf, verb_inf, distance])
            except TypeError:
                if coin_nan >= 3:
                    if coin_flip:
                        text = ' '.join([verb, drct, distance])
                    else:
                        text = ' '.join([verb, distance, drct])
                else:
                    text = ' '.join([verb, distance])

            if coin_nan >= 3:
                direct = self.dictionary.dir_schema[coin_dir][0]
            else:
                direct = 'dir_right'

            num = str(hour_key)
            rdf = self.rotate_direction_numeric(n=n, direct=direct, num=num)
            vector = self.rdf_to_nn(rdf)

            if save:
                hour.append([text, pattern, 4, *vector, 'generator'])
            else:
                hour = ([text, pattern, 4, *vector, 'generator'], '')

        return hour

    @df_dec
    def gen_object(self, patience, pattern, save, n=0):
        """
        Генератор команд типа "двигайся/искать/обгонять/исследовать к дому"
        Случайно выбирает слова из словарей
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        obj = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            # coin_verb = random.randint(0, 4)
            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))

            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            obj_key = random.choice(list(self.dictionary.objects.keys()))
            name = random.choice(list(self.dictionary.objects[obj_key]))
            gender1 = self.gender(name)

            act = self.dictionary.to_obj_schema[coin_verb][0]
            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
                cased_obj = self.case_to_object(name, {coin_case[0]})
                to = coin_case[1] + cased_obj
            else:
                cased_obj = self.case_to_object(name, {'accs'})
                to = cased_obj

            try:
                text = ' '.join([inf, verb_inf, to])
            except TypeError:
                text = ' '.join([verb, to])

            rdf = self.move_to_object(n=n, act=act, obj1=obj_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                obj.append([text, pattern, 5, *vector, 'generator'])
            else:
                obj = {
                    'text': text,
                    'object': name,
                    'cased': cased_obj,
                    'verb_num': coin_verb,
                }

        return obj

    @df_dec
    def gen_nearest(self, patience, pattern, save, n=0):
        """
        Генератор команд типа "двигайся/искать/обгонять/исследовать ближайший дом"
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        nearest = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            # coin_verb = random.randint(0, 4)
            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))

            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            near = random.choice(self.dictionary.nearest)
            obj_key = random.choice(list(self.dictionary.objects.keys()))
            name = random.choice(list(self.dictionary.objects[obj_key]))
            gender = self.gender(name)
            animacy = self.animacy(name)

            act = self.dictionary.to_obj_schema[coin_verb][0]
            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к'), ('gent', 'до')])
                near = self.case_to_object(near, {coin_case[0], gender})
                cased_obj = self.case_to_object(name, {coin_case[0]})
                to = ' '.join([coin_case[1], near, cased_obj])
            else:
                if gender == 'masc' and len(name.split(' ')) == 1 and animacy =='inan':
                    near = near
                else:
                    near = self.case_to_object(near, {'accs', gender})
                cased_obj = self.case_to_object(name, {'accs'})
                to = ' '.join([near, cased_obj])

            try:
                text = ' '.join([inf, verb_inf, to])
            except TypeError:
                text = ' '.join([verb, to])

            rdf = self.move_to_nearest_object(n=n, act=act, obj1=obj_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                nearest.append([text, pattern, 6, *vector, 'generator'])
            else:
                nearest = {
                    'text': text,
                    'object': name,
                    'cased': cased_obj,
                    'verb_num': coin_verb,
                }

        return nearest

    @df_dec
    def gen_relation1(self, patience, pattern, save, n=0):
        """
        Генератор команд типа "двигайся/искать/обгонять/исследовать дом около дерева"
        Args:
            patience: число генерируемых событий
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        relation1 = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            # coin_verb = random.randint(0, 4)
            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))

            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            objs = list(self.dictionary.objects.keys())
            obj1_key = random.choice(objs)
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy1 = self.animacy(obj1)

            rels = random.choice(list(self.dictionary.relation.keys()))
            rel_case = random.choice(list(self.dictionary.relation[rels].keys()))
            rel1 = random.choice(self.dictionary.relation[rels][rel_case])

            objs.remove(obj1_key)
            obj2_key = random.choice(objs)
            obj2 = random.choice(self.dictionary.objects[obj2_key])
            obj2 = self.case_to_object(obj2, {rel_case})

            act = self.dictionary.to_obj_schema[coin_verb][0]

            that = random.choice(self.dictionary.that)
            participle = random.choice(self.dictionary.participle)

            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
                case = coin_case[0]
                cased_obj1 = self.case_to_object(obj1, {case})
                o1 = coin_case[1] + cased_obj1
            else:
                case = 'accs'
                cased_obj1 = self.case_to_object(obj1, {case})
                o1 = cased_obj1

            if that:
                try:
                    that = self.case_to_object(that, {gender1})
                except AttributeError:
                    pass
                that = ' '.join([',', that])
                if participle:
                    that_to_verb = self.case_to_object(participle, {'VERB', '3per'})
                else:
                    that_to_verb = ''
                to = ' '.join([that, that_to_verb]).strip()
            else:
                if participle:
                    if gender1 == 'masc' and animacy1 == 'inan' and case == 'accs':
                        to = ' '.join([',', participle])
                    else:
                        to = ' '.join([',', self.case_to_object(participle, {case, gender1})])
                else:
                    to = ''

            try:
                text = ' '.join([inf, verb_inf, o1]) + ' '.join([to, rel1, obj2])
            except TypeError:
                text = ' '.join([verb, o1]) + ' '.join([to, rel1, obj2])

            rdf = self.move_to_object_relation1(n=n, act=act, obj1=obj1_key, rel1=rels, obj2=obj2_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                relation1.append([text, pattern, 7, *vector, 'generator'])
            else:
                relation1 = {
                    'text': text,
                    'object': obj1,
                    'cased': cased_obj1,
                    'verb_num': coin_verb,
                }

        return relation1

    @df_dec
    def gen_relation2(self, patience, pattern, save, n=0):
        """
        Генератор команд с двумя отношениями
        Args:
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        relation2 = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            # coin_verb = random.randint(0, 4)
            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))

            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            objs = list(self.dictionary.objects.keys())
            obj1_key = random.choice(objs)
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy1 = self.animacy(obj1)

            rel1_key = random.choice(list(self.dictionary.relation.keys()))
            rel1_case = random.choice(list(self.dictionary.relation[rel1_key].keys()))
            rel1 = random.choice(self.dictionary.relation[rel1_key][rel1_case])

            objs.remove(obj1_key)
            obj2_key = random.choice(objs)
            obj2 = random.choice(self.dictionary.objects[obj2_key])
            gender2 = self.gender(obj2)
            animacy2 = self.animacy(obj2)
            obj2 = self.case_to_object(obj2, {rel1_case})

            rel2_key = random.choice(list(self.dictionary.relation.keys()))
            rel2_case = random.choice(list(self.dictionary.relation[rel2_key].keys()))
            rel2 = random.choice(self.dictionary.relation[rel2_key][rel2_case])

            objs.remove(obj2_key)
            obj3_key = random.choice(objs)
            obj3 = random.choice(self.dictionary.objects[obj3_key])
            obj3 = self.case_to_object(obj3, {rel2_case})

            act = self.dictionary.to_obj_schema[coin_verb][0]

            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
                case = coin_case[0]
                cased_obj1 = self.case_to_object(obj1, {case})
                o1 = coin_case[1] + cased_obj1
            else:
                case = 'accs'
                cased_obj1 = self.case_to_object(obj1, {case})
                o1 = cased_obj1

            that1 = random.choice(self.dictionary.that)
            participle1 = random.choice(self.dictionary.participle)

            if that1:
                try:
                    that1 = self.case_to_object(that1, {gender1})
                except AttributeError:
                    pass
                that1 = ' '.join([',', that1])
                if participle1:
                    that_to_verb = self.case_to_object(participle1, {'VERB', '3per'})
                else:
                    that_to_verb = ''
                to1 = ' '.join([that1, that_to_verb]).strip()
            else:
                if participle1:
                    if gender1 == 'masc' and animacy1 == 'inan' and case == 'accs':
                        to1 = ' '.join([',', participle1])
                    else:
                        to1 = ' '.join([',', self.case_to_object(participle1, {case, gender1})])
                else:
                    to1 = ''

            that2 = random.choice(self.dictionary.that)
            participle2 = random.choice(self.dictionary.participle)

            if that2:
                try:
                    that2 = self.case_to_object(that2, {gender2})
                except AttributeError:
                    pass
                that2 = ' '.join([',', that2])
                if participle2:
                    that_to_verb = self.case_to_object(participle2, {'VERB', '3per'})
                else:
                    that_to_verb = ''
                to2 = ' '.join([that2, that_to_verb]).strip()
            else:
                if participle2:
                    if gender2 == 'masc' and animacy2 == 'inan' and case == 'accs':
                        to2 = ' '.join([',', participle2])
                    else:
                        to2 = ' '.join([',', self.case_to_object(participle2, {case, gender2})])
                else:
                    to2 = ''

            try:
                text = ' '.join([inf, verb_inf, o1]) + ' '.join([to1, rel1, obj2]) + ' '.join([to2, rel2, obj3])
            except TypeError:
                text = ' '.join([verb, o1]) + ' '.join(([to1, rel1, obj2])) + ' '.join([to2, rel2, obj3])

            rdf = self.move_to_object_relation2(n=n, act=act, obj1=obj1_key, rel1=rel1_key, obj2=obj2_key, rel2=rel2_key, obj3=obj3_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                relation2.append([text, pattern, 8, *vector, 'generator'])
            else:
                relation2 = {
                    'text': text,
                    'object': obj1,
                    'cased': cased_obj1,
                    'verb_num': coin_verb,
                }

        return relation2

    @df_dec
    def gen_circle(self, patience, pattern, save, n=0):
        """
        Генератор команд патрулирвания по кругу
        Args:
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        circle = []

        for _ in range(int(patience)):
            patrol = random.choice(self.dictionary.patrol)
            circ = random.choice(self.dictionary.circle)
            radius = random.choice(self.dictionary.radius)

            meter_key = random.choice(list(self.voc.meters.keys()))
            num = random.choice(self.voc.meters[meter_key])
            name = random.choice(self.voc.measure['meters'])
            name = self.agree_with_number(name, num)

            if radius:
                text = ' '.join([patrol, circ, radius, str(num)]) + name
            else:
                text = ' '.join([patrol, circ, str(num)]) + name

            rdf = self.patrol_circle(n=n, num=str(meter_key))
            vector = self.rdf_to_nn(rdf)

            if save:
                circle.append([text, pattern, 9, *vector, 'generator'])
            else:
                circle = ([text, pattern, 9, *vector, 'generator'], '')

        return circle

    @df_dec
    def gen_self(self, patience, pattern, save, n=0):
        """
        Генератор комад движения/поиска/объезда/осмотра относительно робота
        Args:
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        selfr = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))

            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            obj1_key = random.choice(list(self.dictionary.objects.keys()))
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)

            act = self.dictionary.to_obj_schema[coin_verb][0]
            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
                cased_obj = self.case_to_object(obj1, {coin_case[0]})
                to = coin_case[1] + cased_obj
            else:
                cased_obj = self.case_to_object(obj1, {'accs'})
                to = cased_obj

            self_key = random.choice(list(self.dictionary.robot_rel.keys()))
            self_case = random.choice(list(self.dictionary.robot_rel[self_key].keys()))
            self_rel = random.choice(self.dictionary.robot_rel[self_key][self_case])

            me = random.choice(self.dictionary.robot_name)

            if me:
                if self_rel == 'справа' or self_rel == 'слева':
                    self_rel = ' '.join([self_rel, 'от'])
                else:
                    self_rel = self_rel

                me = self.case_to_object(me, {self_case})
            else:
                if self_case == 'ablt':
                    me = random.choice(['тобой', 'собой'])

            try:
                text = ' '.join([inf, verb_inf, to, self_rel, me])
            except TypeError:
                text = ' '.join([verb, to, self_rel, me])

            rdf = self.move_selfrelation_object(n=n, act=act, obj1=obj1_key, selfrel=self_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                selfr.append([text, pattern, 10, *vector, 'generator'])
            else:
                selfr = {
                    'text': text,
                    'object': obj1,
                    'cased': cased_obj,
                    'verb_num': coin_verb,
                }

        return selfr

    @df_dec
    def gen_gaze(self, patience, pattern, save, n=0):
        """
        Генератор комад движения/поиска/объезда/осмотра относительно робота по направлению взгляда
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        gaze = []
        p = math.ceil(patience / 3)

        for _ in range(p):
            """
            иди туда, иди в эту сторону...
            """
            coin_inf = random.randint(0, 1)

            verb = random.choice(self.dictionary.move)

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            focus = random.choice(self.dictionary.focus)

            try:
                text = ' '.join([inf, verb_inf, focus])
            except TypeError:
                text = ' '.join([verb, focus])

            rdf = self.move_gaze_focus_on(n=n)
            vector = self.rdf_to_nn(rdf)

            if save:
                gaze.append([text, pattern, 11, *vector, 'generator'])

        for _ in range(p):
            """
            иди к этому объекту...
            """
            coin_inf = random.randint(0, 1)

            coin_verb = random.choice([0, 2, 3, 4]) # 0:move_to, 2:go_around, 3:monitor, 4:rotate_to
            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            obj1_key = random.choice(list(self.dictionary.objects.keys()))
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy = self.animacy(obj1)

            focus = random.choice(self.dictionary.focus_obj)

            act = self.dictionary.to_obj_schema[coin_verb][0]
            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к'), ('gent', 'до')])
                cased_obj = self.case_to_object(obj1, {coin_case[0]})
                to = ' '.join([coin_case[1], self.case_to_object(focus, {coin_case[0], gender1}), cased_obj])
            else:
                if animacy == 'anim':
                    focus_case = 'gent'
                elif gender1 == 'masc':
                    focus_case = 'nomn'
                else:
                    focus_case = 'accs'
                case = 'accs'
                cased_obj = self.case_to_object(obj1, {case})
                to = ' '.join([self.case_to_object(focus, {focus_case, gender1}), cased_obj])

            try:
                text = ' '.join([inf, verb_inf, to])
            except TypeError:
                text = ' '.join([verb, to])

            rdf = self.move_gaze_focus_on(n=n, act=act, obj1=obj1_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                gaze.append([text, pattern, 11, *vector, 'generator'])
            else:
                gaze.append({
                    'text': text,
                    'object': obj1,
                    'cased': cased_obj,
                    'verb_num': coin_verb,
                })

        for _ in range(p):
            """
            иди в эту сторону, к дому...
            """
            coin_inf = random.randint(0, 1)

            coin_verb = random.choice([0, 2, 3, 4]) # 0:move_to, 2:go_around, 3:monitor, 4:rotate_to
            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            focus = random.choice(self.dictionary.focus)

            obj1_key = random.choice(list(self.dictionary.objects.keys()))
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)

            coin_case = random.choice([('datv', 'к'), ('gent', 'до')])
            cased_obj = self.case_to_object(obj1, {coin_case[0]})
            to = ' '.join([',', coin_case[1], cased_obj])

            try:
                text = ' '.join([inf, verb_inf, focus]) + ' '.join([to])
            except TypeError:
                text = ' '.join([verb, focus]) + ' '.join([to])

            rdf = self.move_gaze_focus_on(n=n, act='move_to', obj1=obj1_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                gaze.append([text, pattern, 11, *vector, 'generator'])
            else:
                gaze.append({
                    'text': text,
                    'object': obj1,
                    'cased': cased_obj,
                    'verb_num': coin_verb,
                })

        if not save:
            gaze = (random.choice(gaze))

        return gaze

    @df_dec
    def gen_new_relation1(self, patience, pattern, save, n=0):
        """
        Генератор комад типа "За берёзой находится упавшее дерево, к которому надо подойти"
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """

        new_relation1 = []

        for _ in range(int(patience)):
            rel1_key = random.choice(list(self.dictionary.relation.keys()))
            rel1_case = random.choice(list(self.dictionary.relation[rel1_key].keys()))
            rel1 = random.choice(self.dictionary.relation[rel1_key][rel1_case])

            objs = list(self.dictionary.objects.keys())
            obj2_key = random.choice(objs)
            obj2 = random.choice(self.dictionary.objects[obj2_key])
            obj2 = self.case_to_object(obj2, {rel1_case})

            participle = random.choice(self.dictionary.participle)
            if participle:
                participle = self.case_to_object(participle, {'VERB', '3per'})
            else:
                participle = ''

            objs.remove(obj2_key)
            obj1_key = random.choice(objs)
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy1 = self.animacy(obj1)

            coin_verb = random.choice(list(self.dictionary.to_obj_schema.keys()))
            verb = random.choice(self.dictionary.to_obj_schema[coin_verb][1])
            act = self.dictionary.to_obj_schema[coin_verb][0]

            if act == 'move_to' or act == 'rotate_to':
                coin_case = random.choice([('datv', 'к'), ('gent', 'до')])
                to = ' '.join([',', coin_case[1], self.case_to_object('который', {coin_case[0], gender1})])
            else:
                if animacy1 == 'anim' and gender1 == 'masc':
                    case = 'gent'
                else:
                    case = 'accs'
                to = ' '.join([',', self.case_to_object('который', {case, gender1})])

            need = random.choice(self.dictionary.needs)

            verb_inf = self.infinitive(verb)

            if not verb_inf:
                v = verb.split(' ')
                if len(v) == 1:
                    verb_inf = self.morph.parse(v[0])[0].normal_form
                else:
                    vinf = self.morph.parse(v[0])[0].normal_form
                    verb_inf = ' '.join([vinf, *v[1:]])

            if participle:
                text = ' '.join([rel1, obj2, participle, obj1]) + ' '.join([to, need, verb_inf])
            else:
                text = ' '.join([rel1, obj2, obj1]) + ' '.join([to, need, verb_inf])

            rdf = self.move_to_object_relation1(n=n, act=act, obj1=obj1_key, rel1=rel1_key, obj2=obj2_key)
            vector = self.rdf_to_nn(rdf)

            if save:
                new_relation1.append([text, 'relation1', 7, *vector, 'generator'])
            else:
                new_relation1 = {
                    'text': text,
                    'object': obj1,
                    'cased': obj1,
                    'verb_num': coin_verb,
                }

        return new_relation1

    @df_dec
    def gen_new_relation2(self, patience, pattern, save, n=0):
        """
        TODO: Генератор комад типа "За берёзой рядом с домом находится упавшее дерево, к которому надо подойти"
            patience: количество переборов
            pattern: кодовое имя шаблона

        Returns:
            вложенный список сгенерированных команд
        """
        pass

    @df_dec
    def gen_patrol_on_route(self, patience, pattern, save, n=0):
        """

        """
        patrol_route = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)
            verb = random.choice(self.dictionary.patrol)
            route = random.choice(self.dictionary.route)
            coin_place = random.randint(0, 1)

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            prep = 'по'

            route = self.case_to_object(route, {'datv'})

            try:
                if coin_place == 0:
                    # TODO:
                    nums = {1: ['1', 'первому'], 2: ['2', 'второму']}
                    num_key = random.choice(list(nums.keys()))
                    num = random.choice(nums[num_key])
                    try:
                        gender = self.gender(route)
                        num = self.morph.parse(num)[0].inflect({gender}).word
                    except AttributeError:
                        pass
                    text = ' '.join([inf, verb_inf, prep, num, route])
                else:
                    nums = {1: ['1','номер 1'], 2: ['2', 'номер 2']}
                    num_key = random.choice(list(nums.keys()))
                    num = random.choice(nums[num_key])

                    text = ' '.join([inf, verb_inf, prep, route, num])
            except TypeError:
                if coin_place == 0:
                    # TODO:
                    nums = {1: ['1', 'первому'], 2: ['2', 'второму']}
                    num_key = random.choice(list(nums.keys()))
                    num = random.choice(nums[num_key])
                    try:
                        gender = self.gender(route)
                        num = self.morph.parse(num)[0].inflect({gender}).word
                    except AttributeError:
                        pass
                    text = ' '.join([verb, prep, num, route])
                else:
                    nums = {1: ['1','номер 1'], 2: ['2', 'номер 2']}
                    num_key = random.choice(list(nums.keys()))
                    num = random.choice(nums[num_key])

                    text = ' '.join([verb, prep, route, num])

            rdf = self.patrol_on_route(route=num_key)
            # TODO:
            vector = self.duplicate.rdf_to_vector(rdf)[0]

            if save:
                patrol_route.append([text, pattern, 12, *vector, 'generator'])
            else:
                patrol_route = ([text, pattern, 12, *vector, 'generator'], '')

        return patrol_route


if __name__ == '__main__':
    gen = ExtGenerator()

    data = gen.gen_patrol_on_route(1e2, 'route', save=True)
    print(data)
