## Install Elasticsearch

sudo 설치
```
apt-get update && apt-get -y install sudo
```

패키지 색인을 업데이트
```
sudo apt update
```

HTTPS를 통해 리포지토리에 액세스하는 데 필요한 apt-transport-https 패키지를 설치
```
sudo apt install apt-transport-https
```

OpenJDK 8 설치
```
sudo apt install openjdk-8-jdk
java -version  # openjdk version "1.8.0_191"
```

OpenPGP 암호화 툴 설치
```
apt-get install -y gnupg2
```

Elasticsearch 저장소의 GPG key를 사용해 설치 
```
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -  
```

Elasticsearch 저장소를 시스템에 추가
```
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
```

elasticsearch 설치
```
sudo apt update
sudo apt install elasticsearch  # elasticsearch (7.10.0 설치됨)
```

elasticsearch 시작
```
service elasticsearch start
```

경로 이동해서 nori 형태소분석기 설치
```
cd /usr/share/elasticsearch
bin/elasticsearch-plugin install analysis-nori
```

elasticsearch 재시작 (형태소분석기 설치 후 재시작이 필수적!)
```
service elasticsearch restart
```

curl 명령어 설치
```
sudo install curl
```

Elasticsearch가 실행 중인지 확인
```
curl "localhost:9200"
```

Python Elasticsearch Client 설치
```
pip install elasticsearch
```

5초마다 서버에 존재하는 인덱스변 문서 개수 조회
```
watch -n 5 curl -XGET localhost:9200/_cat/indices?v
```
