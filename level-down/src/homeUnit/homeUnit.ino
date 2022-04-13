#include "Station.h"

int azEND = 8;
int elEND = 9;

int azimutPullPin = 4;
int azimutDirPin = 3;
int azimutEN = 2;

int elevationPullPin = 7;
int elevationDirPin = 6;
int elevationEN = 5;

// Инициализация моторов
Station station(azimutPullPin, azimutDirPin, elevationPullPin, elevationDirPin, azEND, elEND);

void setup() {
    Serial.begin(115200);
  
    pinMode(elEND, INPUT);
    pinMode(azEND, INPUT);
}

void loop() {
    //station.YouSpinMeRound();
    station.findHome();
    delay(1000);
    station.navigate(-90, 90, true);
    delay(100);
}
