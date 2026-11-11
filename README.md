# Cache Project — прокси с кешированием на Valkey

Учебный DevOps-проект: развёртывание приложения из четырёх компонентов на двух виртуальных машинах, сборка пакетов DEB/RPM, запуск через systemd и настройка сетевого доступа.

## Архитектура

```text
Клиент
   |
   | HTTP :5000
   v
CentOS Stream 10 — 192.168.97.114
   Flask Proxy (cache-api)
      |                |
      | cache hit      | cache miss, HTTP :8080
      v                v
   Valkey          Ubuntu — 192.168.96.249
   127.0.0.1:6379     Go Backend (backend-api)
                          |
                          | TCP :5432
                          v
                       PostgreSQL 16
                       127.0.0.1:5432
```

1. Клиент обращается к `GET /user?id=<id>` на Flask Proxy.
2. Proxy ищет пользователя в Valkey. При попадании в кеш возвращает данные с `"cached": true`.
3. Если ключа нет, Proxy запрашивает Go Backend, который читает данные из PostgreSQL.
4. Proxy сохраняет ответ в Valkey на **60 секунд** и возвращает `"cached": false`.

Вместо Redis используется совместимый с его протоколом **Valkey** — замена согласована для учебного задания.

## Компоненты

| ВМ | Компоненты | Назначение |
| --- | --- | --- |
| Ubuntu, `192.168.96.249` | PostgreSQL 16, Go Backend | Хранение данных и API на `:8080` |
| CentOS Stream 10, `192.168.97.114` | Valkey, Python Flask Proxy | Кеширование и публичная точка входа на `:5000` |

IP-адреса приведены для учебного стенда. При развёртывании в другой сети их нужно заменить в настройках.

## Структура репозитория

```text
backend-app/       Исходники Go Backend и go.mod/go.sum
backend-package/   Структура Debian-пакета (DEBIAN/, etc/, usr/)
firewall/rules.sh   Правила nftables для Backend на Ubuntu
proxy/SOURCES/     Python-приложение, конфигурация и systemd unit
proxy/SPECS/       RPM-спецификация cache-api.spec
screenshots/        Скриншоты проверок для отчёта
README.md          Документация проекта
```

## Сборка и установка Backend (Ubuntu)

Требуются Go, `dpkg-deb` и установленный PostgreSQL 15+ (в стенде — PostgreSQL 16). Перед запуском Backend необходимо создать БД `test`, пользователя приложения с доступом к ней и таблицу `users`:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    email VARCHAR(100)
);
```

Таблица заполняется 20 записями из CSV, предоставленного к заданию (сам CSV в данный репозиторий не включён). Параметры пользователя БД должны соответствовать `/etc/backend-api/config.yaml`.

Из корня клонированного репозитория:

```bash
cd backend-app
go build -o ../backend-package/usr/bin/backend-api .
cd ..
dpkg-deb --build backend-package backend-api.deb
sudo apt install ./backend-api.deb
```

Параметры подключения к базе находятся в `/etc/backend-api/config.yaml`. Для этого стенда PostgreSQL слушает только `127.0.0.1:5432`; Backend и PostgreSQL работают на одной ВМ.

```bash
sudo systemctl enable --now backend-api.service
systemctl status backend-api.service
```

Проверка на Ubuntu:

```bash
curl 'http://127.0.0.1:8080/user?id=5'
```

## Сборка и установка Proxy (CentOS)

Необходимы подключённые репозитории CentOS и EPEL 10, Valkey, системный Python, зависимости Python и инструменты сборки RPM.

```bash
sudo dnf install rpm-build rpmdevtools \
    python3 python3-flask python3-redis python3-requests python3-pyyaml
rpmdev-setuptree
```

Из корня репозитория скопировать файлы в стандартное дерево сборки RPM:

```bash
cp proxy/SOURCES/* ~/rpmbuild/SOURCES/
cp proxy/SPECS/cache-api.spec ~/rpmbuild/SPECS/
rpmbuild -bb ~/rpmbuild/SPECS/cache-api.spec
```

Установить созданный пакет (имя файла зависит от `Version` и `Release` в спецификации):

```bash
sudo dnf install ~/rpmbuild/RPMS/noarch/cache-api-*.rpm
sudo systemctl enable --now valkey.service cache-api.service
systemctl status cache-api.service
```

RPM устанавливает приложение в `/usr/libexec/cache-api/`, конфигурацию в `/etc/cache-api/config.yaml` и unit `cache-api.service`. Прокси использует системный Python, а не локальный `.venv`.

Рабочие параметры учебного стенда: Valkey — `127.0.0.1:6379`, Backend — `192.168.96.249:8080`, Flask — `0.0.0.0:5000`.


