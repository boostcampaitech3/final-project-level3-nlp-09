# 회의록 Open-domain Question Answering
> 네이버 부스트캠프 AI Tech 3기 최종 프로젝트


## Members
김태일|문찬국|이재학|하성진|한나연|
:-:|:-:|:-:|:-:|:-:
<img src='https://user-images.githubusercontent.com/46811558/162856318-13a478a3-ad96-4e1f-ad24-3e0a92b81eb7.jpg' height=100 width=100px></img>|<img src='https://user-images.githubusercontent.com/46811558/162856364-d71ea54c-31df-433f-8968-93ade6da30b5.jpg' height=100 width=100px></img>|<img src='https://user-images.githubusercontent.com/46811558/157460675-9ee90b62-7a39-4542-893d-00eafdb0fd95.jpg' height=100 width=100px></img>|<img src='https://user-images.githubusercontent.com/46811558/162856411-70847d72-1dbc-4389-b6e5-bcacba95b2ab.jpg' height=100 width=100px></img>|<img src='https://user-images.githubusercontent.com/46811558/162856463-e10110b7-7e68-4469-9418-6165108a3885.jpg' height=100 width=100px></img>
[detailTales](https://github.com/detailTales)|[nonegom](https://github.com/nonegom)|[wogkr810](https://github.com/wogkr810)|[maxha97](https://github.com/maxha97)|[HanNayeoniee](https://github.com/HanNayeoniee)
gimty97@gmail.com|fksl9959@naver.com |jaehahk810@naver.com|maxha97@naver.com |nayeon2.han@gmail.com

## Installation
```
# 파이썬 버전 확인 (3.8.5 확인)
python3 --version 

# venv 설치
sudo apt-get install python3-venv 

# 가상환경 생성하기
python3 -m venv [venv_name] 

# 가상환경 활성화(생성한 가상환경 폴더가 있는 경로에서 활성화 해야 함)
source [venv_name]/bin/activate 

# 라이브러리 설치
pip install -r requirements.txt

# 가상환경 종료
deactivate
```


## Commit Rule
```
- feat      : 새로운 기능 추가
- debug     : 버그 수정
- docs      : 문서 수정
- style     : 코드 formatting, 세미콜론(;) 누락, 코드 변경이 없는 경우
- refactor  : 코드 리팩토링
- test      : 테스트 코드, 리팩토링 테스트 코드 추가
- chore     : 빌드 업무 수정, 패키지 매니저 수정
- exp       : 실험 진행
- merge     : 코드 합칠 경우
- anno      : 주석 작업
- etc       : 기타
```