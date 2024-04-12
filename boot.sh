# Create and activate virtual Env
sudo apt-get update
sudo apt install -y postgresql
sudo apt install -y redis
python -m venv /home/bitnami/.venv

# Placeholder for vars.
touch vars.py

# Create git dir
mkdir keywordextractor.git
mkdir keywordextractor
sudo chown -R bitnami keywordextractor.git/
sudo chown -R bitnami keywordextractor/
cd keywordextractor.git
git config --global init.defaultBranch main
git init --bare

# Create post receive
touch /home/bitnami/keywordextractor.git/hooks/post-receive
cat > /home/bitnami/keywordextractor.git/hooks/post-receive <<- "EOF"
#!/bin/bash
cd ~
git --work-tree="keywordextractor" --git-dir="keywordextractor.git" checkout -f main
source .venv/bin/activate
cd keywordextractor
pip install -r requirements.txt
deactivate
sudo /opt/bitnami/ctlscript.sh restart apache
EOF
chmod +x /home/bitnami/keywordextractor.git/hooks/post-receive

# Apache Server
touch /opt/bitnami/apache/conf/vhosts/keywordextractor-http-vhost.conf
cat > /opt/bitnami/apache/conf/vhosts/keywordextractor-http-vhost.conf <<- "EOF"
<IfDefine !IS_keywordextractor_LOADED>
    Define IS_keywordextractor_LOADED
    WSGIDaemonProcess keywordextractor python-home=/home/bitnami/.venv python-path=/home/bitnami/keywordextractor
</IfDefine>
<VirtualHost 127.0.0.1:80 _default_:80>
ServerAlias *
WSGIProcessGroup keywordextractor
WSGIScriptAlias / /home/bitnami/keywordextractor/keywordextractor/wsgi.py
<Directory /home/bitnami/keywordextractor/keywordextractor>
    <Files wsgi.py>
    Require all granted
    </Files>
</Directory>
</VirtualHost>
EOF

touch /opt/bitnami/apache/conf/vhosts/keywordextractor-https-vhost.conf
cat > /opt/bitnami/apache/conf/vhosts/keywordextractor-https-vhost.conf <<- "EOF"
<IfDefine !IS_keywordextractor_LOADED>
    Define IS_keywordextractor_LOADED
    WSGIDaemonProcess keywordextractor python-home=/home/bitnami/.venv python-path=/home/bitnami/keywordextractor
</IfDefine>
<VirtualHost 127.0.0.1:443 _default_:443>
ServerAlias *
SSLEngine on
SSLCertificateFile "/opt/bitnami/apache/conf/bitnami/certs/server.crt"
SSLCertificateKeyFile "/opt/bitnami/apache/conf/bitnami/certs/server.key"
WSGIProcessGroup keywordextractor
WSGIScriptAlias / /home/bitnami/keywordextractor/keywordextractor/wsgi.py
<Directory /home/bitnami/keywordextractor/keywordextractor>
    <Files wsgi.py>
    Require all granted
    </Files>
</Directory>
</VirtualHost>
EOF

sudo chown -R bitnami /home/bitnami/.venv
sudo chown -R bitnami /home/bitnami/keywordextractor
sudo chown -R bitnami /home/bitnami/keywordextractor.git
# celery -A keywordextractor worker -l INFO
