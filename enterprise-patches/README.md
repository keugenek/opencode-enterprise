# OpenCode Enterprise: серия патчей

Дата review: 2026-09-05. Upstream: https://github.com/anomalyco/opencode, релиз v1.18.29,
точный baseline: `16747470f976aca3d362ad730bcd3fe82ecc2c9a`.

Это проверенный сборкой кандидат Linux CLI/TUI для дальнейшей enterprise-приёмки.
Поддерживаются локальные CLI/TUI и `run`, один внутренний OpenAI-compatible
Chat Completions endpoint и одна модель. Desktop, Web, ACP, облачные аккаунты,
внешние плагины/MCP и экспериментальный V2 не входят в поддерживаемый профиль.
Это намеренно ограниченный профиль; полноценный универсальный дистрибутив требует
отдельно проектировать управляемые исключения, внутренний каталог инструментов и аудит.

## Применение к своему форку

В чистом checkout своего форка, при наличии upstream baseline:

```sh
git fetch origin
git fetch --no-tags https://github.com/anomalyco/opencode.git 16747470f976aca3d362ad730bcd3fe82ecc2c9a
# Run from the repository root on the branch containing enterprise-patches/.
patch_dir="$(pwd)/enterprise-patches/patches"
git worktree add -b enterprise-runtime ../opencode-enterprise-runtime 16747470f976aca3d362ad730bcd3fe82ecc2c9a
cd ../opencode-enterprise-runtime
git am "$patch_dir"/000*.patch
```

Серия: (1) доверенная конфигурация и одна модель; (2) транспорт и запреты обхода;
(3) отключение удалённой телеметрии/sharing/cloud entrypoints; (4) тесты и документация.
Не применять вслепую к другой версии. После обновления повторить review изменённых
путей выполнения и все release gates. Целевой форк: https://github.com/keugenek/opencode-enterprise.
Эта директория содержит patch series; само её добавление в dev не включает
enterprise-ограничения в исходниках. Для сборки примените серию к точному baseline.

## Сборка

В контролируемом CI нужны Bun 1.3.14, зависимости из lockfile и одобренные зеркала.
Сборка сама по себе не является offline: скачивание зависимостей/ассетов выполняется
на этапе подготовки. Runtime не должен скачивать инструменты.

```sh
bun install --frozen-lockfile --ignore-scripts
bun run --cwd packages/core fix-node-pty
cd packages/opencode
bun run script/build.ts --single --skip-install --skip-embed-web-ui
```

Администратор задаёт реальный endpoint, model ID и лимиты в
`enterprise/enterprise.example.json`. Он копируется в образ как
`/etc/opencode/enterprise.json`: root:root, 0644; родители root-owned и без записи
для группы/остальных; root filesystem read-only. Отсутствующая/некорректная политика
останавливает программу, включая `--version`. Для встроенного smoke test сборки
нужен этот файл в изолированном CI-контейнере. Не меняйте policy на рабочем хосте
ради сборки. Пример — заглушка, он не указывает на ваш действующий inference.

Для x64 скопируйте `packages/opencode/dist/opencode-linux-x64/bin/opencode` в
`enterprise/opencode`, затем соберите Dockerfile с `RUNTIME_IMAGE`, закреплённым
по digest. Бинарник и образ должны быть подписаны и проверены вашим CI.
В Kubernetes-шаблоне замените image digest, адрес gateway, имя TLS и лимиты;
сначала примените NetworkPolicy. Шаблон не был развёрнут в этой работе.

Клиент не передаёт личные bearer tokens: аутентификация workload должна обеспечиваться
внутренним gateway/mesh. Прочитайте GATEWAY-CONTRACT.md перед подключением vLLM.

## Проверено

- 32 теста: enterprise policy/transport и observability; 0 failures, 52 assertions.
- `bun typecheck` в packages/core, packages/opencode, packages/tui.
- Linux x64 binary собран; build smoke test `--version` прошёл.
- CLI `models` с враждебным OPENCODE_CONFIG_CONTENT, облачной моделью и произвольным
  provider npm вернул только `enterprise/enterprise-coder`.

### Покрытие тестов патча 0004

| Файл после применения патчей | Проверки |
|---|---|
| `packages/core/test/enterprise/policy.test.ts` (новый) | Схема политики и конфигурации OpenCode; допустимый HTTPS endpoint и model ID; независимость объектов конфигурации; обязательные запреты инструментов; точный маршрут/model в inference-запросе; блокировка подмены URL, не-JSON body и remote media; отсутствие OTLP exporter/identity attributes |
| `packages/core/test/effect/observability.test.ts` (обновлён) | Отсутствие экспорта идентификаторов и OTEL attributes; сохранение работы локального файлового логгера |

