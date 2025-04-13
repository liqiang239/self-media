import pyperclip
import pandas
import io
import numpy

def 清空系统剪贴板():
    pyperclip.copy(' ')

def 读取系统剪贴板():
    text = pyperclip.paste()
    return text

def 解析kimi表格(text):
    '''
    >>> df = 解析kimi表格(txt1)
    >>> len(df)
    7
    >>> df.columns.tolist()
    [' 时间 ', ' 发言者 ', ' 内容 ']
    '''
    df = pandas.read_csv(io.StringIO(text.strip()), sep="|", header=0)
    filtered_columns = filter(lambda x:x.strip() and not x.strip().startswith('Unnamed:'), df.columns)
    df = df[list(filtered_columns)].copy()
    col = df.columns.tolist()[0]
    df[col] = df[col].apply(lambda x:numpy.nan if x.strip()=='---' else x)
    df = df.dropna(subset=[col], axis=0)
    return df

def 增加n行(df, n):
    tmp = pandas.DataFrame([{k:v for k,v in zip(df.columns, ['']*len(df.columns))}] * n, columns=df.columns)
    return pandas.concat([df, tmp])


if __name__ == '__main__':
    import doctest
    txt1 = '''| 时间 | 发言者 | 内容 | 
| --- | --- | --- | 
| 2023-10-15 09:30 | 家庭医生 | 您好呀！很高兴您添加我为好友，我是您的家庭医生，随时为您提供健康咨询。有什么不舒服的地方可以告诉我哦！ | 
| 2023-10-15 09:34 | 患者 | 医生您好，我最近有点不舒服，肚子疼了好几天，还拉肚子。 | 
| 2023-10-15 09:36 | 家庭医生 | 您好！感谢您的信任。您能描述一下腹痛的具体位置和性质吗？是绞痛还是隐痛？有没有伴随恶心、呕吐或其他症状？ | 
| 2023-10-15 09:39 | 患者 | 是隐隐的疼，偶尔有点绞痛，昨天还吐了一次，感觉有点恶心。 | 
| 2023-10-15 09:42 | 家庭医生 | 感谢您提供信息。建议您暂时避免进食油腻或刺激性食物，多喝水，观察症状是否缓解。如果疼痛加重或持续超过24小时，建议尽快来诊所进一步检查。 | 
| 2023-10-15 09:45 | 患者 | 好的，谢谢医生！我再观察一下。 | 
| 2023-10-15 09:47 | 家庭医生 | 不客气！如果需要进一步帮助，随时联系我。祝您早日康复！ | 

'''
    # df = 解析kimi表格(txt1)
    # print(df)
    print(doctest.testmod(verbose=False, report=False))
