# Security review OpenCode enterprise candidate

Первоначальный review: 2026-09-05; дополнения: 2026-09-17 и 2026-09-21. Baseline v1.18.29 / 16747470f976aca3d362ad730bcd3fe82ecc2c9a.
Метод: чтение критических путей исходного кода, патчи, направленные тесты,
проверка типов, сборка и CLI smoke test. Это не независимый pentest, не полный
аудит всех зависимостей и не сертификация enterprise-ready.

## Граница доверия

Цель: пользователь и файлы проекта не могут подключить другой provider/model
или изменить фиксированный endpoint в патченном CLI/TUI и нативном Windows
Desktop профилях. Desktop требует отдельной проверки локального транспорта,
Electron renderer/IPC и полного установочного пакета.
Доверены администратор образа, root-owned policy, CI, kernel/CNI и внутренний gateway.
Root/администратор платформы может изменить программу; патчи этого не предотвращают.
Разработчик с обычным доступом к своему компьютеру тоже может запустить другой клиент.
Поэтому обязательны управляемый runtime и сетевые ограничения вне процесса.

Сам upstream прямо описывает OpenCode как не являющийся sandbox; permission prompts
не заменяют изоляцию ОС. Это исходное ограничение продукта, а не установленная
уязвимость данного релиза. [Upstream security policy](https://github.com/anomalyco/opencode/security).

## Находки и меры

| Риск | Где проверено / изменение | Остаток |
|---|---|---|
| Критический: shell обходит запрет облачных моделей | NetworkPolicy, непривилегированный контейнер, отсутствие host mounts и token | CNI и IPv6 надо проверять на реальном кластере; один YAML не доказательство |
| Высокий: конфиг проекта/env добавляет provider, плагины или меняет URL | config/config.ts: ранний trusted-config путь до разрешения пользовательских конфигов и плагинов; mutations запрещены | Root policy — доверенная административная поверхность |
| Высокий: альтернативная модель для summary/subagent | enterprise/policy.ts фиксирует model и small_model; provider/provider.ts проверяет выбор перед SDK/cache | Реальные compaction/subagent workflows с vLLM ещё требуют теста |
| Высокий: redirect/custom fetch/header уводит inference | enterprise/transport.ts фиксирует HTTPS route, POST/model, запрещает redirect и remote media, реконструирует headers | DNS/IP enforce снаружи; gateway должен запретить cloud fallback и произвольные модели |
| Высокий: динамический код plugins/MCP/LSP/formatter/skills | trusted config + plugin early return + TUI config defaults + downloads disabled + central denies | Утрачена соответствующая функциональность; не добавлять исключения через проектный конфиг |
| Высокий: внешняя передача сессий | share-next.ts: disabled и блокирующий request guard; CLI cloud/web/import/attach/serve/ACP entrypoints удалены из регистрации | Native Windows Desktop выпускается только с отдельным hardening-патчем; другие upstream web/desktop profiles не включены |
| Высокий: внешняя наблюдаемость/идентификаторы | core/observability/otlp.ts заменён no-op, нет OTLP exporters/attributes; конфиг OTEL отключён | Локальные логи и история остаются чувствительными; это не удаление всех данных пользователя |
| Средний: модели/обновления как неявный egress | models-dev runtime — пустой каталог; generate.ts не скачивает каталог; autoupdate выключен | CI downloads остаются, нужны зеркала и проверка supply chain |
| Высокий: обход согласований | CLI auto/yolo flags отвергаются; TUI normal-only; deny floor применяется к сохранённым разрешениям/субагентам | Ask/allow для shell не является проверкой безопасности команды |
| Высокий: experimental execution path | runtime flags выключены; V2 provider.use запрещён fail-closed | V2 функциональность не поддерживается данным профилем |
| Высокий: чтение секретов/подмена сборки | read-only image, non-root, отдельный workspace, без SA token | Secret-free workspace и RBAC обеспечиваются платформой; модель может читать доступные ей файлы |

## Что удалено и что не следует обещать

Удалён действующий OTLP export из core. Отключены sharing, public model catalog,
autoupdate, встроенные auth/cloud plugins и перечисленные сетевые функции в
поддерживаемом CLI. Это не доказательство отсутствия любой телеметрии во всём
монорепозитории, всех сторонних SDK или в запущенных shell-командах. Cloud SDK
dependencies физически не вычищены из lockfile: нужен отдельный анализ reachability
и SBOM готового бинарника/образа. Для native Windows Desktop нужен отдельный
review Electron runtime, renderer/IPC, локального backend и native dependencies.
Linux/macOS Desktop и standalone Web остаются неподдерживаемыми и не выпускаются.

Локальные логи, session DB, prompts и tool outputs сохранены ради работы harness.
Задать шифрование дисков, ACL, retention/deletion и редактирование секретов при
экспорте. Удаление remote analytics не заменяет корпоративный security audit:
необходим внутренний журнал пользователя, версии политики, approvals/denials,
действий инструментов и результатов. Gateway видит inference, но не все действия
на файловой системе. Такой SIEM-конвейер здесь не реализован.

## Обязательные дальнейшие работы

1. Реализовать GATEWAY-CONTRACT: workload identity, единственная модель и upstream,
   deny remote media/routing overrides, quotas/budgets и внутренний audit.
2. Выполнить ACCEPTANCE.md на реальном vLLM; подтвердить streaming и tool parser.
3. Проверить egress всех дочерних процессов, metadata/DNS/IPv6; gateway тоже без
   интернет-выхода. Контейнер не должен иметь host Docker socket или host credentials.
4. Сканировать и подписать конечный образ, подготовить SBOM и процесс срочного
   обновления upstream. Официальные advisory проверять перед каждым выпуском;
   наличие advisory в истории не означает применимость к этому baseline.
5. При необходимости MCP/LSP создать администраторский подписанный каталог,
   отдельную изоляцию серверов, scoped credentials и audit. Не возвращать загрузку
   произвольных npm/plugins ради удобства.

## Проверки и пределы доказательства

32 направленных теста прошли; typecheck трёх пакетов и Linux binary build прошли;
CLI проигнорировал внедрённый облачный конфиг. Тесты проверяют policy schema,
фиксированный endpoint/model, remote media и no-op telemetry. Они не являются
пакетным захватом трафика и не доказывают изоляцию runtime. Production rollout
заблокирован до прохождения перечисленных release gates.

## Windows port review scope — 2026-09-17

Patch 0005 adds a fixed Program Files policy and an embedded Windows PowerShell
5.1 ACL reader. It rejects untrusted owners, unsafe write/replacement rights,
reparse points, missing/oversized files and unsupported OS layouts. The checker
uses a fixed executable, working directory, minimal child environment and timeout.
CI exercises synthetic ACL and compiled startup failures; this does not establish
standard-user isolation or production readiness. Windows endpoint/child-process
egress controls and protected binary delivery are mandatory. See the installer
and README in `enterprise/windows/` after applying the series.

The Windows policy port itself does not resolve V1 inference timeouts or saved-approval
precedence. Subsequent patches 0006 and 0007 address these findings as described
below. Private evaluation, actual model/PTY flows and final supply-chain scanning
remain release gates.


## Execution and inference hardening — 2026-09-21

Patch 0006 fails closed for shell input that cannot be safely analyzed and adds
redirect/approval checks. Saved approvals are scoped to the requesting session;
an effective configured deny is not replaced by a saved allow. Regression tests
exercise the actual permission service and shell parser. These controls still do
not make an allowed shell command safe or replace OS/filesystem/network isolation.

Patch 0007 applies deadlines to the enterprise transport itself: headers 30s,
first model output 120s, idle output 60s and total request duration 10min. SSE
keepalives and role-only deltas do not count as output. Wrong/missing success MIME,
empty/stalled bodies and cancellation terminate the request; the source reader is
cancelled and its lock released. There are 21 additional directed deadline tests,
including an actual HTTP fixture checking disconnection. These tests passed on
Linux with Bun 1.3.14; Windows and the exact release build require their own CI.
No retries are introduced by the transport. Real inference/retry behavior remains
part of customer acceptance.

## Native Windows Desktop candidate — 2026-09-21

The additional native desktop patch packages the enterprise renderer and V1 engine
in Electron for Windows x64. It does not enable a remotely shared web service or V2.
Cloud/provider onboarding, arbitrary server switching, remote sharing/update paths,
plugins and MCP must remain unavailable through both the UI and backend. The
backend's immutable model policy and mandatory permission restrictions apply to
this profile as well as to console builds.

The native-client patch also closes adjacent entry points found during review:
TUI network flags must not expose an unrestricted listener, `run --attach` must
not select an unpatched remote server, and remote attachments must be rejected
before SDK preprocessing can fetch their URLs. Directed regression checks are
part of the candidate; their exact release-run status remains a CI gate.

Review/acceptance must cover Electron navigation and IPC boundaries, authenticated
local transport, renderer network requests, native modules, standard-user policy
failures and child-process cleanup. A screenshot demonstrates rendering, not these
security properties. Consult the exact native CI result and artifact manifest;
this document does not claim a completed desktop smoke run or private evaluation.

The NSIS installer and complete portable ZIP are **unsigned public CI candidates**.
The application installs separately from the fixed Program Files policy directory;
policy provisioning remains an administrator responsibility. Checksums do not
replace Authenticode signing, software provenance/SBOM review or endpoint controls.
See [desktop delivery instructions](../delivery/DESKTOP.md).
