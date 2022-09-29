# coding: utf-8
import re
import pickle
import pandas as pd
import pymorphy2

from random import choice, seed, sample, shuffle

from dataclasses import dataclass, field
from rdflib import Graph, Namespace, Literal


@dataclass
class Voc:
    # Область имен для RDF формата команд
    ki: Namespace = Namespace("ki:")
    KI: Namespace = Namespace("KI:")

    # Контейнер для сгенерированных команд
    generated_list: list = field(default_factory=list)

    # ключи для словаря векторов
    keys: list = field(default_factory=lambda: ['action', 'direction', 'meters', 'degshours', 'object1', 'nearest',
                                                'relation1', 'object2', 'relation2', 'object3', 'self', 'gaze',
                                                'delayed'])

    # # схема для текстового описания
    # text_schema: list

    # схема для кодировки RDF
    rdf_schema: dict = field(default_factory=lambda: {'action': {'patrol': 0, 'stop': 1, 'move_dir': 2, 'rotate_dir': 3,
                                                                 'move_on': 4, 'rotate_on': 5, 'move_to': 6, 'find': 7,
                                                                 'go_around': 8, 'monitor': 9, 'rotate_to': 10,
                                                                 'pause': 11, 'continue': 12, 'analyze': 13},
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
                                                                  'barrier': 12, 'lamp_post': 13, 'car': 14,
                                                                  'circle': 15, 'route': 16},
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
                                                      'gaze': {'': 0, 'by_gaze_line': 1},
                                                      'delayed': {0: 0, 1: 1, 2: 2}})

    # словарь простых команд
    simple_actions: dict = field(default_factory=lambda: {'patrol': ['патрулируй', 'осуществляй обход местности',
                                                                     'обойди окрестности', 'разведывай',
                                                                     'начинай патрулирование', 'неси дозор', 'охраняй',
                                                                     'неси патрульную службу', 'наблюдай за местностью',
                                                                     'следи за обстановкой вокруг', 'иди в дозор',
                                                                     'разведка', 'иди в патруль', 'разведуй местность',
                                                                     'разведывай местность'],
                                                          'stop': ['стоп', 'остановись', 'прекрати движение', 'стой',
                                                                   'стоять', 'не двигаться', 'сделай остановку',
                                                                   'замри', 'не двигайся', 'остановка', 'притормози',
                                                                   'ни шагу далее', 'тормози', 'ни с места',
                                                                   'жди здесь', 'куда пошел', 'приехали', 'припаркуйся',
                                                                   'ваша остановка', 'дай по тормозам', 'погоди',
                                                                   'не надо', 'хватит']})

    # словарь команд движения/поворота в направлении
    actions_dir: dict = field(default_factory=lambda: {'move_dir': ['двигайся ', 'иди ', 'езжай ', 'поезжай ',
                                                                    'направляйся ', 'следуй ', 'беги ', 'топай ',
                                                                    'отправляйся ', 'сдай ', 'шагай ',
                                                                    'начинай движение ', ''],
                                                       'rotate_dir': ['поворачивай ', 'повернись ', 'заворачивай ',
                                                                      'сделай поворот ', 'соверши поворот ',
                                                                      'начинай поворачивать ', '']})

    # словарь команд движения/поворота на заданное расстояние/угол
    move_on: dict = field(default_factory=lambda: {'move_on': ['двигайся ', 'иди ', 'езжай ', 'поезжай ',
                                                               'направляйся ', 'следуй ', 'беги ', 'топай ',
                                                               'отправляйся ', 'сдай ', 'шагай ', 'начинай движение ',
                                                               '']})

    rotate_on: dict = field(default_factory=lambda: {'rotate_on': ['поворачивай ', 'повернись ', 'заворачивай ',
                                                                   'сделай поворот ', 'соверши поворот ',
                                                                   'начинай поворачивать ', '']})

    # словарь команд движения/поиска/объезда/осмотра объекта
    actions_to: dict = field(default_factory=lambda: {'move_to': {'datv': ['двигайся к', 'иди к', 'езжай к',
                                                                           'поезжай к', 'направляйся к', 'следуй к',
                                                                           'беги к', 'отправляйся к', 'топай к',
                                                                           'шагай к', 'тебе нужно подъехать к'],
                                                                  'ablt': ['сократи расстояние между собой и'],
                                                                  'gent': ['сократи дистанцию до']},
                                                      'find': {'accs': ['найди', 'отыщи', 'обнаружь', 'разыщи']},
                                                      'go_around': {'accs': ['объезжай', 'обходи', 'объедь', 'обгоняй',
                                                                             'оставь позади', 'обставь', 'опережай',
                                                                             'опереди', 'обскакивай', 'обскочи']},
                                                      'monitor': {'accs': ['осматривай', 'осмотри', 'обозревай',
                                                                           'обследуй', 'исследуй', 'рассматривай',
                                                                           'рассмотри', 'разглядывай']}})

    # направления для команд move_dir/rotate_dir, move_on/rotate_on
    direction: dict = field(default_factory=lambda: {'dir_forward': ['вперед', 'прямо', 'напрямик', 'прямо по курсу',
                                                                     'напролом', ''],
                                                     'dir_backward': ['назад', 'взад', 'вспять', 'задом'],
                                                     'dir_left': ['налево', 'влево', 'в левую сторону', 'по левую руку'],
                                                     'dir_right': ['направо', 'вправо', 'в правую сторону',
                                                                   'по правую руку', ''],
                                                     'dir_north': ['на север', 'в северную сторону', 'на северный край',
                                                                   'в сторону севера'],
                                                     'dir_south': ['на юг', 'в южную сторону', 'на южный край',
                                                                   'в сторону юга'],
                                                     'dir_east': ['на восток', 'в восточную сторону',
                                                                  'на восточный край', 'в сторону востока'],
                                                     'dir_west': ['на запад', 'в западную сторону', 'на западный край',
                                                                  'в сторону запада']})

    # метры, градусы, часы для команд move_on/rotate_on
    meters: dict = field(default_factory=lambda: {1: [1, 2],
                                                  3: [3, 4],
                                                  5: [5, 6],
                                                  7: [7, 8],
                                                  10: [i for i in range(9, 14)],
                                                  15: [i for i in range(14, 18)],
                                                  20: [i for i in range(18, 23)],
                                                  25: [i for i in range(23, 28)],
                                                  35: [i for i in range(28, 43)],
                                                  50: [i for i in range(43, 65)],
                                                  75: [i for i in range(65, 85)],
                                                  100: [i for i in range(85, 111)]})

    degrees: dict = field(default_factory=lambda: {15: [i for i in range(0, 25)],
                                                   30: [i for i in range(25, 35)],
                                                   45: [i for i in range(35, 50)],
                                                   60: [i for i in range(50, 65)],
                                                   75: [i for i in range(65, 80)],
                                                   90: [i for i in range(80, 95)],
                                                   105: [i for i in range(95, 110)],
                                                   120: [i for i in range(110, 125)],
                                                   135: [i for i in range(125, 140)],
                                                   150: [i for i in range(140, 155)],
                                                   165: [i for i in range(155, 170)],
                                                   180: [i for i in range(170, 185)],
                                                   195: [i for i in range(185, 200)],
                                                   210: [i for i in range(200, 215)],
                                                   225: [i for i in range(215, 230)],
                                                   240: [i for i in range(230, 245)],
                                                   255: [i for i in range(245, 260)],
                                                   270: [i for i in range(260, 275)],
                                                   285: [i for i in range(275, 290)],
                                                   300: [i for i in range(290, 305)],
                                                   315: [i for i in range(305, 320)],
                                                   330: [i for i in range(320, 335)],
                                                   345: [i for i in range(335, 350)],
                                                   360: [i for i in range(350, 361)]})

    hours: dict = field(default_factory=lambda: {15: ['0:30', 'полчаса', '030', '0 с половиной часов'],
                                                 30: ['1:00', 'один час', 'час', 'час 0 минут', 'один час 0 минут',
                                                      '100'],
                                                 45: ['1:30', 'полтора часа', '1 час 30 минут', 'один с половиной час'],
                                                 60: ['2:00', '2 часа 0 минут', '200'],
                                                 75: ['2:30', 'два с половиной часа'],
                                                 90: ['3:00', '3 часа 0 минут', '300'],
                                                 105: ['3:30', 'три с половиной часа', '3,5 часа'],
                                                 120: ['4:00', '4 часа 0 минут', '400'],
                                                 135: ['4:30', 'четыре с половиной часа'],
                                                 150: ['5:00', '500'],
                                                 165: ['5:30', 'пять с половиной часов', '5,5 часов'],
                                                 180: ['6:00'],
                                                 195: ['6:30', 'шесть с половиной часов', '6,5 часов'],
                                                 210: ['7:00', '700'],
                                                 225: ['7:30', '7 с половиной часов', '7,5 часов'],
                                                 240: ['8:00'],
                                                 255: ['8:30', '8 с половиной часов', '8,5 часов'],
                                                 270: ['9:00', '900'],
                                                 285: ['9:30', 'девять с половиной часов'],
                                                 300: ['10:00'],
                                                 315: ['10:30', '10 с половиной часов', '10,5 часов'],
                                                 330: ['11:00', '11:00 0 минут'],
                                                 345: ['11:30', '11 с половиной часов'],
                                                 360: ['12:00', '1200', '12:00 0 минут']})

    hours_yandex: dict = field(default_factory=lambda: {15: ['0:30', 'полчаса', 'пол 1', 'полпервого', '0,5 часов'],
                                                        30: ['1:00', '1:0', '1 час', 'час', '1 0 0'],
                                                        45: ['1:30', 'полтора часа', '1,5 час', 'пол 2'],
                                                        60: ['2:00', '2:0', '2 часа', '2 0 0'],
                                                        75: ['2:30', '2 30', '2,5 часа', 'пол 3'],
                                                        90: ['3:00', '3:0', '3 часа', '3 0 0'],
                                                        105: ['3:30', '3,5 часа', '3 30', 'пол 4'],
                                                        120: ['4:00', '4:0', '4 часа', '4 0 0'],
                                                        135: ['4:30', '4,5 часа', '4 30', 'пол 5'],
                                                        150: ['5:00', '5:0', '5 часов', '5 0 0'],
                                                        165: ['5:30', '5,5 часов', '5 30', 'пол 6'],
                                                        180: ['6:00', '6:0', '6 часов', '6 0 0'],
                                                        195: ['6:30', '6,5 часов', '6 30', 'пол 7'],
                                                        210: ['7:00', '7:0', '7 часов', '7 0 0'],
                                                        225: ['7:30', '7,5 часов', '7 30', 'пол 8'],
                                                        240: ['8:00', '8:0', '8 часов', '8 0 0'],
                                                        255: ['8:30', '8,5 часов', '8 30', 'пол 9'],
                                                        270: ['9:00', '9:0', '9 часов', '9 0 0'],
                                                        285: ['9:30', '9,5 часов', '9 30', 'пол 10'],
                                                        300: ['10:00', '10:0', '10 часов', '10 0 0'],
                                                        315: ['10:30', '10,5 часов', '10 30', 'пол 11'],
                                                        330: ['11:00', '11:0', '11 часов', '11 0 0'],
                                                        345: ['11:30', '11,5 часов', '11 30', 'пол 12'],
                                                        360: ['12:00', '12:0', '12 часов', '12 0 0']})

    # измерения для метров, градусов, часов
    pretext: list = field(default_factory=lambda: ['на ', ''])

    measure: dict = field(default_factory=lambda: {'meters': [' метр', 'm', 'M', ' м', 'м', 'М'],
                                                   'degrees': [' градус', '\xb0', ' \xb0']})

    # объекты для команд move_to/find/go_around/monitor
    objects: dict = field(default_factory=lambda: {'house': ['дом', 'здание', 'изба', 'строение', 'постройка', 'коттедж',
                                                             'особняк', 'домик'],
                                                   'tree': ['дерево', 'растение', 'дуб', 'берёза', 'сосна', 'ольха',
                                                            'деревце'],
                                                   'broken_tree': ['поваленное дерево', 'спиленное дерево',
                                                                   'срубленное дерево', 'сломанное дерево',
                                                                   'сваленное дерево', 'упавшее дерево'],
                                                   'forest': ['лес', 'роща', 'лесополоса', 'чаща', 'дубрава'],
                                                   'pit': ['яма', 'овраг', 'канава', 'рытвина', 'пропасть', 'провал',
                                                           'впадина'],
                                                   'human': ['человек', 'мужчина', 'женщина', 'ребёнок', 'дама',
                                                             'товарищ'],
                                                   'hill': ['холм', 'гора', 'куча', 'бугор', 'возвышенность', 'горка',
                                                            'пригорок', 'холмик'],
                                                   'fissure': ['трещина', 'расщелина', 'разлом', 'разрыв'],
                                                   'man_lay': ['лежащий человек', 'пьяный человек', 'упавший человек',
                                                               'свалившийся человек'],
                                                   'rock': ['камень', 'булыжник', 'камушек', 'булыга'],
                                                   'butte': ['валун', 'останец'],
                                                   'barrier': ['барьер', 'препятствие', 'загородка', 'ограждение',
                                                               'преграда'],
                                                   'lamp_post': ['фонарь', 'светильник', 'лампа', 'свет', 'столб'],
                                                   'car': ['автомобиль', 'машина', 'авто', 'тачка', 'железный конь']})

    # ближайшие объекты
    nearest: dict = field(default_factory=lambda: {'nearest': ['ближайший', 'ближний', 'близкий', 'близлежащий']})

    # отношения между объектами
    relation: dict = field(default_factory=lambda: {'near': {'gent': ['около', 'неподалеку от'],
                                                             'ablt': ['рядом с']},
                                                    'behind_of': {'gent': ['позади', 'сзади от'],
                                                                  'ablt': ['за']},
                                                    'in_front_of': {'gent': ['спереди от'],
                                                                    'ablt': ['перед']},
                                                    'to_left_from': {'gent': ['слева от', 'левее']},
                                                    'to_right_from': {'gent': ['справа от', 'правее']}})

    # сложноподчиненные предлоги
    that: list = field(default_factory=lambda: ['который', ''])
    participle: list = field(default_factory=lambda: ['находящийся', 'располагающийся', '', ''])
    verbs: list = field(default_factory=lambda: ['находится', 'располагается', '', ''])

    # круговая траектория
    circle: list = field(default_factory=lambda: ['по кругу', 'по окружности', 'по кольцу', 'по касательной к кругу',
                                                  'по круговой траектории', 'по касательной', 'по орбите'])

    radius: list = field(default_factory=lambda: ['', 'радиуса ', 'радиусом ', 'размером '])

    # отношения с роботом
    self_relation: dict = field(default_factory=lambda: {'behind_of': {'gent': ['позади', 'сзади'],
                                                                       'ablt': ['за']},
                                                         'in_front_of': {'gent': ['спереди', 'впереди'],
                                                                         'ablt': ['перед']},
                                                         'to_left_from': {'gent': ['слева', 'левее']},
                                                         'to_right_from': {'gent': ['справа', 'правее']}})

    self_names: list = field(default_factory=lambda: ['тебя', 'себя', ''])

    # направление взгляда
    focus: list = field(default_factory=lambda: ['туда', 'сюда', 'в ту сторону', 'в том направлении', 'в эту сторону',
                                                 'в это место', 'в этом направлении', 'куда смотрю'])

    focus_on_object: list = field(default_factory=lambda: ['к этому ', 'к тому ', 'к данному ', 'к наблюдаемому ',
                                                           'к наблюдаемому мной '])


