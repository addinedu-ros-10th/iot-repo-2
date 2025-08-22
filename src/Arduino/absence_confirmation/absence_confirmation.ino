#define TRIG      9
#define ECHO      8
#define BLUE_LED  7
#define RED_LED   3
#define FSR_PIN   A0
#define THRESHOLD_CM 50.0

float readDistanceCm() {
  digitalWrite(TRIG, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  unsigned long d = pulseIn(ECHO, HIGH, 30000UL);
  if (!d) return NAN;
  float cm = d / 58.0;
  return (cm < 2 || cm > 400) ? NAN : cm;
}

const unsigned long PRINT_PERIOD_MS = 4000;  // 출력 간격
unsigned long lastPrint = 0;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG, OUTPUT);   digitalWrite(TRIG, LOW);
  pinMode(ECHO, INPUT);
  pinMode(BLUE_LED, OUTPUT); digitalWrite(BLUE_LED, LOW);
  pinMode(RED_LED, OUTPUT);  digitalWrite(RED_LED, LOW); // Active-HIGH 가정
}

void loop() {
  // 센서 읽기
  float distance = readDistanceCm();
  int fsr = analogRead(FSR_PIN);          // 0~1023
  bool isZero = (fsr <= 3);               // 0~3을 0으로 간주

  // LED 제어(즉시 반응)
  // LED 제어(예시)
  bool blueOn = (!isnan(distance) && distance >= THRESHOLD_CM);  // 파란 LED 조건
  bool redOn  = isZero;                                          // 빨간 LED 조건

  digitalWrite(BLUE_LED, blueOn ? HIGH : LOW);
  digitalWrite(RED_LED,  redOn  ? HIGH : LOW);

// === 여기 변경 ===
  bool present = !(blueOn && redOn);    // 둘 다 OFF면 재실
  bool absent  = !present;

// JSON 로깅 (PyQt에서 쓰기 좋게)
  Serial.print("{\"blue\":");    Serial.print(blueOn);
  Serial.print(",\"red\":");     Serial.print(redOn);
  Serial.print(",\"present\":"); Serial.print(present);
  Serial.println("}");

  // 출력은 주기적으로만
  if (millis() - lastPrint >= PRINT_PERIOD_MS) {
    lastPrint += PRINT_PERIOD_MS;         // 드리프트 방지

    if (isnan(distance)) Serial.println(F("Distance: ---"));
    else { Serial.print(F("Distance: ")); Serial.print(distance,1); Serial.println(F(" cm")); }

    Serial.print(F("FSR raw: "));
    Serial.println(fsr);
  }

  delay(20);  // 센서 폴링 속도(원하면 0~50ms 사이로 조절)
}
