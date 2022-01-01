import re
import nltk
from nltk.util import unique_list
from nltk.metrics.scores import recall,precision
import pickle
from operator import itemgetter
from tkinter import*

#生成所有可能路径
def able_path(sub_text,pinyin_list):
    #sub_text=text.split(' ')
    old_list=[]
    cur_list=[]
    for len_text in range(len(sub_text)):
        #第一个字符
        if len_text==0:
            flag=False
            for i in range(len(pinyin_list)):
                if pinyin_list[i][0]==sub_text[0]:
                    flag=True
                    for j in range(len(pinyin_list[i][1])):
                        cur_list.append((sub_text[0],pinyin_list[i][1][j]))
            if flag==False:
                error_put=[]
                return error_put
        else:
            flag=False
            old_list=cur_list
            cur_list=[]
            for i in range(len(pinyin_list)):
                if pinyin_list[i][0]==sub_text[len_text]:
                    flag=True
                    for j in range(len(pinyin_list[i][1])):
                        for k in range(len(old_list)):
                            #new_one=old_list[k]
                            new_one=[]
                            new_one.append(old_list[k])
                            new_one.append((sub_text[len_text],pinyin_list[i][1][j]))
                            #tuple(sub_text[len_text],pinyin_list[i][1][j])
                            cur_list.append(new_one)
            if flag==False:
                error_put=[]
                return error_put
    return cur_list

print('正在训练，请耐心等待')

#读入pinyin.py
text_pinyin=[]
dicFile=open('pinyin.txt','r')
while True:
    line = dicFile.readline()
    line = line.strip('\n')
    text_pinyin.append(line)
    if not line:
        break
dicFile.close()
del(text_pinyin[-1])

#形成tag和发射概率矩阵（为了单个音节用）
pinyin_pro=[]
pinyin_list=[]
for i in range(len(text_pinyin)):
    sub_pinyin=text_pinyin[i].split(':')
    pinyin_list.append((sub_pinyin[0],sub_pinyin[1]))
    pro_ori=[]
    for j in range(len(sub_pinyin[1])):
        pro_ori.append(0)
    pinyin_pro.append((i,pro_ori))
#print(len(pinyin_list))
#print(pinyin_pro[0])

#一些量
num_pinyin=0

#读入训练集
symbols = set()
tags = set()
new_sentence = []
new_sentences = []

with open('word_seg_train.txt', encoding='gb18030') as f:
#with open('word_seg.txt') as f:
    r = re.compile(r'(.+)/(.+)')
    i = 0
    while(True):
        word = f.readline().replace('\n', '')
        if not word:
            if not new_sentence:
                break
            new_sentences.append(new_sentence)
            # print(new_sentence)
            new_sentence = []
        else:
            #print(word)
            subword=word.split('/')
            if(len(subword))==1:
                continue
            symbol=subword[0]
            tag=subword[1]
            symbols.add(symbol)
            tags.add(tag)
            new_sentence.append((symbol, tag))
            if len(symbol)<=0:
                continue
            if symbol[0]>='a' and symbol[0]<='z':
                num_pinyin=num_pinyin+1
                for i in range(len(pinyin_list)):
                    if pinyin_list[i][0]==symbol:
                        for j in range(len(pinyin_list[i][1])):
                            if tag==pinyin_list[i][1][j]:
                                pinyin_pro[i][1][j]=pinyin_pro[i][1][j]+1
#print(new_sentences)

data=new_sentences

#构建hmm模型
tag_set = unique_list(tag for sent in data for (word,tag) in sent)
#print(len(tag_set))
symbols = unique_list(word for sent in data for (word,tag) in sent)
#print(len(symbols))

trainer = nltk.tag.HiddenMarkovModelTrainer(tag_set, symbols)

#训练
#print(len(data))
#hmm=trainer.train_supervised(data[1:int(len(data)/1000)])
hmm=trainer.train_supervised(data)

print('训练完毕，开始生成GUI')

entry1=[]
entry2=[]
entry3=[]
pinyin_ori=[]
res_len=0
cur=0
local=0
able_list=[]
flag=1
path_list=[]
one_able=[]
def general():
    global cur
    global local
    global res_len
    global pinyin_ori
    global able_list
    global flag
    global path_list
    global one_able
    entry2.delete(0,END)
    pinyin=entry1.get()
    pinyin_ori=pinyin
    if len(pinyin)==0:
        entry2.insert(0,pinyin_ori)
        return
    
    #拼音分割，并且单拼音单独处理
    pinyin=pinyin.split(' ')
    if len(pinyin)==1:
        #需要补充代码
        able_list=[]
        local=0
        for i in range(len(pinyin_list)):
            if pinyin[0]==pinyin_list[i][0]:
                local=i
                for j in range(len(pinyin_list[i][1])):
                    able_list.append((j,pinyin_pro[i][1][j]))
        able_list=sorted(able_list,key=itemgetter(1),reverse=True)
        #print(len(one_able))
        res_len=len(able_list)
        if res_len==0:
            entry2.insert(0,pinyin_ori)
            return
        cur=0
        entry2.insert(0,pinyin_ori)
        flag=1
        return

    #获取全部可能路径
    flag=2
    able_list=[]
    path_list=able_path(pinyin,pinyin_list)
    
    #返回空串（有非拼音），直接输出
    if len(path_list)==0:
        entry2.insert(0,pinyin_ori)
        return

    #计算可能性并排序
    for i in range(len(path_list)):
        res=hmm.probability(path_list[i])
        #启用减少选项
        #if res==0:
        #    continue
        able_list.append((i,res))
    able_list=sorted(able_list,key=itemgetter(1),reverse=True)
    res_len=len(able_list)
    cur=0
    entry2.insert(0,pinyin_ori)

def next_path():
    global cur
    global local
    global res_len
    global pinyin_ori
    global able_list
    global flag
    global path_list
    global one_able
    if res_len>cur:
        entry2.delete(0,END)
        if flag==1:
            entry2.insert(0,pinyin_list[local][1][able_list[cur][0]])
        else:
            a_path=[]
            for j in range(len(path_list[able_list[cur][0]])):
                a_path.append(path_list[able_list[cur][0]][j][1])
            a_path=''.join(a_path)
            entry2.insert(0,a_path)
        cur=cur+1

def print_text():
    text=entry2.get()
    text_ori=entry3.get()
    entry3.insert(len(text_ori),text)

#GUI
#初始化Tk()
myWindow = Tk()
#设置标题
myWindow.title('全拼')
#标签控件布局
Label(myWindow, text="输入拼音").grid(row=0)
Label(myWindow, text="生成结果").grid(row=1)
Label(myWindow, text="写入结果").grid(row=2)
#Entry控件布局
entry1=Entry(myWindow)
entry2=Entry(myWindow)
entry3=Entry(myWindow)
entry1.grid(row=0, column=1)
entry2.grid(row=1, column=1)
entry3.grid(row=2, column=1)
#Quit按钮退出；Run按钮打印计算结果
Button(myWindow, text='退出', command=myWindow.quit).grid(row=3, column=0,sticky=W, padx=5, pady=5)
Button(myWindow, text='生成结果', command=general).grid(row=3, column=1, sticky=W, padx=5, pady=5)
Button(myWindow, text='下一结果', command=next_path).grid(row=3, column=2, sticky=W, padx=5, pady=5)
Button(myWindow, text='写入结果', command=print_text).grid(row=3, column=3, sticky=W, padx=5, pady=5)
#进入消息循环
print('生成GUI成功')
myWindow.mainloop()
