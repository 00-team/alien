
SPACER="======================================"
EG="🔷"

cd /alien/
source .env/bin/activate

OLD_COMMIT=$(git rev-parse HEAD)

echo "$EG update the source"
git pull
echo $SPACER

NEW_COMMIT=$(git rev-parse HEAD)

function check_diff {
    local file_has_changed=$(git diff --name-only $OLD_COMMIT...$NEW_COMMIT --exit-code $1)
    if [ -z "$file_has_changed" ]; then
        return 1
    else
        return 0
    fi
}

if check_diff "requirements.txt"; then
    echo "$EG install pip packages"
    pip install -r requirements.txt
    echo $SPACER
fi



if check_diff "athena/athena.service"; then
    echo "$EG update athena service"
    cp athena/athena.service /etc/systemd/system/ --force
    systemctl daemon-reload
    echo $SPACER
fi

if check_diff "athena/*"; then
    echo "$EG restart athena service"
    systemctl restart athena
    echo $SPACER
fi

if check_diff "twitter/*"; then
    echo "$EG restart twitter bots"
    systemctl restart fxhash.twt
    systemctl restart xix.twt
    echo $SPACER
fi


echo "Deploy is Done! ✅"

