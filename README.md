# Lorett-Rotator


sudo pip3 install pyorbital
sudo pip3 install prettytable
sudo pip3 install matplotlib

Настройка ssh на серверной стороне.

1. Делаем аккаунт для ngrok (ngrok.com)

(
у нас он уже есть
login: nebosckop@yandex.ru
password: nebosckop-1
token: 23BZwt7S1xxKeXXE1tC69EORBSa_6CCurBJNPQ5iN7Man4V1W
)

2. Проверяем наличие snap (есть ли вывод на команду snap, если выводит справку пропускаем следующие 2 пункта)

3. Если его нет то выполнить команды 

sudo apt update (нужно не всегда)
sudo apt install snapd (<- d не опечатка)

4. Дожидаемся установки и перезапускаем систему

sudo reboot

5. Устанавливаем ядро для snap

sudo snap install core

6. Устанавливаем саму утилиту ngrok

sudo snap install ngrok

7. переходим в дирректорию с конфигом ngrok:

cd /home/{user_name}/.ngrok2

(
у нас:
cd /home/pi/.ngrok2
)

если ругается, что такого пути нет, то создаём его и переходим в него

cd /home/{user_name}
mkdir .ngrok2
cd .ngrok2

(
у нас:
cd /home/pi
mkdir .ngrok2
cd .ngrok2
)

8. заходим в редактор nano

nano

9. прописываем с соблюдением отступов

authtoken: {ngrok_token}

region: eu
web_addr: localhost:4040

tunnels:
  ssh:
    addr: 22
    proto: tcp


(
с нашим токеном вышлядит так:
authtoken: 261sjOeufLODHlcVrGnxRE9vSKm_4DPjfpUV93JxaHrrhsZQv

region: eu
web_addr: localhost:4040

tunnels:
  ssh:
    addr: 22
    proto: tcp
)

10. Сохраняем файл

CTRL + O
ngrok.yml
ENTER
CTRL + X


15. Узнаём число нужное для доступа к файлу ngrok

cd /snap/ngrok
ls

Здесь должно быть папка с именем в виде числа. Оно призодится в дальнейшем как {число}
(в моём случае число было 35 и 38 на разных системах)

cd /home/{user_name}

16. Добавляем задачи в CRON

crontab -e

17. Если первый запуск выбираем редактор. Для удобства выбираем nano

как правило:
1
ENTER

18. Откроется редактор задач. В конец файла дописываем 2 стороки

@reboot sleep 10 && /snap/ngrok/37/ngrok start ssh --log=stdout > /dev/null &