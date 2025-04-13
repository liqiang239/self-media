## 1. 进入至pack目录
确保manage.spec文件存在. (pyi-makespec -D manage.py生成)

## 2. venv初始化: 
```shell script
    python main.py init_venv
```

## 3. 激活venv: 
```shell script
    .\venv\Scripts\activate
```

## 4. 安装 requirements: 
```shell script
    python main.py install
```

## 4. 打包主流程(该流程会创建django超级用户, 需要手动输入账户密码): 
```shell script
    python main.py pack
```


## EXE相关命令
```shell script
    manage.exe cmd --爬 --user_data_dir=xx --driver_path=xx --headless # user_data_dir, driver_path, headless参数为可选

    manage.exe runserver --noreload 0.0.0.0:8000  # 运行服务端
```
