from Pronouns import PronounsGeneratorDataset


gen = PronounsGeneratorDataset()
gen.gen_eval_dataset()
gen.set_eval_and_train('data/pronouns_to_object_v3.csv', 'eval/eval.csv')
