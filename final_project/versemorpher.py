import re
import gensim
import urllib.request
import os.path
import random

import pymorphy2

morph = pymorphy2.MorphAnalyzer()

#from gensim.models import word2vec

#загружаем модель для word2vec
m = 'http://rusvectores.org/static/models/rusvectores2/ruscorpora_mystem_cbow_300_2_2015.bin.gz'
suffixes = {'ADJF': 'A', 'ADJS' : 'A', 'COMP':'A', 'NOUN': 'S', 'VERB': 'V', 'INFN': 'V', 
            'ADVB': 'ADV', 'PRTF': 'V', 'PRTS' : 'V', 'GRND' :'V'}
#suffixes = {'ADJF': 'ADJ', 'ADJS' : 'ADJ', 'COMP':'ADJ', 'NOUN': 'NOUN', 'VERB': 'VERB', 'INFN': 'VERB', 
#            'ADVB': 'ADV', 'PRTF': 'VERB', 'PRTS' : 'VERB', 'GRND' :'VERB'}
#m = 'https://rusvectores.org/static/models/ruscorpora_upos_skipgram_600_10_2017.bin.gz'
f = os.path.basename(m)
if not os.path.exists(f) :
    urllib.request.urlretrieve(m, f)
    
variantCount = 25

if m.endswith('.vec.gz'):
    model = gensim.models.KeyedVectors.load_word2vec_format(f, binary=False)
elif m.endswith('.bin.gz'):
    model = gensim.models.KeyedVectors.load_word2vec_format(f, binary=True)
else:
    model = gensim.models.KeyedVectors.load(f)

reVow = re.compile(r"[^иыэеаяоёуюИЫЭЕАЯОЁУЮ]",flags=re.UNICODE)
#посчитать гласные в слове
def countVows(w) :
    return len(re.sub(
       reVow,
       '',
       w
    ))

#парсит базу ударений
def buildAcentBase() :
    base = {}
    for line in open('accentBase.txt', 'r', encoding='cp1251') :
        parts = line.split('#')[1].split(',')
        for p in parts :
            x = p
            if x.strip() == u'' : continue
            acc = countVows(x[0:x.find(u"'")-1])
            w = x.replace(u"'", u"")
            if w not in base : base[w] = []
            if acc not in base[w]: base[w].append(acc)
    return base
accentBase = buildAcentBase()

#ищем все возможные ударения в слове
def findAccent(w):
    if u'ё' in w: return [countVows(w[0:w.find(u'ё')])]
    vows = countVows(w)
    if vows == 0: return [-1]
    if vows == 1: return [0]

    w = w.lower()
    if w not in accentBase: return []
    # if len(accentBase[w])==0 : return -1
    return accentBase[w]

#схема слова - (кол-во гласных, номер ударной)
#возвращает множество возможных схем данного слова
def word2Scheme(w):
    acc = findAccent(w)
    if len(acc) == 0: return None
    vow = countVows(w)
    return set([(vow, a) for a in acc])

#вписывается ли слово в метр
#stressScheme - схема метра, например [0,1] для хорея
#wordStart сколько слогов в строке до этого слова
#wordScheme схема слова
def wordApplicableAt(stressScheme, wordStart, wordScheme) :
    if wordScheme[1] < 0 : return True
    wordAcc = wordStart + wordScheme[1]
    wordEnd = wordStart + wordScheme[0]
    return stressScheme[wordAcc % len(stressScheme)] == 1 or \
                        sum([stressScheme[x % len(stressScheme)] for x in range(wordStart, wordEnd)]) == 0 

# составляет схемы возможных ударений для строчки
# схема потом применяется функцией applySchemeRandomly
# wordsSchemes - наборы возможных схем для каждого слова в строчке
# stressScheme - схема метра
# possibleSyllabs - возможное кол-во слогов в строке
def findAllSchemes(wordsSchemes, stressScheme, possibleSyllabs):
    res = [set(possibleSyllabs)]

    for schemes in reversed(wordsSchemes):
        newPossibleSyllabs = []
        for scheme in schemes:
            for syl in possibleSyllabs:
                wordStart = syl - scheme[0]
                if wordStart < 0: continue
                wordAcc = wordStart + scheme[1]
                # if stressed syllab not accent and there is some accent in the word
                if not wordApplicableAt(stressScheme, wordStart, scheme): continue
                newPossibleSyllabs.append(wordStart)
        possibleSyllabs = set(newPossibleSyllabs)
        res.insert(0, possibleSyllabs)

    return res

