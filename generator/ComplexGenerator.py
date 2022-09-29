import os
import random
import numpy as np
import pandas as pd

from generator.ExtGenerator import ExtGenerator


def complex_dec(method):
    """
    Декортаор, создает таблицу DataFrame из данных комплексного генератора
    Удаляет дублирующиеся строки
    Args:
        method:

    Returns:

    """
    def wrapper(self, patience, pattern):
        data = method(self, patience)

        vec1 = [i + '_1' for i in self.voc.keys]
        vec2 = [i + '_2' for i in self.voc.keys]
        vec3 = [i + '_3' for i in self.voc.keys]

        columns = ['full_text', 'text1', 'text2', 'text3'] + \
                  ['y_name_1', 'y_1'] + vec1 + \
                  ['y_name_2', 'y_2'] + vec2 + \
                  ['y_name_3', 'y_3'] + vec3 + \
                  ['type']

        data = pd.DataFrame(data=data, columns=columns)
        uniq_data = data.drop_duplicates().reset_index(drop=True)
        uniq_data.to_csv(os.path.join(os.path.dirname(__file__), 'ext_data', f'{pattern}.csv'), sep=';', index=False)

        return uniq_data

    return wrapper


class ComplexGenerator(ExtGenerator):

    def __init__(self):
        super(ComplexGenerator, self).__init__()

        self.dist = {'simple': self.gen_simple,
                     'direction': self.gen_direction,
                     'meter': self.gen_meter,
                     'degree': self.gen_degree,
                     'hour': self.gen_hour,
                     'object': self.gen_object,
                     'nearest': self.gen_nearest,
                     'relation1': random.choice([self.gen_relation1,
                                                 self.gen_new_relation1]),
                     'relation2': random.choice([self.gen_relation2,
                                                 # self.gen_new_relation2
                                                ]),
                     'circle': self.gen_circle,
                     'self': self.gen_self,
                     'gaze': self.gen_gaze,
                     }

        self.pnoun = {'masc': 'он',
                      'femn': 'она',
                      'neut': 'оно'}

        self.mock = [None, ] + [0 for _ in range(14)]

    @complex_dec
    def gen_complex1(self, patience):
        """
        Генератор составных команд [команда], [команда]
        Args:
            patience:

        Returns:

        """
        complex1 = []

        for _ in range(int(patience)):

            first = random.choice(list(self.dist.keys()))
            second = random.choice(list(self.dist.keys()))

            cmd1 = self.dist[first](patience=1, pattern=first, save=False, n=0)
            cmd2 = self.dist[second](patience=1, pattern=second, save=False, n=1)

            after = random.choice(self.dictionary.after)

            sep = ' '.join([',', after]).strip()

            try:
                text = cmd1[0][0] + ' '.join([sep, cmd2[0][0]])
            except IndexError:
                continue

            complex1.append([text, *[cmd1[0][0], cmd2[0][0], ''],
                             *cmd1[0][1:-1], *cmd2[0][1:-1], *self.mock, 'generator'])

        return complex1

    @complex_dec
    def gen_complex2(self, patience):
        """
        Генератор составных команд [команда] [команда] [команда]
        Args:
            patience:

        Returns:

        """
        complex2 = []

        for _ in range(int(patience)):

            first = random.choice(list(self.dist.keys()))
            second = random.choice(list(self.dist.keys()))
            third = random.choice(list(self.dist.keys()))

            cmd1 = self.dist[first](patience=1, pattern=first, save=False, n=0)
            cmd2 = self.dist[second](patience=1, pattern=second, save=False, n=1)
            cmd3 = self.dist[third](patience=1, pattern=first, save=False, n=2)

            after1 = random.choice(self.dictionary.after)
            after2 = random.choice(self.dictionary.after)

            sep1 = ' '.join([',', after1]).strip()
            sep2 = ' '.join([',', after2]).strip()

            try:
                text = cmd1[0][0] + ' '.join([sep1, cmd2[0][0]]) + ' '.join([sep2, cmd3[0][0]])
            except IndexError:
                continue

            complex2.append([text, *[cmd1[0][0], cmd2[0][0], cmd3[0][0]],
                             *cmd1[0][1:-1], *cmd2[0][1:-1], *cmd3[0][1:-1], 'generator'])

        return complex2

    @complex_dec
    def gen_find_and_move_v1(self, patience):
        """
        Генератор составных команд, "найди объект. за объектом находится другой объект к которому надо подойти"
        Примеры
        Args:
            patience:

        Returns:

        """
        find_and_move = []

        for _ in range(int(patience)):
            coin_inf = random.randint(0, 1)

            verb = random.choice(self.dictionary.to_obj_schema[1][1]) # find

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            obj2_key = random.choice(list(self.dictionary.objects.keys()))
            obj2 = random.choice(list(self.dictionary.objects[obj2_key]))
            gender2 = self.gender(obj2)

            to = self.case_to_object(obj2, {'accs'})

            try:
                text1 = ' '.join([inf, verb_inf, to])
            except TypeError:
                text1 = ' '.join([verb, to])

            rel1_key = random.choice(list(self.dictionary.relation.keys()))
            rel1_case = random.choice(list(self.dictionary.relation[rel1_key].keys()))
            rel1 = random.choice(self.dictionary.relation[rel1_key][rel1_case])

            pn = self.pnoun[gender2]

            obj2_s = random.choice([self.case_to_object(obj2, {rel1_case}),
                                    self.case_to_object(pn, {'3per', rel1_case, 'Af-p'})])

            participle = random.choice(self.dictionary.participle)
            if participle:
                participle = self.case_to_object(participle, {'VERB', '3per'})
            else:
                participle = ''

            objs = list(self.dictionary.objects.keys())
            objs.remove(obj2_key)
            obj1_key = random.choice(objs)
            obj1 = random.choice(self.dictionary.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy1 = self.animacy(obj1)

            coin_verb = random.choice([0, 2, 3]) # move_to, go_around, monitor
            verb2 = random.choice(self.dictionary.to_obj_schema[coin_verb][1])
            act2 = self.dictionary.to_obj_schema[coin_verb][0]

            if act2 == 'move_to':
                coin_case = random.choice([('datv', 'к'), ('gent', 'до')])
                to = ' '.join([',', coin_case[1], self.case_to_object('который', {coin_case[0], gender1})])
            else:
                if animacy1 == 'anim' and gender1 == 'masc':
                    case = 'gent'
                else:
                    case = 'accs'
                to = ' '.join([',', self.case_to_object('который', {case, gender1})])

            need = random.choice(self.dictionary.needs)

            verb_inf2 = self.infinitive(verb2)

            if not verb_inf2:
                v = verb2.split(' ')
                if len(v) == 1:
                    verb_inf2 = self.morph.parse(v[0])[0].normal_form
                else:
                    vinf = self.morph.parse(v[0])[0].normal_form
                    verb_inf2 = ' '.join([vinf, *v[1:]])

            if participle:
                text2 = ' '.join([rel1, obj2_s, participle, obj1]) + ' '.join([to, need, verb_inf2])
            else:
                text2 = ' '.join([rel1, obj2_s, obj1]) + ' '.join([to, need, verb_inf2])

            text = text1 + ' '.join(['.', text2])

            rdf1 = self.move_to_object(n=0, act='find', obj1=obj2_key)
            vector1 = self.rdf_to_nn(rdf1)
            vector1 = ['object', 5] + vector1

            rdf2 = self.move_to_object_relation1(n=1, act=act2, obj1=obj1_key, rel1=rel1_key, obj2=obj2_key)
            vector2 = self.rdf_to_nn(rdf2)
            vector2 = ['relation1', 7] + vector2

            find_and_move.append([text, *[text1, text2, ''],
                                  *vector1, *vector2, *self.mock, 'generator'])

        return find_and_move

    @complex_dec
    def gen_move_pnoun(self, patience):
        """

        Args:
            patience:

        Returns:

        """
        move_pnoun = []

        for _ in range(int(patience)):

            first = random.choice(['object', 'nearest', 'relation1', 'relation2'])

            cmd1 = self.dist[first](patience=1, pattern=first, save=False, n=0)

            if not cmd1[1]:
                continue

            if cmd1[0][3] == 6: # move_to
                second = random.choice([2, 3]) # go_around, monitor
                pn = self.pnoun[cmd1[1]]
                pn = self.case_to_object(pn, {'3per', 'accs'})

            elif cmd1[0][3] == 7: # find
                second = random.choice([0, 2, 3]) # move_to, go_around, monitor
                pn = self.pnoun[cmd1[1]]

                if second == 0:
                    coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
                    pn = coin_case[1] + self.case_to_object(pn, {'3per', coin_case[0], 'Af-p'})
                else:
                    pn = self.case_to_object(pn, {'3per', 'accs'})
            else:
                continue

            coin_inf = random.randint(0, 1)
            verb = random.choice(self.dictionary.to_obj_schema[second][1])
            act = self.dictionary.to_obj_schema[second][0]

            if coin_inf:
                inf = random.choice(self.dictionary.inf)
                verb_inf = self.infinitive(verb)
            else:
                inf = None
                verb_inf = None

            try:
                text2 = ' '.join([inf, verb_inf, pn])
            except TypeError:
                text2 = ' '.join([verb, pn])

            text = ' '.join([cmd1[0][0], 'и', text2])

            vector1 = cmd1[0][3:-1]
            objs = self.nn_to_obj(vector1)

            rdf2 = self.move_to_object(n=1, act=act, obj1=objs['object1'])
            vector2 = self.rdf_to_nn(rdf2)
            vector2 = ['object', 5] + vector2

            move_pnoun.append([text, *[cmd1[0][0], text2, ''],
                               *cmd1[0][1:-1], *vector2, *self.mock, 'generator'])

        return move_pnoun
