#include <AccelStepper.h>
#include <math.h>

class Station {
    private:
        AccelStepper elevationStep;
        AccelStepper azimutStep;

        int azEND = 1;
        int elEND = 4;

        int azimutPullPin = 6;
        int azimutDirPin = 3;
        int azimutEN = 2;

        int elevationPullPin = 11;
        int elevationDirPin = 10;
        int elevationEN = 9;

        float calibrationSpeed = 30;
        float motorSpeed = 10;

        int azMotork = 1;
        int elMotork = 1;

        int azReductionk = 16;
        int elReductionk = 16;

        int azAllSteps = 800;
        int elAllSteps = 800;

        int azRation = azMotork * azReductionk;
        int elRation = elMotork * elReductionk;

        int8_t azInverted = 1;
        int8_t elInverted = -1;

        bool inHome = false;
        bool defCorr = true;

        float azCorrection = 0;
        float elCorrection = -16;

        float tAzCorrection = 0;
        float tElCorrection = 0;


        void _calcRation(){
            azRation = azMotork * azReductionk;
            elRation = elMotork * elReductionk;
        };

        inline float _getAzSteps(float degree) {
            return degree * azRation * azAllSteps / 360.0;
        }

        inline float _getElSteps(float degree) {
            return degree * elRation * elAllSteps / 360.0;
        }

        bool _checkAzEND() {
            if(digitalRead(azEND) && !inHome){
                azimutStep.stop();
                azimutStep.setCurrentPosition(0);
                Serial.println("Unexpectedly Az END ");
                return true;
            }
            return false;
        }

        bool _checkElEND() {
            if(digitalRead(elEND) && !inHome){
                elevationStep.stop();
                elevationStep.setCurrentPosition(0);
                Serial.println("Unexpectedly El END ");
                return true;
            }
            return false;
        }
        
    public:
        Station(int azPullPin, int azDirPin, int elPullPin, int elDirPin, int azE, int elE){
            this->azimutDirPin = azDirPin;
            this->azimutPullPin = azPullPin;

            this->elevationDirPin = elDirPin;
            this->elevationPullPin = elPullPin;
        
            this->azEND = azE;
            this->elEND = elE;

            elevationStep = AccelStepper(1, elevationPullPin, elevationDirPin);
            azimutStep = AccelStepper(1, azimutPullPin, azimutDirPin);

            this->_calcRation();
            
            azimutStep.setCurrentPosition(0);
            elevationStep.setCurrentPosition(0);
           
            //this->navigateRel(-azCorrection, -elCorrection);
        }

        void setCalibrationSpeed(float speed) {
            calibrationSpeed = speed;
        }
    
        void setSpeed(float speed) {
            motorSpeed = speed;
        }

        void setRation(int azM=1, int elM=1, int elR=16, int azR=16) {
            azMotork = azM;
            elMotork = elM;
            azReductionk = azR;
            elReductionk = elR;
        }
        
        void setHome() {
            if (!defCorr)
                azCorrection = tAzCorrection;
                elCorrection = tElCorrection;

            tAzCorrection = 0;
            tElCorrection = 0;

            Serial.print(azCorrection);
            Serial.print(" ");
            Serial.println(elCorrection);

            elevationStep.setCurrentPosition(0);
            azimutStep.setCurrentPosition(0);
        }

        void setCorrections(float azimuth, float elevation) {
            if (azimuth || elevation) {
                tAzCorrection += azimuth;
                tElCorrection += elevation;
                defCorr = false;
            }
            this->navigateRel(azimuth, elevation);
        }

        void printCorrections() {
            Serial.print(azCorrection);
            Serial.print(" ");
            Serial.println(elCorrection);
        }

        void clearCorrections() {

            azCorrection = 0;
            elCorrection = 0;
        }

        void navigate(float azimuth, float elevation, bool fast=false) {

            if (fast) {
                elevationStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
                elevationStep.setAcceleration(this->_getAzSteps(calibrationSpeed));

                azimutStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
                azimutStep.setAcceleration(this->_getAzSteps(calibrationSpeed));
            }

            else {
                elevationStep.setMaxSpeed(this->_getAzSteps(motorSpeed));
                elevationStep.setAcceleration(this->_getAzSteps(motorSpeed));

                azimutStep.setMaxSpeed(this->_getAzSteps(motorSpeed));
                azimutStep.setAcceleration(this->_getAzSteps(motorSpeed));
            }

            azimuth = fmod(azimuth, 361);

            elevation = elevation >= 0 ? elevation : -elevation;
            elevation = fmod(elevation, 91);
            
            Serial.print("Navigate to ");
            Serial.print("az: ");
            Serial.print(azimuth);
            Serial.print(" el: ");
            Serial.println(elevation);
            
            azimutStep.moveTo(this->_getAzSteps(azimuth * azInverted));
            elevationStep.moveTo(this->_getElSteps(elevation * elInverted));
                      
            while(azimutStep.distanceToGo() || elevationStep.distanceToGo()){

                azimutStep.run();
                elevationStep.run();                
            }

            inHome = false;
            Serial.println("OK");
            
        }

