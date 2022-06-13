# AEDA: An Easier Data Augmentation Technique for Text classification
# Akbar Karimi, Leonardo Rossi, Andrea Prati

import random

random.seed(0)

PUNCTUATIONS = ['.', ',', '!', '?', ';', ':']
# DATASETS = ['cr', 'sst2', 'subj', 'pc', 'trec']
NUM_AUGS = [1, 2, 4, 8]
PUNC_RATIO = 0.3

# Insert punction words into a given sentence with the given ratio "punc_ratio"
def insert_punctuation_marks(sentence, punc_ratio=PUNC_RATIO):
	words = sentence.split(' ')
	new_line = []
	q = random.randint(1, int(punc_ratio * len(words) + 1))
	qs = random.sample(range(0, len(words)), q)

	for j, word in enumerate(words):
		if j in qs:
			new_line.append(PUNCTUATIONS[random.randint(0, len(PUNCTUATIONS)-1)])
			new_line.append(word)
		else:
			new_line.append(word)
	new_line = ' '.join(new_line)
	return new_line


def main(dataset):
	for aug in NUM_AUGS:
		data_aug = []
		with open(dataset + '/train.txt', 'r') as train_orig:
			for line in train_orig:
				line1 = line.split('\t')
				label = line1[0]
				sentence = line1[1]
				for i in range(aug):
					sentence_aug = insert_punctuation_marks(sentence)
					line_aug = '\t'.join([label, sentence_aug])
					data_aug.append(line_aug)
				data_aug.append(line)

		with open(dataset + '/train_orig_plus_augs_' + str(aug) + '.txt', 'w') as train_orig_plus_augs:
			train_orig_plus_augs.writelines(data_aug)


if __name__ == "__main__":
	for dataset in DATASETS:
		main(dataset)