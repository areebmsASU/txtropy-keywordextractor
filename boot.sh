# Create and activate virtual Env
sudo apt-get update
sudo apt install -y python3.10-venv
sudo apt install -y postgresql
sudo apt install -y cron
cd /home/ubuntu
python3 -m venv .venv
sudo chown -R ubuntu .venv/

# Placeholder for vars.
touch vars.sh
chmod +x vars.sh


# Create git dir
mkdir keywordextractor.git
mkdir keywordextractor
sudo chown -R ubuntu /home/ubuntu/keywordextractor.git/
sudo chown -R ubuntu /home/ubuntu/keywordextractor/
cd keywordextractor.git
git config --global init.defaultBranch main
git init --bare

# Create post receive
touch /home/ubuntu/keywordextractor.git/hooks/post-receive
cat > /home/ubuntu/keywordextractor.git/hooks/post-receive <<- "EOF"
#!/bin/bash
cd ~
git --work-tree="keywordextractor" --git-dir="keywordextractor.git" checkout -f main
source .venv/bin/activate
cd keywordextractor
pip install -r requirements.txt
deactivate
EOF
chmod +x /home/ubuntu/keywordextractor.git/hooks/post-receive

touch /etc/cron.hourly/run_routine.sh
cat > /etc/cron.hourly/run_routine.sh <<- "EOF"
echo “Routine started at $(date)” >> $HOME/log.txt
cd ~
source vars.sh
source .venv/bin/activate
cd keywordextractor
python manage.py count_chunk_vocab >> $HOME/log.txt
timeout 55m python manage.py load_chunks && python manage.py get_spacy_tokens >> $HOME/log.txt
echo “Routine completed at $(date)” >> $HOME/log.txt
EOF
chmod +x /etc/cron.hourly/run_routine.sh
