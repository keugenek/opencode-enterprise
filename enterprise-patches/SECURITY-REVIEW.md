# Security review OpenCode enterprise candidate

2026-09-05; baseline v1.18.29 / 16747470f976aca3d362ad730bcd3fe82ecc2c9a.
Метод: чтение критических путей исходного кода, патчи, направленные тесты,
проверка типов, сборка и CLI smoke test. Это не независимый pentest, не полный
аудит всех зависимостей и не сертификация enterprise-ready.

## Граница доверия

Цель: пользователь и файлы проекта не могут подключить другой provider/model
или изменить фиксированный endpoint в поддерживаемом Linux CLI-профиле.
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
| Высокий: внешняя передача сессий | share-next.ts: disabled и блокирующий request guard; CLI cloud/web/import/attach/serve/ACP entrypoints удалены из регистрации | В исходниках остаются неподдерживаемые пакеты; нельзя отдельно выпускать из них продукты |
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
и SBOM готового бинарника/образа. Неподдерживаемые desktop/web packages не релизить.

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
