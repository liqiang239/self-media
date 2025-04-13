'''
Created on 2024 Nov 24

@author: Winston
'''
import re


ptn_txt_count = re.compile('\[.{1,2}\]')

def 清理表情(txt):
    return ptn_txt_count.sub('', txt).strip()


def 统计字数(txt):
    '''
    >>> 统计字数('123')
    3
    >>> 统计字数('[23]')
    0
    >>> 统计字数('[231]')
    5
    >>> 统计字数('[占美]')
    0
    >>> 统计字数('[占]')
    0
    '''
    return len(清理表情(txt))
 

ptn_lines = re.compile('[男女]：')

def split_smart(txt):
    '''
    >>> split_smart('男：各位听众大家好，欢迎收听聊生活电台。真快呀。女：可不是嘛。。男：啥消息呀？女：台媒体人')
    ['各位听众大家好，欢迎收听聊生活电台。真快呀。', '可不是嘛。。', '啥消息呀？', '台媒体人']
    '''
    l = map(lambda x:x.strip(), ptn_lines.split(txt))
    l = filter(lambda x:x, l)
    return list(l)


def produce_triple(l):
    '''
    >>> r = produce_triple(['1', '2', '3', '4', '5', '6','7'])
    >>> r[0]
    ['1', '3', '5', '7']
    >>> r[1]
    ['2', '4', '6']
    >>> r[2]
    [{'name': 'male', 'index': 0}, {'name': 'female', 'index': 0}, {'name': 'male', 'index': 1}, {'name': 'female', 'index': 1}, {'name': 'male', 'index': 2}, {'name': 'female', 'index': 2}, {'name': 'male', 'index': 3}]
    '''
    total = len(l)
    male = [l[i] for i in range(0, total, 2)]
    femal = [l[i] for i in range(1, total, 2)]
    index = []
    name = ('male','female')
    for i in range(total):
        tmp = {'name':name[i%2], 
               'index':i//2,
               }
        index.append(tmp)
    
    return male, femal, index




if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    tmp1 = '''男：各位听众大家好，欢迎收听聊生活电台。真快呀。女：可不是嘛。。男：啥消息呀？女：台媒体人'''