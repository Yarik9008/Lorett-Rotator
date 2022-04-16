#include <Arduino.h>
#include "Station.h"

//#define DEGUG

int azEND = 8;
int elEND = 9;
int azimutPullPin = 4;
int azimutDirPin = 3;
int azimutEN = 2;

int elevationPullPin = 7;
int elevationDirPin = 6;
int elevationEN = 5;

// Переменные для принятия информации из СОМ-порта
bool newData = false;
String messageFromPC;
const byte numChars = 64;
char tempChars[numChars];
char receivedChars[numChars];

// Инициализация моторов
Station station(azimutPullPin, azimutDirPin, elevationPullPin, elevationDirPin, azEND, elEND);

// Парсинг полученной строки
void parseData() {      // разделение данных на составляющие части
    float azimut;
    float  elevation;

    char * strtokIndx; // это используется функцией strtok() как индекс
    strtokIndx = strtok(tempChars, " ");      // получаем значение первой переменной - строку
    messageFromPC = strtokIndx; //записываем её в переменную messageFromPC
    //Serial.println(tempChars);
    //Serial.println(strtokIndx);
    if(messageFromPC=="n"){ 
        strtokIndx = strtok(NULL, " ");
        azimut = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
        elevation = atof(strtokIndx);     // конвертируем эту составляющую во float
        station.navigate(azimut, elevation);
        String messageFromPC;
    }

    if(messageFromPC=="nf"){ 
        strtokIndx = strtok(NULL, " ");
        azimut = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
        elevation = atof(strtokIndx);     // конвертируем эту составляющую во float
        station.navigate(azimut, elevation, true);
        String messageFromPC;
    }

    else if(messageFromPC=="nr"){ 
        strtokIndx = strtok(NULL, " ");
        azimut = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
        elevation = atof(strtokIndx);     // конвертируем эту составляющую во float
        station.navigateRel(azimut, elevation);
        String messageFromPC;
    }

    else if(messageFromPC=="nd"){ 
        strtokIndx = strtok(NULL, " ");
        azimut = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        
        strtokIndx = strtok(NULL, " ");
        elevation = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
        float speed = atof(strtokIndx);     // конвертируем эту составляющую во float

        speed = fmod(speed, 20);
        station.navigateDynamic(azimut, elevation, speed);
        String messageFromPC;
    }

    else if(messageFromPC=="nrc"){ 
        strtokIndx = strtok(NULL, " ");
        azimut = atof(strtokIndx);     // преобразовываем этот кусок текста во float

        strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
        elevation = atof(strtokIndx);     // конвертируем эту составляющую во float
        station.setCorrections(azimut, elevation);
        String messageFromPC;
    }

    else if(messageFromPC == "cb") {
        station.comeBack();
    }

    else if(messageFromPC=="s"){ 
        station.setHome();
    }

    else if(messageFromPC=="c"){ 
        station.clearCorrections();
    }

    else if(messageFromPC=="h")

        station.findHome();
}

// Считывание строки из СОМ-порта
void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    
    char startMarker = '$';
    char endMarker = ';';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();
        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // завершаем строку
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }
        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
    //Serial.println(receivedChars);
}

void setup() {
    Serial.begin(115200);
  
    pinMode(elEND, INPUT);
    pinMode(azEND, INPUT);

    //station.setRation();
    //station.findHome();
    //station.YouSpinMeRound(); 
}

#ifdef DEBUG
    bool setupF = true;
#endif
void loop() {
    #ifdef DEBUG
        if(setupF){
            //station.navigate(0, 25);
            //station.findHome();
            setupF = false;
        }
    #endif
    
    recvWithStartEndMarkers();
    station.printCorrections();
    if (newData == true) {
        strcpy(tempChars, receivedChars);
        parseData();

        newData = false;
    }
    
}