#применяет одну из схем, найденных функцией findAllSchemes к конкретным словам
#слова выбираются рандомно из предложенных вариантов
def applySchemeRandomly(words, stressScheme, foundSchemes) :
    curPos = 0
    res = []
    for i in range(len(words)) :
        ws = list(words[i])
        random.shuffle(ws)
        
        poses = foundSchemes[i+1]
        
        foundWord = False
        for w in ws :
            if curPos + countVows(w) not in poses : continue
            
            for scheme in word2Scheme(w) :
                if not wordApplicableAt(stressScheme, curPos, scheme): continue
                foundWord = True
                
            if foundWord :
                res.append(w)
                curPos += countVows(w)
                break
                
        if not foundWord:
            #print('Fail')
            return None
            
    return res

#по части речи определить список родственных частей речи (которые могут быть между собой транформированы)
def getPosGroup(pos) :
    posGroups = [
        ['ADJF', 'ADJS','COMP'],
        ['VERB', 'INFN', 'PRTF', 'PRTF', 'GRND'],
        ['ADVB'],
        ['NOUN']
    ]
    posGroups = [x for x in posGroups if pos in x]
    return posGroups[0] if len(posGroups)>0 else [pos]

def capLetter(l) :
    return l[0].upper() + l[1:]

#приводим слово src к такой же форме, какую имеет dst
#при этом убеждаемся, что во всех интерфпретация слова dst получается одно и то же
#иначе возвращаем None
def morphWord(src, dst) :
    #dstPoss = set([x.tag.POS for x in morph.parse(dst)])
    #if len(dstPoss) != 1 : return None
    pos = morph.parse(dst)[0].tag.POS #dstPoss.pop()
    
    posGroup = getPosGroup(pos)
    srcForms = [x for x in morph.parse(src) if x.tag.POS in posGroup]
    if len(srcForms) == 0 : return None

    ress = []
    for form in morph.parse(dst):
        w = srcForms[0]
        t = form.tag
        res = w.inflect(
            {x for x in {t.POS, t.case, t.number, t.mood, t.person, t.tense, t.voice, t.aspect,
                        t.gender} if x is not None})
        if res is not None : ress.append(res.word)
        #w = morph.parse(src)#[0]
        #t = morph.parse(dst)[0].tag
        #res = w.inflect({x for x in {t.POS, t.case, t.number, t.mood, t.person, t.tense, t.voice, t.aspect} if x is not None})
        #return res.word if res is not None else None

    resSet = set(ress)
    #print(resSet)
    if len(resSet) != 1 : return None

    res = resSet.pop()

    if dst[0].isupper() :
        res = capLetter(res)

    return res

reWordSel = re.compile(r'([^\W\d_]+|[\W\d_]+)',flags=re.UNICODE)
reWord = re.compile(r'[^\W\d_]+',flags=re.UNICODE)

#приводим слово и добавляем его суффикс, как требуется в модели
def word2model(w) :
    form = morph.parse(w)[0]
    pos = form.tag.POS
    if pos not in suffixes: return None

    return '%s_%s' % (form.normal_form, suffixes[pos])

#для каждого слова строки l находим множество замен по принципу l - minus + plus
#замены приводим к правильной форме
#функция возвращает tuple: (список вариантов замен, список пробелов между словами)
def morphLine(l, plus, minus, variantCount = 25):
    plus_m = word2model(plus)
    minus_m = word2model(minus)

    res = []
    spaces = []
    for w in re.findall(reWordSel, l) :
        if not re.match(reWord, w) :
            spaces.append(w)
            continue

        if len(spaces)==0 : spaces.append('')
            
        if w==minus :
            ans = morphWord(plus, w)
            if ans is None : return (None, None)
            
            res.append([ans])
            continue

        w_m = word2model(w)

        if w_m is None or w_m not in model :
            res.append([w])
            continue

        if w!=minus : 
            top = model.most_similar(positive=[w_m, plus_m], negative=[minus_m], topn=500)
        else :
            top = [[plus_m]]
            
        #print(top)
        morphs = []
        for x in top :
            m = morphWord(x[0].split('_')[0], w)
            if m is not None and len(findAccent(m))==1 :
                morphs.append(m)
            if len(morphs) >= variantCount : break

        if not morphs : morphs = [w]
        res.append(morphs)

    spaces.append('')
    return (res, spaces)

#составляем схемы для каждого слова в строке
def schemeAll(lineWords) :
    #print([[word2Scheme(w) for w in ws if word2Scheme(w) is not None] for ws in lineWords])
    #schemes = [[word2Scheme(w) for w in ws] for ws in lineWords]
    args = [[word2Scheme(w) for w in ws if word2Scheme(w) is not None] for ws in lineWords]
    if any(not x for x in args) : return None
    
    return [set.union(*x) for x in args]

