# GitHub 저장소 설정 가이드

로컬 프로젝트를 GitHub 원격 저장소에 연결하고 업로드하기 위해 사용한 명령어들을 설명합니다.

---

## 1. Git 저장소 초기화

```bash
git init
```

- 현재 디렉토리에 새로운 Git 저장소를 생성한다.
- 실행하면 `.git` 폴더가 생성되며, 이후부터 버전 관리가 가능해진다.
- 프로젝트당 **최초 1회**만 실행하면 된다.

---

## 2. 원격 저장소 연결

```bash
git remote add origin <원격 저장소 URL>
```

- 로컬 저장소와 GitHub 원격 저장소를 연결한다.
- `origin`은 원격 저장소의 별칭(alias)이다. 관례적으로 `origin`을 사용한다.
- `<원격 저장소 URL>`에는 GitHub에서 생성한 저장소의 URL을 입력한다.

**사용 예시:**

```bash
git remote add origin https://github.com/ljs535-source/BigDataAnalysis.git
```

**관련 명령어:**

| 명령어 | 설명 |
|--------|------|
| `git remote -v` | 연결된 원격 저장소 목록 확인 |
| `git remote remove origin` | 원격 저장소 연결 해제 |
| `git remote set-url origin <새 URL>` | 원격 저장소 URL 변경 |

---

## 3. 파일 스테이징 (커밋 준비)

```bash
git add <파일명>
```

- 변경된 파일을 스테이징 영역(staging area)에 추가한다.
- 스테이징된 파일만 커밋에 포함된다.

**사용 예시:**

```bash
git add 1.html          # 특정 파일 추가
git add .               # 현재 디렉토리의 모든 변경 파일 추가
git add *.html          # 모든 HTML 파일 추가
```

---

## 4. 커밋 (변경 사항 저장)

```bash
git commit -m "커밋 메시지"
```

- 스테이징된 파일들을 하나의 커밋으로 저장한다.
- `-m` 옵션 뒤에 변경 내용을 설명하는 메시지를 작성한다.
- 커밋 메시지는 **변경 내용을 명확하게** 작성하는 것이 좋다.

**사용 예시:**

```bash
git commit -m "add 1.html"
```

---

## 5. 브랜치 이름 변경

```bash
git branch -M main
```

- 현재 브랜치의 이름을 `main`으로 변경한다.
- `-M` 옵션은 강제 이름 변경(이미 같은 이름의 브랜치가 있어도 덮어쓰기)을 의미한다.
- Git 기본 브랜치명이 `master`로 생성되지만, GitHub는 `main`을 기본으로 사용하므로 이름을 맞춰주는 것이 좋다.

---

## 6. 원격 저장소에 업로드 (Push)

```bash
git push -u origin main
```

- 로컬의 커밋을 원격 저장소(`origin`)의 `main` 브랜치에 업로드한다.
- `-u` 옵션은 upstream을 설정하여, 이후에는 `git push`만으로 push할 수 있게 해준다.

**이후 push 시:**

```bash
git push                # -u 설정 이후에는 이것만으로 충분
```

---

## 전체 흐름 요약

```bash
# 1. 저장소 초기화
git init

# 2. 원격 저장소 연결
git remote add origin https://github.com/사용자명/저장소명.git

# 3. 파일 스테이징
git add .

# 4. 커밋
git commit -m "first commit"

# 5. 브랜치 이름 변경
git branch -M main

# 6. 원격 저장소에 push
git push -u origin main
```

---

## 자주 발생하는 오류

### `fatal: not a git repository`

- **원인:** `git init`을 실행하지 않은 상태에서 git 명령어를 사용한 경우
- **해결:** `git init`으로 저장소를 먼저 초기화한다.

### `error: src refspec main does not match any`

- **원인:** 현재 브랜치 이름이 `main`이 아닌 경우 (예: `master`)
- **해결:** `git branch -M main`으로 브랜치 이름을 변경한다.

### `remote: Permission denied`

- **원인:** 현재 로그인된 GitHub 계정에 해당 저장소의 push 권한이 없는 경우
- **해결:** 저장소 소유자가 Settings > Collaborators에서 권한을 부여하거나, 올바른 계정으로 로그인한다.
