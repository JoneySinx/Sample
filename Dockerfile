FROM python:3.10-slim-bullseye

# 1. System updates aur Git install karna (Pip packages ke liye)
# 'rm -rf' se hum apt cache hata dete hain taaki image choti bane
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# 2. Working Directory set karna
WORKDIR /EvaMaria

# 3. Pehle requirements copy aur install karein (Caching ke liye fast hota hai)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir -U -r requirements.txt

# 4. Ab baaki saara code copy karein (Ye step purane wale mein missing tha)
COPY . .

# 5. Bot start command
# Agar aapke paas start.sh nahi hai, to seedha python command use karein
# Koyeb ke liye ye sabse best aur fast tareeka hai:
CMD ["python3", "bot.py"]