#первый этап морфирования строки fullProcLine - поиск замен
def prepaireLine(l, plus, minus, variantCount=25) :
    words, spaces = morphLine(l, plus, minus, variantCount)
    if words is None or spaces is None : return None
    
    s = schemeAll(words)
    if s is None : return None
    
    return (words, spaces, s)

#второй этап морфирования строки fullProcLine - на основе выбранного списка замен ищем тот, который впишется в заданный метр
def processLine(prepaired, stressScheme, possibleSyllabs) :
    if prepaired is None : return None
    words, spaces, s = prepaired
    
    foundSchemes = findAllSchemes(s, stressScheme, possibleSyllabs)
    if 0 not in foundSchemes[0] : return None
    
    lll = applySchemeRandomly(words, stressScheme, foundSchemes)
    if lll is None : return None
    
    return ''.join([spaces[0]] + [lll[i//2] if i % 2 == 0 else spaces[1+i//2] for i in range(2*len(words))])
    
#заменяем в строке слова по принципу w-minus+plus, и подбираем такие замены, 
#чтобы они вписались в метр, заданный параметрами stressScheme, possibleSyllabs
def fullProcLine(l, plus, minus, stressScheme, possibleSyllabs):
    return processLine(prepaireLine(l,plus,minus), stressScheme, possibleSyllabs)

#возвращает первое слово хокку и его ранг - доля слов нашей модели
def parseHokku(h) :
    firstWord = None
    goodWords = 0
    badWords = 0
    
    for w in re.findall(reWord, h) :
        w_m = word2model(w)
        bad = w_m is None or w_m not in model

        if bad and len(findAccent(w)) == 0 : return None
        
        if bad : badWords += 1
        else : goodWords += 1
            
        if firstWord is None:
            if bad and badWords>1 : return None
            if not bad : firstWord = w
            
    return (firstWord, goodWords / (goodWords + badWords))

#приведённая часть речи слова
def getWordTag(word) :
    return getPosGroup(morph.parse(word)[0].tag.POS)[0]

#парсить многострочную схему ударений в формате -\--\--\--
#возвращает список схем строк
def parseScheme(x) :
    return [[1 if s=='\\' else 0 for s in l] for l in x.split('\n') if set(l) == {'-', '\\'}]

#этот класс задаёт корпус текстов и корпус ритических схем
#он позволяет морфировать рандомный текст, добавляя в него нужное слово
#и выстраивая результат по одной из данных ритмических схем
class VerseCorpa :
    def __init__(self, verseFile, schemeFile):
        # загружаем схемы и парсим их
        with open(schemeFile, 'r', encoding='utf-8') as file:
            self.schemes = [parseScheme(x) for x in file.read().split('\n\n')]

        # парсим корпус хокку
        with open(verseFile, 'r', encoding='utf-8') as file:
            hokku = file.read().split('\n\n')

        # составим список хокку по части речи первого слова
        self.hokkuByTag = {}
        for h in hokku:
            ph = parseHokku(h)
            if ph is None: continue

            firstWord, rank = ph
            tag = getWordTag(firstWord)

            if tag not in self.hokkuByTag: self.hokkuByTag[tag] = []
            self.hokkuByTag[tag].append((h, firstWord, rank))

        # отсортируем их по рангу
        for tag, h in self.hokkuByTag.items():
            h.sort(key=lambda x: -x[2])

    # морфируем опр. хокку по рандомной схеме (перебираем схемы)
    def morphHokkuRandomScheme(self, hokku, plus, minus, variantCount=25):
        schemesShuf = self.schemes.copy()
        random.shuffle(schemesShuf)

        lines = [prepaireLine(l, plus, minus, variantCount) for l in hokku.split('\n')]
        if None in lines: return None

        for scheme in schemesShuf:
            res = [processLine(lines[i], scheme[i], [len(scheme[i])]) for i in range(len(lines))]
            if None not in res: return '\n'.join(res)

    # морфируем рандомный хокку по рандомной схеме
    # заменяя первое слово на word
    def morphRandomHokku(self, word, variantCount=25):
        tag = getWordTag(word)
        allHokkus = self.hokkuByTag[tag][0:len(self.hokkuByTag[tag]) // 3]
        random.shuffle(allHokkus)

        for hokkuInfo in allHokkus:
            hokku, firstWord, rank = hokkuInfo
            print(hokku)
            res = self.morphHokkuRandomScheme(hokku, word, firstWord, variantCount)
            if res is not None: return res

#hokkus = VerseCorpa('bashuo.txt','hokku-schemes.txt')
#hokkus = VerseCorpa('bashuo.txt','hokku-schemes.txt')
#print(hokkus.morphRandomHokku('компьютер', 20))