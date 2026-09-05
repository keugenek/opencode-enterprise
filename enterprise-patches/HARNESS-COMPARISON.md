# Выбор enterprise coding harness

По состоянию на 2026-09-05. Требование: закрытая среда, одна фиксированная модель
на внутреннем vLLM, запрет пользовательского добавления cloud providers, управляемые
инструменты, отсутствие внешней телеметрии. Ниже — анализ официальной документации,
а не результаты запуска всех продуктов. Наличие настройки не означает невозможность
её обхода; формулировки «поддерживается» требуют проверки конкретной редакции и версии.

| Harness | Guardrails из коробки | Внутренний vLLM / закрытая среда | Вывод |
|---|---|---|---|
| OpenCode | Permissions, managed config, experimental provider.use policies; enterprise offering | OpenAI-compatible endpoint подходит; standalone CLI возможен | Удобная OSS-база; runtime isolation и полная неизменяемая политика требуют дополнительных мер |
| Cline Enterprise | SSO/RBAC, централизованные конфиги, управление моделями/инструментами, audit/OTEL | Документирован OpenAI-compatible и private infrastructure | Первый кандидат на покупку/POC; подтвердить offline control plane и неизменяемую URL/model policy |
| Codex CLI | Managed requirements, approvals, OS sandbox, ограничения permission profiles | Custom provider есть; актуальный transport — Responses API | Сильная база sandbox; обычного vLLM Chat Completions недостаточно без совместимости/адаптера |
| Claude Code | Managed settings, tool permissions, запрет bypass, OS sandbox | Официальный provider ecosystem ориентирован на Claude | Подходит если допустим Claude; произвольная локальная модель не подтверждена как поддерживаемый сценарий |
| Gemini CLI | System settings, admin-tier policy engine, sandbox | Ориентирован на Gemini/Vertex | Хорошая административная модель; универсальный vLLM backend не установлен по изученной документации |
| Continue | Self-hosted models, offline режим, отключение telemetry | Документирован vLLM | Хороший локальный IDE вариант; жёсткие централизованные guardrails требуют отдельной проверки |
| Cursor | Enterprise controls; отдельные self-hosted workers | BYOK запросы проходят через Cursor backend | Не первый выбор для требования полного отсутствия vendor network |

## Рекомендация

Начать с POC Cline Enterprise: проверить, можно ли купить требуемое управление
вместо постоянного сопровождения форка. Условия приёмки: полностью внутренний
control plane, отсутствие обязательной vendor telemetry, root/admin-managed
фиксация baseURL + model (не только списка моделей), отключение пользовательских
плагинов/MCP, невозможность обхода через env/project config, работоспособность
при заблокированном интернете и управляемая изоляция shell. Документация поставщика
не заменяет эти испытания. [Enterprise overview](https://docs.cline.bot/enterprise-solutions/overview),
[совместимые endpoints](https://docs.cline.bot/provider-config/openai-compatible).

Если нужна полностью контролируемая OSS CLI-поставка, продолжить OpenCode-форк
с этой серией патчей, внутренним gateway и отдельным sandbox на workspace.
Официальные [policies](https://opencode.ai/docs/policies/) покрывают provider.use,
но это экспериментальный механизм; [permissions](https://opencode.ai/docs/permissions/)
сами по себе не изолируют процессы. Enterprise-возможности upstream тоже стоит
проверить коммерческим POC: [OpenCode Enterprise](https://opencode.ai/docs/enterprise/).

Codex стоит параллельно проверить, если внутренний gateway способен корректно
реализовать Responses API: [managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration),
[security](https://learn.chatgpt.com/docs/security),
[provider configuration](https://learn.chatgpt.com/docs/config-file/config-reference).
Из этой документации нельзя вывести, что arbitrary endpoint/model уже неизменяемо
закреплены всеми нужными constraints; gateway остаётся отдельной границей доверия.

## Остальные кандидаты и источники

Claude Code имеет [managed settings](https://code.claude.com/docs/en/settings)
и [sandbox](https://code.claude.com/docs/en/sandboxing), включая контроль выхода из
sandbox. Но [поддерживаемые интеграции](https://code.claude.com/docs/en/third-party-integrations)
не доказывают возможность заменить Claude любой open-weight моделью на vLLM.

Gemini CLI документирует [enterprise settings](https://geminicli.com/docs/cli/enterprise/)
и [admin-tier policy](https://geminicli.com/docs/reference/policy-engine/).
Такая политика сильнее инструкций модели; привилегированный администратор хоста
всё равно остаётся доверенным.

Continue явно описывает [self-hosted model/vLLM](https://docs.continue.dev/guides/how-to-self-host-a-model)
и [работу без интернета](https://docs.continue.dev/guides/running-continue-without-internet).
Rules в prompt не считать security boundary; неизменяемые enterprise policies
и sandbox нужно подтвердить отдельно, включая коммерческую редакцию.

Для Cursor [BYOK documentation](https://cursor.com/help/models-and-usage/api-keys)
указывает на прохождение запросов через backend Cursor. Наличие
[self-hosted workers](https://cursor.com/docs/cloud-agent/self-hosted)
не означает полностью автономного control plane.

## Универсальный дистрибутив

Универсальным лучше делать платформенный слой: identity → managed policy →
одноразовый изолированный workspace → внутренний inference gateway → vLLM.
Harness — заменяемый клиент с адаптером протокола и общей acceptance suite.
Модель/tool policy закреплять также на gateway; сеть и файлы ограничивать ОС;
внутренний audit собирать отдельно от продуктовой аналитики.

Не обязательно писать sandbox самостоятельно: Docker документирует
[запуск OpenCode в Sandboxes](https://docs.docker.com/ai/sandboxes/agents/opencode/).
Это кандидат на слой исполнения с отдельной проверкой платформенной поддержки,
сетевой политики и offline provisioning, а не готовая замена model governance.
