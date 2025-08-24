
#include <DHT.h>

#define DHTPIN   A0

int sensorPin = A0;     
int sensorValue = 0;
int buzzerPin = 2;


void setup() {
  // declare the ledPin as an OUTPUT:
  pinMode(buzzerPin, OUTPUT);
  Serial.begin(9600);
}

void loop()
{
  sensorValue = analogRead(sensorPin);
  // Serial.println(sensorValue);
  bool buzzerState = false;
  delay(500);
  if(sensorValue < 980)
  {
    Serial.println("Object Detected!");
    digitalWrite(buzzerPin, HIGH);  // 부저 ON
    Serial.println(sensorValue);  // 센서 값 전송
    buzzerState = true;
    delay(500);                   // 0.5초마다 전송

  }
  else
  {
    Serial.println("No Object");
    digitalWrite(buzzerPin, LOW);
    buzzerState = false;
  }
    Serial.print(sensorValue);
    Serial.print(",");
    Serial.println(buzzerState ? 1 : 0);

    delay(500);
}