32 — общее число прошедших тестов этих двух файлов, а не число полностью новых
тестов. Проверка внедрённого облачного конфига выполнена отдельно как CLI smoke test.

Запуск после применения серии и установки зависимостей, из корня **патченного**
worktree:

```sh
(cd packages/core && bun test test/enterprise/policy.test.ts test/effect/observability.test.ts)
(cd packages/core && bun typecheck)
(cd packages/opencode && bun typecheck)
(cd packages/tui && bun typecheck)
```

Тесты и typecheck запускаются из каталогов пакетов. Для проверки целостности
опубликованного комплекта до применения патчей:

```sh
(cd enterprise-patches && sha256sum -c SHA256SUMS)
```

Результаты выше относятся к уже выполненной локальной проверке baseline. Эти
локальные результаты не являются подтверждением прохождения GitHub Actions;
статус нового workflow проверяйте во вкладке Actions.

Не проверены: реальный vLLM, качество/tool calling выбранной модели, интерактивные
сценарии TUI целиком, deployed CNI/network capture, image/SBOM scan, SSO, SIEM,
изоляция между пользователями и production gateway. Критерии — ACCEPTANCE.md.

## Опубликованные файлы

Патчи сохранены без изменений относительно проверенного комплекта. Документы внутри
патча 0004 отражают момент подготовки до публикации; актуальная инструкция для
этого форка находится в данном README. SHA256SUMS проверяет комплект в этой папке.

## CI/CD и релизные сборки

Workflow: [Enterprise build and release](../.github/workflows/enterprise-release.yml).
Он запускается на PR, изменяющих комплект/workflow, на соответствующих push в
`dev`/`enterprise-patches` и на тегах `enterprise-v*`. Ручной `workflow_dispatch`
доступен после появления workflow в default branch. Если GitHub отключил Actions
для нового форка, включите их во вкладке Actions репозитория.

Pipeline проверяет SHA256SUMS, создаёт отдельный worktree точного BASE_COMMIT,
при необходимости загружает точный baseline SHA из upstream (release-коммит может
отсутствовать в истории dev-форка), применяет четыре патча, устанавливает Bun 1.3.14 и зависимости по lockfile,
запускает 32 направленных теста и typecheck трёх пакетов. Затем он собирает Linux
x64/glibc (AVX2) CLI и проверяет бинарник: версия, игнорирование cloud config,
отказ для auto/yolo flags и остановка без администраторской политики.
Пример policy устанавливается только на одноразовый GitHub runner; реальные
адреса и credentials компании в CI не требуются и в бинарник не встраиваются.

Обычные сборки сохраняют артефакт `enterprise-linux-x64` на 14 дней. Тег вида
`enterprise-v1.18.29-rc.1` создаёт GitHub **prerelease** только после успешной
сборки и проверок. Публикация существующего релиза повторным запуском не перезаписывает
его: используйте новый RC-тег. Не перемещайте опубликованные теги.

Из проверенного checkout с этим workflow:

```sh
git tag -a enterprise-v1.18.29-rc.1 -m 'Enterprise candidate 1.18.29-rc.1'
git push origin enterprise-v1.18.29-rc.1
```

Assets: архив бинарника с инструкцией и LICENSE, архив патчей, архив точных
патченных исходников, `build-manifest.json` и `SHA256SUMS`. Manifest фиксирует
коммит дистрибутива, baseline, tree hash исходников, версию Bun и хеши патчей/lockfile.
SHA-256 подтверждает целостность скачанных файлов; это не криптографическая подпись
издателя и не SBOM. Attestation/signing и сканирование конечного контейнера нужно
добавить в корпоративном release процессе.

Build job имеет только `contents: read`; публикация выполняется отдельным job с
`contents: write` только для push релизного тега в этом форке. Actions закреплены
по commit SHA, checkout не сохраняет token в Git-конфиге. Используются GitHub-hosted
Ubuntu runners; сборка требует интернета для зависимостей. Для закрытого CI нужны
одобренные зеркала и отдельный доверенный runner, недоступный непроверенным PR.

Автоматического production deploy и stable-release promotion нет до выполнения
[ACCEPTANCE.md](ACCEPTANCE.md). macOS/Windows/ARM и контейнерные образы данным
workflow не выпускаются. Унаследованные upstream workflow — отдельные процессы;
статус enterprise-сборки смотрите именно в `Enterprise build and release`.
