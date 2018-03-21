'''
将笛子简谱转换成五线谱

这里假设笛子6个孔代表的key分别是：
2 2 1 2 2 1
目前只支持大调，暂不支持升调式
暂时只支持C调笛
@perf
处于性能的考虑，不进行安全检查
@version 0.1
将唱名转换成音名
@version 0.2
加入音符的歌词
'''

def diaoxing(diaohao, tongyin): # 判断笛子调性
	temp = {"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11, \
	"bC":11,"bD":1,"bE":3,"bF":4,"bG":6,"bA":8,"bB":10, \
	"#C":1,"#D":3,"#E":5,"#F":6,"#G":8,"#A":10,"#B":0
	}
	temp1 = ["C", "bD", "D", "bE", "E", "F", "bG",\
	"G", "bA", "A", "bB", "B"]
	change = 0
	if tongyin == '1':
		change = 5
	elif tongyin == '2':
		change = -10 + 5 + 12
	elif tongyin == '3':
		change = -8 + 5 + 12
	elif tongyin == '4':
		change = -7 + 5 + 12
	elif tongyin == '5':
		change = -5 + 5
	elif tongyin == '6':
		change = -3 + 5
	else:
		change = -1 + 5
	yinkey = (temp[diaohao] + change) % 12
	print("这是一根 %s 调笛" % temp1[yinkey])

	
# GLOBAL VARIABLES
note_processed = 0 # 已经处理了的音符的数量
note_pos = 0 # 小节内音符的位置
measure_pos = 0 # 小节的位置
meter = []
diaohao = "" # key signature
yinmap = {} # 唱名到音名的映射

import sys
f = open(sys.argv[1], encoding="utf-8")
fl = f.readlines()
title = fl[0]
extra = fl[1].split(" ")
if extra[0] != "笛子" :
	print("错误！这是 %s 谱" % extra[0])
for i in extra[1:]:
	meter.append(i.split("/"))
extra = fl[2].split(" ")
diaohao = extra[0].split("=")[1]
# tongyin = extra[1][-2] # -1 是 '\n'
# diaoxing(diaohao, tongyin)
if diaohao == "C":
	# 按照C调笛的样式来
	yinmap = {'0':"00", '1':'C5','2':'D5','3':'E5','4':'F5','5':'G5','6':'A5','7':'B5'}
else:
	pass
	
yuepu = " ".join([i.strip() for i in fl[3:]])
ypstream = yuepu.split(" ")

import music21

def getBestQuarterLength(meter):
	return int(meter[0][1])/4.0

def process_note(nstr, meter):
	l = nstr.split("(")
	yin = yinmap[l[0]]
	
	if len(l) == 1:
		if yin == "00":
			f = music21.note.Rest()
		else:
			f = music21.note.Note(yin)
		f.quarterLength = getBestQuarterLength(meter)
		f.lyric = l[0]
		return f
	else:
		l1 = l[1][:-1].split(",") # rid )
		keyupdown = ""
		octave = int(yin[1])
		ql = 0.0
		for i in l1:
			if i == "#":
				keyupdown = "#"
			elif i == "b":
				keyupdown = "-"
			elif i[0] == "H":
				octave += len(i)
			elif i[0] == "L":
				octave -= len(i)
			else: # only float number possible
				ql = float(i)
		if ql == 0.0:
			ql = getBestQuarterLength(meter)
		if yin == "00":
			f = music21.note.Rest()
		else:
			f = music21.note.Note(yin[0]+keyupdown+str(octave))
		f.quarterLength = ql
		f.lyric = l[0]
		return f

score = music21.stream.Score()
score.metadata = music21.metadata.Metadata(title=title)
part = music21.stream.Part()
part.append(music21.instrument.Flute())
# ignore clef
# ignore key signature for C dizi

measure = None
meter_flag = False

if len(meter) == 1:
	part.append(music21.meter.TimeSignature("/".join(meter[0])))
	meter_flag = False
else:
	meter_flag = True	# 每小节单独处理meter
	
note_flag = False
note_prev = ""
slur_flag = 0
slur_stack = []
tie_flag = False	# 不允许嵌套
tie_stack = []
for i in ypstream:
	note_flag = False
	note_cur = i
	if len(i) == 1:
		if i == '{':
			slur_stack.append([])
			slur_flag += 1
		elif i == '[':
			tie_stack.append([])
			tie_flag = True
		elif i == "}":
			sl = music21.spanner.Slur(slur_stack[-1])
			part.insert(0, sl)
			slur_flag -= 1
			slur_stack = slur_stack[:-1]
		elif i == ']':
			tie_stack[0][0].tie = music21.tie.Tie('start')
			tie_stack[0][-1].tie = music21.tie.Tie('stop')
			for j in tie_stack[0][1:-1]:
				j.tie = music21.tie.Tie('continue')
			
			tie_flag = False
			tie_stack = []
		elif i == '|':
			measure_pos += 1
			note_pos = 0
			if meter_flag == True:
				measure.insert(0, music21.meter.bestTimeSignature(measure))
			part.append(measure)
		elif i == '-':
			note_cur = note_prev
			note_flag = True
		elif i.isdigit() == True:
			note_flag = True
	else:
		note_flag = True
	if note_flag == True:
		if note_pos == 0:
			measure = music21.stream.Measure()
			measure.number = measure_pos
		note_pos += 1
		f = process_note(note_cur, meter)
		measure.append(f)
		if slur_flag > 0:
			for j in slur_stack:
				j.append(f)
		if tie_flag == True:
			tie_stack[0].append(f)
		note_prev = note_cur

score.append(part)
fn = sys.argv[1].split(".")[0] + ".xml"
score.write(fmt="musicxml",fp=fn)
		