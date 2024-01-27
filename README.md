# sbts

バグ管理システムの試作

## 起動

```
cp -r config-sample config
cp sbts_public_custom-sample.py sbts_public_custom.py
cp sample.env .env
docker compose build
docker compose up -d
```

## テスト

```
./run_tests_from_host.sh
```