class Generator:
    """
    Создание датасета вида: TEXT, RDF, VECTOR
    """
    def __init__(self, use_generated_dict=False):
        self.voc = Voc()
        self.morph = pymorphy2.MorphAnalyzer()
        self.patterns()

        self.use_generated_dict = use_generated_dict

        values = [0 for _ in range(len(self.voc.keys))]
        self.result = dict(zip(self.voc.keys, values))

        self.generated = {'x': [],
                          'y_name': [],
                          'y': []}

    def patterns(self):
        """
        Шаблоны текстовых команд
        Returns:

        """
        self.text_pattern_simple = '{}'
        self.text_pattern_move_rotate = '{}{}'
        self.text_pattern_move_rotate_num = '{}{} {}{}'
        self.text_pattern_move_to_object = '{} {}'
        self.text_pattern_move_to_nearest_object = '{} {} {}'
        self.text_pattern_move_to_object_relation1 = '{} {}{} {}'
        self.text_pattern_move_to_object_relation2 = '{} {}{} {}{} {}'
        self.text_pattern_patrol_circle = '{} {} {}{}{}'
        self.text_pattern_move_to_self_object = '{} {} {} {}'
        self.text_pattern_move_gaze_focus_on = '{}{}{}'

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.direction))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.value, self.voc.ki[direct]))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki.move_on))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.direction))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.value, self.voc.ki[direct]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.numeric_value, Literal(num)))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki.rotate_on))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.direction))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.value, self.voc.ki[direct]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.numeric_value, Literal(num)))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))

        return g.serialize(format='nt')

    def move_to_nearest_object(self, n=0, act='move_to', obj1='OBJECT1'):
        """
        Шаблон для команды движения к ближайшему объекту
        Пример: двигайся к к ближайшему дому
        Args:
            n: порядок действия, для составных команд
            obj1: объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.nearest_from_type, self.voc.ki[obj1]))

        return g.serialize(format='nt')

    def move_to_object_relation1(self, n=0, act='move_to', obj1='OBJECT1', rel1='RELATION1', obj2='OBJECT2'):
        """
        Шаблон для команды движения с одним отношением
        Пример: двигайся к дому около дерева
        Args:
            n: порядок действия, для составных команд
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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki[rel1], self.voc.KI[cmd_obj2]))
        g.add((self.voc.KI[cmd_obj2], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj2], self.voc.ki.type, self.voc.ki[obj2]))

        return g.serialize(format='nt')

    def move_to_object_relation2(self, n=0, act='move_to', obj1='OBJECT1', rel1='RELATION1', obj2='OBJECT2', rel2='RELATION2', obj3='OBJECT3'):
        """
        Шаблон для команды движения с двумя отношениями
        Пример: двигайся к дому около дерева рядом с камнем
        Args:
            n: порядок действия, для составных команд
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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki[rel1], self.voc.KI[cmd_obj2]))
        g.add((self.voc.KI[cmd_obj2], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj2], self.voc.ki.type, self.voc.ki[obj2]))
        g.add((self.voc.KI[cmd_obj2], self.voc.ki[rel2], self.voc.KI[cmd_obj3]))
        g.add((self.voc.KI[cmd_obj3], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj3], self.voc.ki.type, self.voc.ki[obj3]))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki.patrol))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.circle))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.numeric_value, Literal(num)))

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
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki[selfrel], self.voc.ki.me))

        return g.serialize(format='nt')

    def move_gaze_focus_on(self, n=0, act='move_to', obj1=None):
        """
        Шаблон для команды движения по направлению взгляда
        Args:
            n: порядок действия для составных команд
            obj1: целевой объект мира (house, human...)

        Returns:
            RDF
        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n-1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki[act]))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.object))
        g.add((self.voc.ki.me, self.voc.ki.has_gaze_focus_on, self.voc.KI[cmd_obj1]))

        if obj1:
            g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki[obj1]))

        return g.serialize(format='nt')

    def patrol_on_route(self, route, n=0):
        """

        """
        cmd_num = 'F' + str(n)
        cmd_obj1 = cmd_num + '_V0'
        g = Graph()
        if n == 0:
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.action))
        else:
            prev_num = 'F' + str(n - 1)
            g.add((self.voc.KI[cmd_num], self.voc.ki.after, self.voc.KI[prev_num]))
            g.add((self.voc.KI[cmd_num], self.voc.ki.type, self.voc.ki.delayed_action))
        g.add((self.voc.KI[cmd_num], self.voc.ki.actor, self.voc.ki.me))
        g.add((self.voc.KI[cmd_num], self.voc.ki.action_type, self.voc.ki.patrol))
        g.add((self.voc.KI[cmd_num], self.voc.ki.patient, self.voc.KI[cmd_obj1]))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.type, self.voc.ki.route))
        g.add((self.voc.KI[cmd_obj1], self.voc.ki.numeric_value, Literal(route)))

        return g.serialize(format='nt')

    def rdf_to_nn(self, rdf):
        """
        Кодирует RDF формат в векторное представление
        Args:
            rdf: Строка или байты

        Returns:
            Вектор признаков
        """
        result = self.result.copy()

        if type(rdf) != str:
            dec = bytes.decode(rdf)
        else:
            dec = rdf

        instances = dec.strip().split('\n')

        for triple in sorted(instances):
            reg = re.findall(r'\w+', triple)

            if 'action_type' in reg:
                action = reg[-1]
                result['action'] = self.voc.rdf_schema['action'][action]

            elif 'value' in reg:
                direction = reg[-1]
                result['direction'] = self.voc.rdf_schema['direction'][direction]

            elif 'numeric_value' in reg:
                if result['action'] == 4:  # move_on
                    meters = reg[-1]
                    result['meters'] = self.voc.rdf_schema['meters'][meters]
                elif result['action'] == 5:    # rotate_on
                    degshours = reg[-1]
                    result['degshours'] = self.voc.rdf_schema['degshours'][degshours]
                elif result['action'] == 0:     # patrol
                    radius = reg[-1]
                    result['meters'] = self.voc.rdf_schema['meters'][radius]

            elif ('V0' in reg[1]) and \
                 ('type' in reg) and \
                 ('direction' not in reg) and \
                 ('object' not in reg):
                object1 = reg[-1]
                result['object1'] = self.voc.rdf_schema['object1'][object1]

            elif 'nearest_from_type' in reg:
                result['nearest'] = 1

            elif ('V0' in reg[1]) and \
                 ('V1' in reg[-1]):
                relation1 = reg[3]
                result['relation1'] = self.voc.rdf_schema['relation1'][relation1]

            elif ('V1' in reg[1]) and \
                 ('type' in reg) and \
                 ('direction' not in reg) and\
                 ('object' not in reg):
                object2 = reg[-1]
                result['object2'] = self.voc.rdf_schema['object2'][object2]

            elif ('V1' in reg[1]) and\
                 ('V2' in reg[-1]):
                relation2 = reg[3]
                result['relation2'] = self.voc.rdf_schema['relation2'][relation2]

            elif ('V2' in reg[1]) and \
                 ('type' in reg) and \
                 ('direction' not in reg) and \
                 ('object' not in reg):
                object3 = reg[-1]
                result['object3'] = self.voc.rdf_schema['object3'][object3]

            elif ('V0' in reg[1]) and \
                 ('me' in reg):
                self_relation = reg[3]
                result['self'] = self.voc.rdf_schema['self'][self_relation]

            elif 'by_gaze_line' in reg:
                gaze = reg[3]
                result['gaze'] = self.voc.rdf_schema['gaze'][gaze]

            elif 'delayed_action' in reg:
                delayed = int(reg[1][-1])
                result['delayed'] = self.voc.rdf_schema['delayed'][delayed]

        return list(result.values())

    def rdf_to_nn_old(self, rdf):
        """
        Перевод старой версии rdf в новое векторное представление
        Args:
            rdf:

        Returns:
            Вектор признаков
        """
        result = self.result.copy()

        if type(rdf) != str:
            dec = bytes.decode(rdf)
        else:
            dec = rdf

        instances = dec.strip().split('\n')

        for triple in sorted(instances):
            reg = re.findall(r'\w+', triple)

            if 'action_type' in reg:
                action = reg[-1]
                result['action'] = self.voc.rdf_schema['action'][action]

            elif ('patient' in reg) and \
                 (not 'X' in reg[-1]):
                direction = 'dir_' + reg[-1]
                result['direction'] = self.voc.rdf_schema['direction'][direction]

            elif ('X2' in reg) and \
                 ('type' in reg):
                object1 = reg[-1]
                result['object1'] = self.voc.rdf_schema['object1'][object1]

            elif ('X2' in reg) and \
                 ('X3' in reg):
                relation1 = reg[3]
                result['relation1'] = self.voc.rdf_schema['relation1'][relation1]

            elif ('X3' in reg) and \
                 ('type' in reg):
                object2 = reg[-1]
                result['object2'] = self.voc.rdf_schema['object2'][object2]

            elif ('X3' in reg) and \
                 ('X4' in reg):
                relation2 = reg[3]
                result['relation2'] = self.voc.rdf_schema['relation2'][relation2]

            elif ('X4' in reg) and \
                 ('type' in reg):
                object3 = reg[-1]
                result['object3'] = self.voc.rdf_schema['object3'][object3]

        return list(result.values())

    def nn_to_obj(self, vecn10):

        key_words = []
        for i, val in enumerate(vecn10):
            key_schema = self.voc.keys[i]
            type_of = self.voc.rdf_schema[key_schema]

            key_words.append(self._get_key(type_of, val))

        result = dict(zip(self.voc.keys, key_words))

        return result

    def nn_to_rdf(self, vecn10):
        """
        Расшифровывает векторное представление в RDF формат
        Args:
            vecn10: закодированный RDF
        Returns:
            RDF
        """
        key_words = []
        for i, val in enumerate(vecn10):
            key_schema = self.voc.keys[i]
            type_of = self.voc.rdf_schema[key_schema]

            key_words.append(self._get_key(type_of, val))

        result = dict(zip(self.voc.keys, key_words))

        if (result['action']) and \
           (not result['direction']) and \
           (not result['object1']) and \
           (not result['meters']) and \
           (not result['gaze']):

            if result['delayed']:
                return self.move_simple(n=result['delayed'], act=result['action'])
            else:
                return self.move_simple(act=result['action'])

        elif (result['direction']) and \
             (not result['meters']) and \
             (not result['degshours']):

            if result['delayed']:
                return self.move_direction(n=result['delayed'], act=result['action'], direct=result['direction'])
            else:
                return self.move_direction(act=result['action'], direct=result['direction'])

        elif (result['meters']) and \
             (result['direction']):

            if result['delayed']:
                return self.move_direction_numeric(n=result['delayed'], direct=result['direction'],
                                                   num=result['meters'])
            else:
                return self.move_direction_numeric(direct=result['direction'], num=result['meters'])

        elif result['degshours']:

            if result['delayed']:
                return self.rotate_direction_numeric(n=result['delayed'], direct=result['direction'],
                                                     num=result['degshours'])
            else:
                return self.rotate_direction_numeric(direct=result['direction'], num=result['degshours'])

        elif (result['object1']) and \
             (not result['nearest']) and \
             (not result['object2']) and \
             (not result['self']) and \
             (not result['gaze']):

            if result['delayed']:
                return self.move_to_object(n=result['delayed'], act=result['action'], obj1=result['object1'])
            else:
                return self.move_to_object(act=result['action'], obj1=result['object1'])

        elif result['nearest']:

            if result['delayed']:
                return self.move_to_nearest_object(n=result['delayed'], obj1=result['object1'])
            else:
                return self.move_to_nearest_object(obj1=result['object1'])

        elif (result['object2']) and \
             (not result['object3']):

            if result['delayed']:
                return self.move_to_object_relation1(n=result['delayed'], obj1=result['object1'],
                                                     rel1=result['relation1'], obj2=result['object2'])
            else:
                return self.move_to_object_relation1(obj1=result['object1'], rel1=result['relation1'],
                                                     obj2=result['object2'])

        elif result['object3']:

            if result['delayed']:
                return self.move_to_object_relation2(n=result['delayed'], obj1=result['object1'],
                                                     rel1=result['relation1'], obj2=result['object2'],
                                                     rel2=result['relation2'], obj3=result['object3'])
            else:
                return self.move_to_object_relation2(obj1=result['object1'], rel1=result['relation1'],
                                                     obj2=result['object2'], rel2=result['relation2'],
                                                     obj3=result['object3'])

        elif result['meters']:

            if result['delayed']:
                return self.patrol_circle(n=result['delayed'], num=result['meters'])
            else:
                return self.patrol_circle(num=result['meters'])

        elif result['self']:

            if result['delayed']:
                return self.move_selfrelation_object(n=result['delayed'], act=result['action'],
                                                     obj1=result['object1'], selfrel=result['self'])
            else:
                return self.move_selfrelation_object(act=result['action'], obj1=result['object1'],
                                                     selfrel=result['self'])

        elif result['gaze']:

            if result['delayed']:
                return self.move_gaze_focus_on(n=result['delayed'], obj1=result['object1'])
            else:
                return self.move_gaze_focus_on(obj1=result['object1'])

    def nn_to_text(self, vecn10):
        """
        Расшифровывает векторное представление в текстовое описание команды
        Args:
            vecn10: закодированный RDF

        Returns:
            text
        """
        key_words = []

        for i, val in enumerate(vecn10):
            key_schema = self.voc.keys[i]
            type_of = self.voc.rdf_schema[key_schema]

            key_words.append(self._get_key(type_of, val))

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

    def _generated_update(self, text, mark, label):
        """
        Заполнение словаря генератора
        Args:
            text: сгенерированная текстовая команда
            mark: метка шаблона
            label: номер шаблона

        Returns:

        """
        self.generated['x'].append(text)
        self.generated['y_name'].append(mark)
        self.generated['y'].append(label)

    def gen_simple(self):
        """
        Генератор простых команд
        Номер шаблона - 0
        Returns:

        """
        for k in self.voc.simple_actions.keys():
            for action in self.voc.simple_actions[k]:
                text = self.text_pattern_simple.format(action)
                rdf = self.move_simple(act=k)
                vector = self.rdf_to_nn(rdf)

                if self.use_generated_dict:
                    self._generated_update(text=text, mark='simple', label=0)
                else:
                    self.voc.generated_list.append([text, 'simple', 0, *vector])

    def gen_move_rotate_dir(self):
        """
        Генератор команд на движение/поворот в направлении
        Номер шаблона - 1
        Returns:

        """
        for k_a in self.voc.actions_dir.keys():
            for action in self.voc.actions_dir[k_a]:
                for k_d in self.voc.direction.keys():
                    for direction in self.voc.direction[k_d]:
                        if k_a == 'rotate_dir' and k_d in ['dir_forward', 'dir_backward']:
                            pass
                        else:
                            if action == '' and direction == '':
                                pass
                            else:
                                text = self.text_pattern_move_rotate.format(action, direction)
                                rdf = self.move_direction(act=k_a, direct=k_d)
                                vector = self.rdf_to_nn(rdf)

                                if self.use_generated_dict:
                                    self._generated_update(text=text, mark='direction', label=1)
                                else:
                                    self.voc.generated_list.append([text, 'direction', 1, *vector])

    def gen_move_num(self):
        """
        Генератор команд на движение в направлении на заданное число метров
        Номер шаблона - 2
        Returns:

        """
        for action in self.voc.move_on['move_on']:
            for k_d in self.voc.direction.keys():
                for direction in self.voc.direction[k_d]:
                    for pret in self.voc.pretext:
                        for k_m in self.voc.meters.keys():
                            for num in self.voc.meters[k_m]:
                                for m in self.voc.measure['meters']:
                                    if action == '' and direction == '':
                                        pass
                                    else:
                                        if len(m) > 2:
                                            meter = self.agree_with_number(m, num)
                                        else:
                                            meter = m

                                        text = self.text_pattern_move_rotate_num.format(action, direction, pret+str(num), meter)
                                        rdf = self.move_direction_numeric(direct=k_d, num=str(k_m))
                                        vector = self.rdf_to_nn(rdf)

                                        if self.use_generated_dict:
                                            self._generated_update(text=text, mark='meter', label=2)
                                        else:
                                            self.voc.generated_list.append([text, 'meter', 2, *vector])

    def gen_rotate_deg(self):
        """
        Генератор команд на поворот в направлении на заданное число градусов
        Номер шаблона - 3
        Returns:

        """
        for action in self.voc.rotate_on['rotate_on']:
            for k_d in self.voc.direction.keys():
                for direction in self.voc.direction[k_d]:
                    for pret in self.voc.pretext:
                        if k_d not in ['dir_forward', 'dir_backward']:
                            for k_g in self.voc.degrees.keys():
                                for num in self.voc.degrees[k_g]:
                                    for g in self.voc.measure['degrees']:
                                        if action == '' and direction == '':
                                            pass
                                        else:
                                            g = self.agree_with_number(g, num)
                                            text = self.text_pattern_move_rotate_num.format(action, direction, pret+str(num), g)
                                            rdf = self.rotate_direction_numeric(direct=k_d, num=str(k_g))
                                            vector = self.rdf_to_nn(rdf)

                                            if self.use_generated_dict:
                                                self._generated_update(text=text, mark='degree', label=3)
                                            else:
                                                self.voc.generated_list.append([text, 'degree', 3, *vector])

    def gen_rotate_hours(self):
        """
        Генератор команд на поворот в направлении на заданное число часов
        Номер шаблона - 4
        Returns:

        """
        for action in self.voc.rotate_on['rotate_on']:
            for k_d in self.voc.direction.keys():
                for direction in self.voc.direction[k_d]:
                    for pret in self.voc.pretext:
                        if k_d not in ['dir_forward', 'dir_backward']:
                            for k_h in self.voc.hours.keys():
                                for hour in self.voc.hours[k_h]:
                                    if action == '' and direction == '':
                                        pass
                                    else:
                                        text = self.text_pattern_move_rotate_num.format(action, direction, pret+hour, '')
                                        rdf = self.rotate_direction_numeric(direct=k_d, num=str(k_h))
                                        vector = self.rdf_to_nn(rdf)

                                        if self.use_generated_dict:
                                            self._generated_update(text=text, mark='hour', label=4)
                                        else:
                                            self.voc.generated_list.append([text, 'hour', 4, *vector])

    def gen_move_to_object(self):
        """
        Генератор команд движения/поиска/объезда/осмотра объекта
        Номер шаблона - 5
        Returns:

        """
        for k_a in self.voc.actions_to.keys():
            cases = self.voc.actions_to[k_a]
            for case in cases.keys():
                for action in cases[case]:
                    for k_o in self.voc.objects.keys():
                        for obj in self.voc.objects[k_o]:
                            obj = self.case_to_object(obj, {case})
                            text = self.text_pattern_move_to_object.format(action, obj)
                            rdf = self.move_to_object(act=k_a, obj1=k_o)
                            vector = self.rdf_to_nn(rdf)

                            if self.use_generated_dict:
                                self._generated_update(text=text, mark='object', label=5)
                            else:
                                self.voc.generated_list.append([text, 'object', 5, *vector])

    def gen_move_to_nearest_object(self):
        """
        Генератор команд движения к ближайшему объекту
        Номер шаблона - 6
        Returns:

        """
        cases = self.voc.actions_to['move_to']
        for case in cases.keys():
            for action in cases[case]:
                for n in self.voc.nearest['nearest']:
                    for k_o in self.voc.objects.keys():
                        for obj in self.voc.objects[k_o]:
                            gender = self.gender(obj)
                            animacy = self.animacy(obj)
                            obj = self.case_to_object(obj, {case})
                            if case == 'accs' and gender == 'masc' and len(obj.split(' ')) == 1 and animacy == 'inan':
                                near = n
                            else:
                                near = self.case_to_object(n, {case, gender})
                            text = self.text_pattern_move_to_nearest_object.format(action, near, obj)
                            rdf = self.move_to_nearest_object(obj1=k_o)
                            vector = self.rdf_to_nn(rdf)

                            if self.use_generated_dict:
                                self._generated_update(text=text, mark='nearest', label=6)
                            else:
                                self.voc.generated_list.append([text, 'nearest', 6, *vector])

    def gen_move_to_object_relation1(self, pat=1e4):
        """
        Генератор команд движения к объекту с одним отношением
        Номер шаблона - 7
        Args:
            pat: число примеров

        Returns:

        """
        for _ in range(int(pat)):
            a = self.voc.actions_to['move_to']
            case = choice(list(a.keys()))
            action = choice(a[case])

            objs = list(self.voc.objects.keys())

            obj1_key = choice(objs)
            obj1 = choice(self.voc.objects[obj1_key])
            gender = self.gender(obj1)
            animacy = self.animacy(obj1)
            obj1 = self.case_to_object(obj1, {case})

            rels = choice(list(self.voc.relation.keys()))
            rel_case = choice(list(self.voc.relation[rels].keys()))
            rel1 = ' ' + choice(self.voc.relation[rels][rel_case])

            objs.remove(obj1_key)
            obj2_key = choice(objs)
            obj2 = choice(self.voc.objects[obj2_key])
            obj2 = self.case_to_object(obj2, {rel_case})

            that = choice(self.voc.that)
            participle = choice(self.voc.participle)
            if that:
                that = ', ' + self.case_to_object(that, {gender})
                verb = choice(self.voc.verbs)
                if verb:
                    verb = ' ' + verb
                rel1 = that+verb+rel1
            else:
                if participle:
                    if case == 'accs' and gender == 'masc' and len(obj1.split(' ')) == 1 and animacy == 'inan':
                        participle = ', ' + participle
                    else:
                        participle = ', ' + self.case_to_object(participle, {case, gender})

                    rel1 = participle+rel1

            text = self.text_pattern_move_to_object_relation1.format(action, obj1, rel1, obj2)
            rdf = self.move_to_object_relation1(obj1=obj1_key, rel1=rels, obj2=obj2_key)
            vector = self.rdf_to_nn(rdf)

            if self.use_generated_dict:
                self._generated_update(text=text, mark='relation1', label=7)
            else:
                self.voc.generated_list.append([text, 'relation1', 7, *vector])

    def gen_move_to_object_relation2(self, pat=1e4):
        """
        Генератор команд движения к объекту с двумя отношениями
        Номер шаблона - 8
        Args:
            pat: число примеров

        Returns:

        """
        for _ in range(int(pat)):
            a = self.voc.actions_to['move_to']
            case = choice(list(a.keys()))
            action = choice(a[case])

            objs = list(self.voc.objects.keys())

            obj1_key = choice(objs)
            obj1 = choice(self.voc.objects[obj1_key])
            gender1 = self.gender(obj1)
            animacy1 = self.animacy(obj1)
            obj1 = self.case_to_object(obj1, {case})

            rels1 = choice(list(self.voc.relation.keys()))
            rel_case1 = choice(list(self.voc.relation[rels1].keys()))
            rel1 = ' ' + choice(self.voc.relation[rels1][rel_case1])

            that1 = choice(self.voc.that)
            participle1 = choice(self.voc.participle)
            if that1:
                that1 = ', ' + self.case_to_object(that1, {gender1})
                verb = choice(self.voc.verbs)
                if verb:
                    verb = ' ' + verb
                rel1 = that1+verb+rel1
            else:
                if participle1:
                    if case == 'accs' and gender1 == 'masc' and len(obj1.split(' ')) == 1 and animacy1 == 'inan':
                        participle1 = ', ' + participle1
                    else:
                        participle1 = ', ' + self.case_to_object(participle1, {case, gender1})

                    rel1 = participle1+rel1

            objs.remove(obj1_key)
            obj2_key = choice(objs)
            obj2 = choice(self.voc.objects[obj2_key])
            gender2 = self.gender(obj2)
            obj2 = self.case_to_object(obj2, {rel_case1})

            rels2 = choice(list(self.voc.relation.keys()))
            rel_case2 = choice((list(self.voc.relation[rels2].keys())))
            rel2 = ' ' + choice(self.voc.relation[rels2][rel_case2])

            that2 = choice(self.voc.that)
            participle2 = choice(self.voc.participle)
            if that2:
                that2 = ', ' + self.case_to_object(that2, {gender2})
                verb = choice(self.voc.verbs)
                if verb:
                    verb = ' ' + verb
                rel2 = that2+verb+rel2
            else:
                if participle2:
                    participle2 = ', ' + self.case_to_object(participle2, {rel_case1, gender2})
                    rel2 = participle2 + rel2

            objs.remove(obj2_key)
            obj3_key = choice(objs)
            obj3 = choice(self.voc.objects[obj3_key])
            obj3 = self.case_to_object(obj3, {rel_case2})

            text = self.text_pattern_move_to_object_relation2.format(action, obj1, rel1, obj2, rel2, obj3)
            rdf = self.move_to_object_relation2(obj1=obj1_key, rel1=rels1, obj2=obj2_key, rel2=rels2, obj3=obj3_key)
            vector = self.rdf_to_nn(rdf)

            if self.use_generated_dict:
                self._generated_update(text=text, mark='relation2', label=8)
            else:
                self.voc.generated_list.append([text, 'relation2', 8, *vector])

    def gen_patrol_circle(self):
        """
        Генератор команд патрулирования по кругу с заданным радиусом
        Номер шаблона - 9
        Returns:

        """
        for patrol in self.voc.simple_actions['patrol']:
            for circle in self.voc.circle:
                for radius in self.voc.radius:
                    for k_m in self.voc.meters.keys():
                        for meter in self.voc.meters[k_m]:
                            for measure in self.voc.measure['meters']:
                                if len(measure) > 2:
                                    m = self.agree_with_number(measure, meter)
                                else:
                                    m = measure
                                text = self.text_pattern_patrol_circle.format(patrol, circle, radius, meter, m)
                                rdf = self.patrol_circle(num=str(k_m))
                                vector = self.rdf_to_nn(rdf)

                                if self.use_generated_dict:
                                    self._generated_update(text=text, mark='circle', label=9)
                                else:
                                    self.voc.generated_list.append([text, 'circle', 9, *vector])

    def gen_move_selfrelation_object(self):
        """
        Генератор команд движения/поиска/объезда/осмотра объекта относительно робота
        Номер шаблона - 10
        Returns:

        """
        for k_a in self.voc.actions_to.keys():
            cases = self.voc.actions_to[k_a]
            for case in cases.keys():
                for action in cases[case]:
                    for k_o in self.voc.objects.keys():
                        for obj in self.voc.objects[k_o]:
                            for k_sr in self.voc.self_relation.keys():
                                for self_case in self.voc.self_relation[k_sr]:
                                    for selfrel in self.voc.self_relation[k_sr][self_case]:
                                        for name in self.voc.self_names:
                                            o = self.case_to_object(obj, {case})
                                            if name:
                                                if selfrel == 'справа' or selfrel == 'слева':
                                                    sr = selfrel + ' от'
                                                else:
                                                    sr = selfrel
                                                me = self.case_to_object(name, {self_case})
                                            else:
                                                me = name
                                                if selfrel == 'за':
                                                    break
                                                else:
                                                    sr = selfrel

                                            text = self.text_pattern_move_to_self_object.format(action, o, sr, me)
                                            rdf = self.move_selfrelation_object(act=k_a, obj1=k_o, selfrel=k_sr)
                                            vector = self.rdf_to_nn(rdf)

                                            if self.use_generated_dict:
                                                self._generated_update(text=text, mark='self', label=10)
                                            else:
                                                self.voc.generated_list.append([text, 'self', 10, *vector])

    def gen_move_gaze_focus_on(self):
        """
        Генератор команд движения по направлению взгляда
        Номер шаблона - 11
        Returns:

        """
        obj_dict = self.voc.objects.copy()
        obj_dict[''] = ['']

        for action in self.voc.move_on['move_on']:
            for focus in self.voc.focus:
                for k_o in obj_dict:
                    for o in obj_dict[k_o]:
                        try:
                            obj = ', к ' + self.case_to_object(o, {'datv'})
                        except AttributeError:
                            obj = ''

                        text = self.text_pattern_move_gaze_focus_on.format(action, focus, obj)
                        rdf = self.move_gaze_focus_on(obj1=k_o)
                        vector = self.rdf_to_nn(rdf)

                        if self.use_generated_dict:
                            self._generated_update(text=text, mark='gaze', label=11)
                        else:
                            self.voc.generated_list.append([text, 'gaze', 11, *vector])

            for f in self.voc.focus_on_object:
                for k_o in obj_dict:
                    for o in obj_dict[k_o]:

                        try:
                            gender = self.gender(o)
                            obj = self.case_to_object(o, {'datv'})

                            focus = []
                            for word in f.split(' '):
                                try:
                                    focus.append(self.case_to_object(word, {gender}))
                                except AttributeError:
                                    focus.append(word)

                            focus = ' '.join(focus)

                            text = self.text_pattern_move_gaze_focus_on.format(action, focus, obj)
                            rdf = self.move_gaze_focus_on(obj1=k_o)
                            vector = self.rdf_to_nn(rdf)

                            if self.use_generated_dict:
                                self._generated_update(text=text, mark='gaze', label=11)
                            else:
                                self.voc.generated_list.append([text, 'gaze', 11, *vector])

                        except AttributeError:
                            pass

    def agree_with_number(self, word, num):
        """
        Согласование слова с числом
        Args:
            word: слово
            num: число

        Returns:

        """
        return self.morph.parse(word)[0].make_agree_with_number(num).word

    def case_to_object(self, word, case):
        """
        Склонение слов
        Args:
            word: слово
            case: падеж, род и т.д.

        Returns:

        """
        splt = word.split(' ')
        words = []
        for w in splt:
            words.append(self.morph.parse(w)[0].inflect(case).word)

        return ' '.join(words)

    def gender(self, word):
        """
        Род объектов
        Args:
            word: объект

        Returns:
            признак рода
        """
        return self.morph.parse(word)[0].tag.gender

    def animacy(self, word):
        """
        Одушевленность объектов
        Args:
            word: объект

        Returns:
            признак одушевленности
        """
        return self.morph.parse(word)[0].tag.animacy

    def _sample(self, size):
        """
        Sample and shuffled data
        Args:
            size: sample size

        Returns:
            list of sampled data
        """
        seed(13)
        data = self.voc.generated_list.copy()

        if size != 0:
            data = sample(data, size)

        shuffle(data)
        del self.voc.generated_list
        self.voc.generated_list = []

        return data

    def generate_with_vector(self):
        """
        Генератор текстовых команд с векторным представлением RDF
        Returns:

        """
        self.gen_simple()
        simple = self._sample(0)

        self.gen_move_rotate_dir()
        direction = self._sample(0)

        self.gen_move_num()
        meter = self._sample(5000)

        self.gen_rotate_deg()
        degree = self._sample(5000)

        self.gen_rotate_hours()
        hour = self._sample(5000)

        self.gen_move_to_object()
        objs = self._sample(0)

        self.gen_move_to_nearest_object()
        nearest = self._sample(0)

        self.gen_move_to_object_relation1(2e5)
        relation1 = self._sample(10000)

        self.gen_move_to_object_relation2(5e5)
        relation2 = self._sample(10000)

        self.gen_patrol_circle()
        circle = self._sample(5000)

        self.gen_move_selfrelation_object()
        self_rel = self._sample(5000)

        self.gen_move_gaze_focus_on()
        gaze = self._sample(5000)

        data = simple + direction + meter + degree + hour + objs + nearest + relation1 + relation2 + circle + self_rel + gaze
        columns = ['x', 'y_name', 'y'] + self.voc.keys

        generated = pd.DataFrame(data=data, columns=columns)
        generated.to_csv('data/generated_with_vector.csv', sep=';', index=False)

    def generate_gaze_pattern(self):
        self.gen_move_gaze_focus_on()
        gaze = self._sample(5000)

        data = gaze
        columns = ['x', 'y_name', 'y'] + self.voc.keys

        generated = pd.DataFrame(data=data, columns=columns)
        generated.to_csv('data/generated_gaze.csv', sep=';', index=False)


if __name__ == '__main__':
    gen = Generator()
