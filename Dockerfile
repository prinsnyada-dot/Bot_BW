FROM python:3.10-slim

WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы
COPY . .

# Создаем базу данных
RUN python menu_data.py

# Запускаем бота
CMD ["python", "bot.py"]