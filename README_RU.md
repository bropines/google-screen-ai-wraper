# Google ScreenAI Python Wrapper & CLI

Кроссплатформенная обертка Python и CLI для локальной библиотеки от Google **ScreenAI** (On-Device OCR и Main Content Extraction).

---

## 📸 Автоматическая настройка ShareX и интеграция с буфером обмена

Если вы используете **ShareX** на Windows, вы можете полностью автоматизировать настройку одной командой:

```bash
screen-ai --setup-sharex
```

### Что делает `--setup-sharex`:
1. **Проверяет модели:** Проверяет наличие бинарных файлов и моделей ScreenAI. Если их нет, автоматически скачивает актуальный бинарник из Google CIPD.
2. **Настраивает горячую клавишу:** Регистрирует комбинацию **`Ctrl + Shift + '`** в ShareX для захвата области экрана, запуска OCR на устройстве и копирования распознанного текста в буфер обмена.

### Флаг копирования в буфер обмена
Вы можете копировать результат OCR в буфер обмена через CLI флагом `--sharex` (`-sx`):

```bash
screen-ai ocr -i sample.png --sharex
```

*Примечание: Устанавливайте пакет с опцией `[clipboard]`:*
```bash
pip install -e .[clipboard]
```

---

## Установка

```bash
pip install -e .[clipboard]
```

---

## Команды CLI

```bash
# Проверить статус установки и версию DLL
screen-ai info

# Скачать модели и бинарники Google ScreenAI (~50МБ)
screen-ai download

# Запустить OCR на изображении
screen-ai ocr -i sample.png

# Запустить OCR и скопировать текст в буфер обмена
screen-ai ocr -i sample.png --sharex

# Автоматически настроить интеграцию с ShareX
screen-ai --setup-sharex
```
