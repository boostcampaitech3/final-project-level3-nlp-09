from pororo import Pororo
import pandas as pd

mt = Pororo(task="mt", lang="multi", model="transformer.large.multi.mtpg")

def back_translation(sentence,language):
    sentence_raw=mt(sentence, src= 'ko', tgt=language)
    sentence_bt=mt(sentence_raw, src=language, tgt ='ko')
    return sentence_bt

