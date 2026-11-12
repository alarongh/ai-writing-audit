# Водяные знаки и артефакты в тексте

| Что ищут | Что проверяют | Как читать результат |
| --- | --- | --- |
| Невидимый символ или необычный пробел | Кодовую точку Unicode и её место в файле | Присутствие символа устанавливается точно. Его назначение выясняют по контексту. [Unicode Line Breaking Algorithm](https://unicode.org/reports/tr14/) |
| Статистический водяной знак | Закономерность в последовательности токенов, характерную для конкретной схемы | Результат зависит от схемы, детектора и текста. Учитывают пропуски и ложные срабатывания. [Kirchenbauer и др.](https://proceedings.mlr.press/v202/kirchenbauer23a.html), [SynthID-Text](https://www.nature.com/articles/s41586-024-08025-4.pdf) |
| Сведения о происхождении файла | Свойства контейнера или подписанные записи C2PA | Обычное поле с названием программы и проверяемая подпись дают разные сведения. Для C2PA проверяют подпись и привязку записи к файлу. [Спецификация C2PA 2.4](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) |

## Скиллы и инструменты

| Проект | Механика | Что применено здесь |
| --- | --- | --- |
| Watermarks Remover | Скилл `remove-ai-marks` работает через локальный сервис. `clean-user-facing-text` предназначен для текста и запускается самостоятельно. | Самостоятельный скилл с локальным скриптом. [remove-ai-marks](https://github.com/guillaumemeyer/watermarks-remover/blob/main/skills/remove-ai-marks/SKILL.md), [clean-user-facing-text](https://github.com/guillaumemeyer/watermarks-remover/blob/main/skills/clean-user-facing-text/SKILL.md) |
| no-watermark | Инструмент сообщает о кандидатах и при очистке учитывает роль соединителей и тегов в эмодзи. | Соединители, теги, селекторы варианта, знаки направления письма и пробелы видны в отчёте. Они сохраняются при очистке. [Репозиторий и описание скилла](https://github.com/obrenoalvim/no-watermark#agent-skill) |
| AI Text Watermark Scanner | Показывает точные кодовые точки и позиции. Работает локально, публикует тестовые примеры. | Отчёт JSON с точными позициями и без фрагментов исходного текста. [Репозиторий](https://github.com/GeeDotDee/ai-text-watermark-scanner) |
| AI Watermarks Reality Check | Проверяет наблюдаемые признаки происхождения и отслеживает, что с ними происходит после преобразования. | Повторное сканирование итоговой копии. Удаление подтверждают сравнением версий файла. [Репозиторий](https://github.com/Neeeophytee/ai-watermarks-reality-check) |

## Исследования и стандарты

- **Unicode Standard Annex № 14.** U+200B даёт возможность переноса, U+00AD задаёт мягкий перенос, а U+2060 препятствует переносу. Сканер отмечает их для проверки. Решение об удалении зависит от роли символа в конкретном фрагменте. [Unicode Line Breaking Algorithm](https://unicode.org/reports/tr14/)
- **Unicode Standard Annex № 9 и Unicode Technical Standard № 51.** Управляющие символы направления влияют на отображение двунаправленного текста. ZWJ входит в последовательности эмодзи. Эти символы требуют интерпретации в контексте языка и отображения. [Bidirectional Algorithm](https://unicode.org/reports/tr9/), [Unicode Emoji](https://unicode.org/reports/tr51/)
- **A Watermark for Large Language Models**, Kirchenbauer и др., ICML 2023. Авторы изменяют вероятности выбора части токенов при генерации и проверяют, насколько часто они встречаются в результате. Работа описывает конкретную схему. Из неё нельзя вывести, применяет ли её отдельный поставщик. [PMLR](https://proceedings.mlr.press/v202/kirchenbauer23a.html)
- **Scalable watermarking for identifying large language model outputs**, Dathathri и др., Nature 2024. SynthID-Text использует выбор токенов, поэтому проверка отдельных кодовых точек и проверка водяного знака требуют разных методов. [Оригинал статьи](https://www.nature.com/articles/s41586-024-08025-4.pdf), [документация Google](https://ai.google.dev/responsible/docs/safeguards/synthid)
- **Описание водяных знаков Claude и OpenAI.** Anthropic описывает статистическую проверку последовательности слов с ключом. OpenAI описывает textGrain как статистический сигнал в выборе слов и указывает, что у детектора возможны ложные срабатывания и пропуски. Для текущего охвата моделей и продуктов сверяйтесь с публикациями поставщиков. [Anthropic](https://www.anthropic.com/news/claude-text-watermark), [OpenAI](https://openai.com/index/eu-text-provenance/)
- **C2PA 2.4.** Спецификация описывает подписи и разные способы привязать запись о происхождении к содержимому. Проверка такого файла требует средства, которое читает соответствующий контейнер и валидирует привязку. [Спецификация](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html)

## Локальная проверка

Скилл [text-artifact-audit](../.agents/skills/text-artifact-audit/SKILL.md) работает в Codex из этого репозитория. Ту же проверку можно запустить напрямую из корня проекта. Скрипту достаточно стандартной библиотеки Python 3.10 или новее. Поддерживаются UTF-8-файлы `.txt`, `.md` и `.markdown`.

```text
python .agents/skills/text-artifact-audit/scripts/text_artifacts.py scan draft.md
```

`scan` печатает SHA-256 файла и список находок. Идентификатор включает строку, столбец и кодовую точку, например `2:4:U+200B`. Строки и столбцы начинаются с единицы. Столбец считается по кодовым точкам, включая начальный BOM, если он присутствует. В исходном файле команда ничего не записывает.

После проверки контекста можно удалить отмеченную позицию, если у неё `removable_after_review: true`. Подставьте хеш исходника из отчёта и идентификатор нужного символа. Для нескольких позиций повторите `--remove`.

```text
python .agents/skills/text-artifact-audit/scripts/text_artifacts.py clean draft.md draft.cleaned.md --sha256 HASH_FROM_SCAN --remove 2:4:U+200B
python .agents/skills/text-artifact-audit/scripts/text_artifacts.py scan draft.cleaned.md
```

`clean` сверяет версию файла, проверяет весь список позиций и создаёт новую копию. Путь копии должен быть свободен. Для атомарной записи копии нужна файловая система с поддержкой жёстких ссылок, например NTFS. Команда сохраняет остальные байты файла, включая BOM и исходные переводы строк.

Текст из Word или PDF можно проверить в отдельном экспорте в UTF-8. Вывод сканера тогда относится к этому экспорту. Раскладку страниц, комментарии, свойства файла и подписи проверяют в исходном формате.
