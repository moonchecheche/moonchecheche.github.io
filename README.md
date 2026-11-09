# 어제오늘날씨 공식 소개 사이트

기존 GitHub Pages / Jekyll 사이트다. 앱·언어별 소개, 사용법, 고객지원과 개인정보 처리방침을 제공한다.

언어별 데이터와 페이지는 `../weather`의 스토어 원고에서 만든다.

```sh
cd /Users/medmemara/workspace/weather
npm run sync:discovery-site -- --site-root /Users/medmemara/workspace/yesterday-today-weather
```

Jekyll 3.10으로 빌드한 뒤 아래 검사를 실행한다.

```sh
jekyll build
python3 scripts/check-seo.py _site
```

검사는 22개 페이지의 대표 주소, 17개 언어 연결, 앱 정보, 설치·내부 링크와 사이트맵을 확인한다. `_config.yml`의 Google 소유권 확인 표식은 공개 정보이며, 소유권을 유지하려면 남겨 둬야 한다. 인증 비밀키는 이 저장소에 두지 않는다.

`sitemap.xml`과 공식 지원 형식인 `sitemap.txt`는 같은 대표 주소 목록을 낸다. 검사기는 두 목록이 공개 페이지와 일치하는지도 확인한다. 파일 검사가 통과해도 Search Console의 수집 완료와 검색 노출은 별도로 확인해야 한다.

`sitemap-pages.xml`은 기존 사이트맵 주소만 처리 대기에 남는지 확인하기 위한 별도 경로다. 주 XML과 같은 템플릿으로 만들어 바이트가 같아야 한다. 이 경로의 제출 접수나 파일 접근 성공을 사이트맵 처리 성공으로 기록하지 않는다.

배포는 기존 `main` 브랜치의 GitHub Pages 경로를 사용한다. 게시 뒤 정확한 커밋의 Pages 빌드와 공개 페이지를 확인한다. 앱 설치 파일 배포와는 별개다.

이용약관은 `terms.md`에서 관리하며 `/terms`로 공개합니다. 한국어와 영어를 함께 제공하고, 모든 페이지의 하단에서 연결합니다. Google Play의 앱 수준 판매자 신고에 이 주소를 사용합니다.
