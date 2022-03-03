// Подключение библиотек для работы с шаговыми двигателями
#include <AccelStepper.h>

// Пины
int xENDSTOP = 12;
int yENDSTOP = 13;
int angleDirPin = 8;
int angleStepPin = 9;
int rotateDirPin = 10;
int rotateStepPin = 11;

// Коэффициенты  редукторов
int k1 = 16;
int k2 = 16;

// Коэффициенты  драйверов
int q1 = 16;
int q2 = 16;

// Значения углов поворота
int angle = 0;
int rotation = 0;

// Переменные для принятия информации из СОМ-порта
bool newData = false;
String messageFromPC;
const byte numChars = 64;
char tempChars[numChars];
char receivedChars[numChars];

// Инициализация скорости моторов
int angleSpeed = 3200;
int rotateSpeed = 3200;

// Инициализация моторов
AccelStepper angleStep(1, 9, 8);
AccelStepper rotateStep(1, 11, 10);

// Инициализация порта, скоростей, ускорений и пинов концевиков
void setup(){
  Serial.begin(9600);
  angleStep.setMaxSpeed(32000);
  angleStep.setAcceleration(32000);
  rotateStep.setMaxSpeed(32000);
  rotateStep.setAcceleration(32000);
  pinMode(xENDSTOP, INPUT);
  pinMode(yENDSTOP, INPUT);
}

//=====================================================================================
// Бесконечный цикл для считывания параметров при их появлении
void loop(){
  recvWithStartEndMarkers();
    if (newData == true) {
        strcpy(tempChars, receivedChars);
        parseData();
        newData = false;
    }
}

//=====================================================================================
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
}

//=====================================================================================
// Парсинг полученной строки
void parseData() {      // разделение данных на составляющие части
    char * strtokIndx; // это используется функцией strtok() как индекс
    strtokIndx = strtok(tempChars," ");      // получаем значение первой переменной - строку
    messageFromPC = strtokIndx; //записываем её в переменную messageFromPC
    if(messageFromPC=="rotation"){ 
      strtokIndx = strtok(NULL, " "); // продолжаем с последнего индекса
      angle = atoi(strtokIndx);     // конвертируем эту составляющую в integer
      strtokIndx = strtok(NULL, " ");
      rotation = atoi(strtokIndx);     // преобразовываем этот кусок текста в int
      rotStepAngle(1);
      rotStepAngle(2);
      String messageFromPC;
    }
    if(messageFromPC=="homing"){homingSteppers();}
}

//=====================================================================================
// Поворот на угол, указанный в СОМ-порте. Index - номер мотора
int rotStepAngle(int index){
  Serial.write("OK");
  if(index==1){
    long steps = angle;
    if(steps>180){steps = 180;}
    if(steps<0){steps = 0;}
    steps = (steps * q1 * k1) / 1.8 * 2;
    angleStep.moveTo(steps);
    if(steps>angleStep.currentPosition()){
      while(angleStep.currentPosition() < steps and digitalRead(xENDSTOP) != HIGH){angleStep.run();}
    }
    if(steps<angleStep.currentPosition()){
      while(angleStep.currentPosition() > steps and digitalRead(xENDSTOP) != HIGH){angleStep.run();}
    }
  }
  else{
    long steps = rotation;
    if(steps>360){steps = 360;}
    if(steps<0){steps = 0;}  
    steps = (rotation * q2 * k2) / 1.8 * 2;
    rotateStep.moveTo(steps);
    if(steps>rotateStep.currentPosition()){
      while(rotateStep.currentPosition() < steps and digitalRead(yENDSTOP) != HIGH){rotateStep.run();}
    }
    if(steps<rotateStep.currentPosition()){
      while(rotateStep.currentPosition() > steps and digitalRead(yENDSTOP) != HIGH){rotateStep.run();}
    }
  }
}

//=====================================================================================
// Функция перемещения к концевикам
void homingSteppers(){
  Serial.write("OK");
    while(digitalRead(xENDSTOP)==LOW){
      angleStep.setSpeed(angleSpeed);
      while(digitalRead(xENDSTOP)!=HIGH and angleStep.currentPosition()<=3200){
        angleStep.runSpeed();
        if(digitalRead(xENDSTOP)==HIGH){
          Serial.println("X ENDSTOP");
          angleStep.setCurrentPosition(0);
          break;
        }
      }
      delay(500);
      if(digitalRead(xENDSTOP)==LOW){
        angleStep.setSpeed(-angleSpeed);
        while(digitalRead(xENDSTOP)!=HIGH and angleStep.currentPosition()>=0){
          angleStep.runSpeed();
          if(digitalRead(xENDSTOP)==HIGH){
            Serial.println("X ENDSTOP");
            angleStep.setCurrentPosition(0);
            break;
          }
        }
        delay(500);
      }
    }
    while(digitalRead(yENDSTOP)!=HIGH){
      rotateStep.setSpeed(rotateSpeed);
      while(digitalRead(yENDSTOP)!=HIGH and rotateStep.currentPosition()<=3200){
        rotateStep.runSpeed();
        if(digitalRead(yENDSTOP)==HIGH){
          Serial.println("Y ENDSTOP");
          rotateStep.setCurrentPosition(0);
          break;
        }
      }
      delay(500);
      if(digitalRead(yENDSTOP)==LOW){
        rotateStep.setSpeed(-rotateSpeed);
        while(digitalRead(yENDSTOP)!=HIGH and rotateStep.currentPosition()>=0){
          rotateStep.runSpeed();
          if(digitalRead(yENDSTOP)==HIGH){
            Serial.println("Y ENDSTOP");
            rotateStep.setCurrentPosition(0);
            break;
          }
        }
        delay(500);
      }
    }
}
