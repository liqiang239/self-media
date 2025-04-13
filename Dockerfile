FROM python:3.9.12

COPY deploy/sources.list /etc/apt/sources.list

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32

RUN apt-get update
RUN apt-get upgrade -y
# caidao
#RUN apt-get install -y libx11-xcb1
#RUN apt-get install -y  libgl1-mesa-glx


COPY src/ /data/xxx/src
# COPY caidao /data/caidao

WORKDIR /data/xxx/src

RUN pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
CMD ["bash", "start.sh"]

