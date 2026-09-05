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

Результаты выше относятся к уже выполненной локальной проверке baseline. Этот
README не заявляет наличие нового CI workflow или прохождение GitHub Actions.

Не проверены: реальный vLLM, качество/tool calling выбранной модели, интерактивные
сценарии TUI целиком, deployed CNI/network capture, image/SBOM scan, SSO, SIEM,
изоляция между пользователями и production gateway. Критерии — ACCEPTANCE.md.

## Опубликованные файлы

Патчи сохранены без изменений относительно проверенного комплекта. Документы внутри
патча 0004 отражают момент подготовки до публикации; актуальная инструкция для
этого форка находится в данном README. SHA256SUMS проверяет комплект в этой папке.