        void navigateRel(float azimuth, float elevation) {
            this->_calcRation();

            elevationStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
            elevationStep.setAcceleration(this->_getAzSteps(calibrationSpeed));

            azimutStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
            azimutStep.setAcceleration(this->_getAzSteps(calibrationSpeed));

            azimutStep.move(this->_getAzSteps(azimuth * azInverted));
            elevationStep.move(this->_getElSteps(elevation * elInverted));
            
            while(azimutStep.distanceToGo() || elevationStep.distanceToGo()){
                //this->_checkAzEND();
                //this->_checkElEND();

                azimutStep.run();
                elevationStep.run();
            }
            Serial.println("OK");
            
        }

        void navigateDynamic(float azimuth, float elevation, float speed) {
            this->_calcRation();

            elevationStep.setMaxSpeed(this->_getAzSteps(speed));
            elevationStep.setAcceleration(this->_getAzSteps(speed));

            azimutStep.setMaxSpeed(this->_getAzSteps(speed));
            azimutStep.setAcceleration(this->_getAzSteps(speed));
            
            azimutStep.moveTo(this->_getAzSteps(azimuth * azInverted));
            elevationStep.moveTo(this->_getElSteps(elevation * elInverted));
            
            while(azimutStep.distanceToGo() || elevationStep.distanceToGo()){
                //this->_checkAzEND();
                //this->_checkElEND();
                //Serial.println(elevationStep.distanceToGo());
                azimutStep.run();
                elevationStep.run();
            }
            
            Serial.println("OK");
            
        }

        void comeBack() {
            azimutStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
            azimutStep.setAcceleration(this->_getAzSteps(calibrationSpeed / 2));

            azimutStep.move(-azimutStep.currentPosition() - 10);

            while(azimutStep.distanceToGo()){
                azimutStep.run();
            }
            
            Serial.println("OK");
        }
    
        void findHome(){
            this->_calcRation();
            
            elevationStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
            elevationStep.setAcceleration(this->_getAzSteps(calibrationSpeed / 2));

            azimutStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed));
            azimutStep.setAcceleration(this->_getAzSteps(calibrationSpeed / 2));
      
            unsigned long long azTimer = millis();
            unsigned long long elTimer = millis();
    
            bool azFixed = false;
            bool elFixed = false;
      
            while(!azFixed || !elFixed){
              /*
                Serial.print("fix: ");
                Serial.print(azFixed);
                Serial.print(" ");
                Serial.print(elFixed);
                Serial.print(" ");
              */
                Serial.print("Ends: ");
                Serial.print(digitalRead(azEND));
                Serial.print(" ");
                Serial.println(digitalRead(elEND));
                
              
                if ((millis() - azTimer) < 30 && !azFixed)
                    if (!digitalRead(azEND)) {
                        azimutStep.setSpeed(this->_getAzSteps(calibrationSpeed));
                        azTimer = millis();
                    }
                    else
                        azimutStep.setSpeed(0);
                else
                    azFixed = true;
            
                if ((millis() - elTimer) < 30 && !elFixed)
                    if (!digitalRead(elEND)) {
                        elevationStep.setSpeed(this->_getElSteps(calibrationSpeed));
                        elTimer = millis();
                    }
                    else 
                        elevationStep.setSpeed(0);
                else
                    elFixed = true;
    
                azimutStep.runSpeed();
                elevationStep.runSpeed();
            }

            inHome = true;

            this->navigateRel(azCorrection, elCorrection);
            
            elevationStep.setCurrentPosition(0);
            azimutStep.setCurrentPosition(0);
                    
            Serial.println("In Home");
            Serial.println("OK");
        }
        
        void YouSpinMeRound() {
            this->_calcRation();
            
            azimutStep.setMaxSpeed(this->_getAzSteps(calibrationSpeed * 2));
            azimutStep.setAcceleration(this->_getAzSteps(calibrationSpeed * 2));
            
            azimutStep.setSpeed(this->_getAzSteps(calibrationSpeed * 2));

            elevationStep.setMaxSpeed(this->_getElSteps(calibrationSpeed * 2));
            elevationStep.setAcceleration(this->_getElSteps(calibrationSpeed * 2));
            
            elevationStep.setSpeed(this->_getElSteps(calibrationSpeed * 2));

            unsigned long timer = millis();

            while(millis()-timer < 20000){                
                elevationStep.runSpeed();               
                azimutStep.runSpeed();
            }

            azimutStep.setSpeed(0);
            elevationStep.setSpeed(0);
            Serial.println("OK");
        }
        
};
