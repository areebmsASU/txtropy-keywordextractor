mkdir secrets
mkdir -p ~/.ssh/
touch ~/.ssh/known_hosts

gpg --quiet --batch --yes --decrypt --passphrase="$PEM_DECRYPT_PASSPHRASE" \
--output secrets/git.pem ./.github/git.pem.gpg

chmod 600 secrets/git.pem
eval `ssh-agent -s`
ssh-keyscan -t rsa -H 3.99.1.152 >> ~/.ssh/known_hosts
ssh-add secrets/git.pem

git remote add lightsail ubuntu@3.99.1.152:~/keywordextractor.git
git push lightsail --force