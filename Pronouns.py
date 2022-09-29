import random
import pandas as pd

from generator.ComplexGenerator import ComplexGenerator


class PronounsGeneratorDataset(ComplexGenerator):

    def __init__(self):
        super(PronounsGeneratorDataset, self).__init__()
        self.actions_for_pronouns = ['object', 'nearest', 'relation1', 'relation2', 'self', 'gaze']
        self.separator = [',', ' и']

    def prep_gen_command_verb(self, cmd):
        previous = cmd['text']
        verb_num = cmd['verb_num']
        obj = cmd['object']

        coins = list(self.dictionary.to_obj_schema.keys())
        coins.remove(verb_num)
        try:
            coins.remove(1) # find
        except ValueError:
            pass
        coin_verb = random.choice(coins)

        verbs = self.dictionary.to_obj_schema[coin_verb]
        action = verbs[0]
        text_verb = random.choice(verbs[1])

        sep = random.choice(self.separator)
        previous_with_sep = previous.strip() + sep

        return {
            'action': action,
            'object': obj,
            'previous_with_sep': previous_with_sep,
            'text_verb': text_verb
        }

    def prep_gen_command_object(self, cmd):

        if cmd['action'] in ['move_to', 'rotate_to']:
            coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
            to = coin_case[1] + self.case_to_object(cmd['object'], {coin_case[0]})
        else:
            to = self.case_to_object(cmd['object'], {'accs'})

        return ' '.join([cmd['previous_with_sep'], cmd['text_verb'], to])

    def prep_gen_command_pronoun(self, cmd):

        gender = self.gender(cmd['object'])
        pronoun = self.pnoun[gender]

        if cmd['action'] in ['move_to', 'rotate_to']:
            coin_case = random.choice([('datv', 'к '), ('gent', 'до ')])
            to = coin_case[1] + self.case_to_object(pronoun, {'3per', 'Af-p', coin_case[0]})
        else:
            to = self.case_to_object(pronoun, {'3per', 'accs'})

        return ' '.join([cmd['previous_with_sep'], cmd['text_verb'], to])

    def gen_pronouns_with_object(self, patience=1e3):
        input_ = []
        output_ = []
        for n in range(int(patience)):
            action_with_object_cmd = random.choice(self.actions_for_pronouns)
            cmd = self.dist[action_with_object_cmd](patience=1, pattern=action_with_object_cmd, save=False, n=0)

            prop_of_cmd = self.prep_gen_command_verb(cmd)
            complex_with_nouns = self.prep_gen_command_object(prop_of_cmd)
            complex_with_pronouns = self.prep_gen_command_pronoun(prop_of_cmd)

            input_.append(complex_with_pronouns)
            output_.append(complex_with_nouns)

        dataset = pd.DataFrame({
            'in': input_,
            'out': output_
        })

        uniq_dataset = dataset.drop_duplicates().reset_index(drop=True)
        uniq_dataset.to_csv('data/pronouns_to_object_v1.csv', sep=';', index=False)

    def gen_pronouns_with_single_object(self, patience=1e3):
        input_ = []
        output_ = []
        for _ in range(int(patience)):
            action = random.choice(self.actions_for_pronouns)
            cmd = self.dist[action](patience=1, pattern=action, save=False, n=0)

            prop_of_cmd = self.prep_gen_command_verb(cmd)
            complex_with_pronouns = self.prep_gen_command_pronoun(prop_of_cmd)
            obj = prop_of_cmd['object']

            input_.append(complex_with_pronouns)
            output_.append(obj)

        dataset = pd.DataFrame({
            'in': input_,
            'out': output_,
        })

        uniq_dataset = dataset.drop_duplicates().reset_index(drop=True)
        uniq_dataset.to_csv('data/pronouns_to_object_v2.csv', sep=';', index=False)

    def gen_object_and_pronouns(self, patience=1e3):
        input_ = []
        output_ = []
        for _ in range(int(patience)):
            action = random.choice(self.actions_for_pronouns)
            cmd = self.dist[action](patience=1, pattern=action, save=False, n=0)

            prop_of_cmd = self.prep_gen_command_verb(cmd)
            complex_with_pronouns = self.prep_gen_command_pronoun(prop_of_cmd)

            input_.append(complex_with_pronouns)

            pronoun = complex_with_pronouns.split(' ')[-1]
            before_pronoun = complex_with_pronouns.split(' ')[-2]

            if prop_of_cmd['action'] in ['move_to', 'rotate_to']:
                if before_pronoun == 'к':
                    obj = self.case_to_object(prop_of_cmd['object'], {'datv'})
                else:
                    obj = self.case_to_object(prop_of_cmd['object'], {'gent'})
            else:
                obj = self.case_to_object(prop_of_cmd['object'], {'accs'})

            output_.append(' '.join(['Местоимение:', pronoun+'.', 'Объект:', obj]))

        dataset = pd.DataFrame({
            'in': input_,
            'out': output_,
        })

        uniq_dataset = dataset.drop_duplicates().reset_index(drop=True)
        uniq_dataset.to_csv('data/pronouns_to_object_v3.csv', sep=';', index=False)

    def gen_eval_dataset(self, patience=1e3):
        eval = []
        for _ in range(int(patience)):
            action = random.choice(self.actions_for_pronouns)
            cmd = self.dist[action](patience=1, pattern=action, save=False, n=0)

            prop_of_cmd = self.prep_gen_command_verb(cmd)
            complex_with_pronouns = self.prep_gen_command_pronoun(prop_of_cmd)

            pronoun = complex_with_pronouns.split(' ')[-1]
            obj = cmd['cased']

            eval.append(complex_with_pronouns)

            obj_pos = complex_with_pronouns.find(obj)
            obj_len = len(obj)
            pronoun_pos = complex_with_pronouns.find(pronoun)
            pronoun_len = len(pronoun)

            with open(f'true_keys/cmd_{_}.txt', 'w') as file:
                file.write(f'1 {obj_pos} {obj_len} 1\n')
                file.write(f'2 {pronoun_pos} {pronoun_len} 1')

        df = pd.DataFrame(eval)
        df.to_csv('eval/eval.csv', sep=';', index=False)


if __name__ == '__main__':
    pgen = PronounsGeneratorDataset()
    # pgen.gen_pronouns_with_object(patience=2e4)
    # pgen.gen_pronouns_with_single_object(patience=2e4)
    # pgen.gen_object_and_pronouns(patience=2e4)
    pgen.gen_eval_dataset()