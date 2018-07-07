# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os
import unicodedata
import csv

CJK_IDENTIFIER = 'CJK UNIFIED IDEOGRAPH'
OOV_THRESHOLD = 2
LENGTH_THRESHOLD = 4

def IsCJK(character):
	try:
		return unicodedata.name(character).startswith(CJK_IDENTIFIER)
	except ValueError, v:
		return False

def GetTraditionalSentences(fname):
	def HasCJK(s):
		return any(IsCJK(c) for c in s)
	html = open(fname, 'rb').read()
	raw_text = BeautifulSoup(html, 'html.parser').get_text()
	lines = raw_text.split('\n')

	sentences = []
	for l in lines:
		sentences += l.split(u'\u3002')  # Chinese period
	sentences = [s.strip() for s in sentences if s.strip()]
	return sentences

def Simplify(sentence, vocabulary):
	new_sentence = ''
	for c in sentence:
		if c in vocabulary:
			new_sentence += vocabulary[c]
		else:
			new_sentence += c
	return new_sentence

def CountOOV(sentence, vocabulary):
	return sum(c not in vocabulary and IsCJK(c) for c in sentence)

def CountCJK(sentence):
	return sum(IsCJK(c) for c in sentence)

def ReadVocabulary(csv_path):
	reader = csv.reader(open(csv_path, 'rb'))
	next(reader)  # skip header row
	vocab = {}
	for row in reader:
		simplified = row[1].strip().decode('utf-8')
		traditional = row[2].strip().decode('utf-8')
		if not traditional:
			traditional = simplified
		for t in traditional:
			vocab[t] = simplified
	return vocab

def Readable(sentence, vocabulary, oov_threshold=OOV_THRESHOLD, length_threshold=LENGTH_THRESHOLD):
	oov = CountOOV(sentence, vocab)
	n_cjk = CountCJK(sentence)
	return oov <= oov_threshold and n_cjk >= length_threshold and n_cjk > 0.5 * len(sentence)

if __name__ == '__main__':
	root_dir = '/Users/jinna/workspace/chinese_sentence_finder/wikipedia_dump/articles/'
	vocab = ReadVocabulary('learned_vocabulary.csv')

	# Scrape Wikipedia
	num_chars = 0
	for dir_name, subdirs, files in os.walk(root_dir):
		for fname in files:
			if fname == '.DS_Store':
				continue
			full_path = os.path.join(dir_name, fname)

			traditional = GetTraditionalSentences(full_path)
			simplified_readable = [Simplify(t, vocab) for t in traditional if Readable(t, vocab)]
			for s in simplified_readable:
				if s != '联系我们'.decode('utf-8') and s != '五大支柱'.decode('utf-8'):
					print '__OOV__' + str(CountOOV(s, set(vocab.values()))), '\t', s.encode('utf-8'), '\t', '__FILE__' + fname
