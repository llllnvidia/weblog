FROM daocloud.io/library/ubuntu
MAINTAINER "linw" <815750986@qq.com>

RUN apt-get update && \
    apt-get install -y nginx build-essential python python-pip npm git wget && \
    apt-get clean all

RUN npm install -g n && \
    n stable && \
    npm install -g bower

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN pip install --upgrade pip && \
    pip install supervisor gunicorn

ADD supervisord.conf /etc/supervisord.conf

RUN mkdir -p /etc/supervisor.conf.d && \
    mkdir -p /var/log/supervisor && \
    mkdir -p /usr/src/app && mkdir -p /var/log/gunicorn

WORKDIR /usr/src/app

ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/app
RUN bower install --allow-root

RUN ln -s /usr/src/app/weblog_nginx.conf /etc/nginx/sites-enabled

EXPOSE 8000

CMD ["/usr/local/bin/supervisord", "-n"]
