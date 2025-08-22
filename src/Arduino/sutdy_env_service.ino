#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
#include <math.h>

#define DHTPIN   A0
#define DHTTYPE  DHT11

const int PIN_FAN_A = 5;
const int PIN_FAN_B = 6;
const int PIN_AC    = 9;   // A/C indicator (BLUE LED)
const int PIN_HEAT  = 13;  // HEAT indicator (RED LED)

// 임계값(℃)
float FAN_TEMP_HIGH  = 28.0f;  // Fan ON 기준
float AC_TEMP_HIGH   = 30.0f;  // A/C ON 기준 (습도 조건도 함께)
float HEAT_TEMP_LOW  = 22.0f;  // HEAT ON 기준 (습도 무시)
const float HUMI_HIGH = 50.0f; // A/C 추가 조건(고정)

// 모드/수동 상태
bool modeAuto = true;
bool manFan=false, manAC=false, manHeat=false;

// STATUS
const uint8_t STATUS_OK        = 0x00;
const uint8_t STATUS_READ_FAIL = 0x01;

// DHT11은 1~2초 간격으로 읽어야 하므로 최소 주기를 지킴
DHT_Unified dht(DHTPIN, DHTTYPE);
uint32_t minDelayMS = 1000;
unsigned long lastSample = 0;
float lastT = NAN, lastH = NAN;

// PyQt와 같은 0.1단위 스케일로 정/역변환
static inline int16_t to_i16_10(float v){ return (int16_t)lroundf(v*10.0f); }
static inline float   from_i32_10(int32_t v){ return ((float)v)/10.0f; }

// 모터: 간단히 정회전/정지로 구현
void fanSet(bool on){
  if(on){ digitalWrite(PIN_FAN_A,HIGH); digitalWrite(PIN_FAN_B,LOW); }
  else  { digitalWrite(PIN_FAN_A,LOW);  digitalWrite(PIN_FAN_B,LOW); }
}
void acSet (bool on){ digitalWrite(PIN_AC,   on?HIGH:LOW); }
void heatSet(bool on){ digitalWrite(PIN_HEAT, on?HIGH:LOW); }

void sendFrame(const char c0, const char c1, uint8_t status, const uint8_t *data=nullptr){
  Serial.write((uint8_t)c0);
  Serial.write((uint8_t)c1);
  Serial.write(status);
  if(data) Serial.write(data, 4);  // 데이터가 있을 때만 4B 전송
  Serial.write('\n');
}

// 주기 샘플 + 자동제어
void sampleIfDue(){
  unsigned long now = millis();
  if(now - lastSample < minDelayMS) return;
  lastSample = now;

  sensors_event_t te, he;
  dht.temperature().getEvent(&te);
  dht.humidity().getEvent(&he);
  lastT = te.temperature;
  lastH = he.relative_humidity;

  if(modeAuto && !isnan(lastT) && !isnan(lastH)){
    acSet  (lastT > AC_TEMP_HIGH  && lastH > HUMI_HIGH); // A/C: 온도/습도 모두 높을 때
    heatSet(lastT < HEAT_TEMP_LOW);                      // HEAT: 온도만 낮을 때(습도 무시)
    fanSet (lastT > FAN_TEMP_HIGH);                      // FAN:  온도만 높을 때
  }else if(!modeAuto){
    acSet(manAC); heatSet(manHeat); fanSet(manFan);      // 수동 상태 반영
  }
}

// 요청 처리 (모르는 CMD는 응답 없이 무시)
// 요청 형식(PC→아두이노)은 항상 7B: <2B CMD><4B DATA><\n> (데이터 없으면 0으로 채움)
void handleRequest(const uint8_t *buf, int n){
  if(n < 2) return;

  char c0 = (char)buf[0], c1 = (char)buf[1];

  int32_t i32 = 0; // payload (LE)
  if(n >= 6){
    i32  = (int32_t)buf[2] | ((int32_t)buf[3]<<8) |
           ((int32_t)buf[4]<<16) | ((int32_t)buf[5]<<24);
  }

  uint8_t out[4];

  // RD: 센서값 읽기 (resp: t10:int16 + h10:int16)
  if(c0=='R' && c1=='D'){
    if(isnan(lastT) || isnan(lastH)){ sendFrame('R','D', STATUS_READ_FAIL); return; }
    int16_t t10 = to_i16_10(lastT), h10 = to_i16_10(lastH);
    out[0]= t10 & 0xFF; out[1]= (t10>>8) & 0xFF;
    out[2]= h10 & 0xFF; out[3]= (h10>>8) & 0xFF;
    sendFrame('R','D', STATUS_OK, out);
  }
  // RF/RA/RH: 임계 조회 (resp: int32)
  else if(c0=='R' && (c1=='F' || c1=='A' || c1=='H')){
    int32_t v10 = (c1=='F') ? lroundf(FAN_TEMP_HIGH*10.0f)
                 : (c1=='A') ? lroundf(AC_TEMP_HIGH*10.0f)
                             : lroundf(HEAT_TEMP_LOW*10.0f);
    out[0]= v10 & 0xFF; out[1]= (v10>>8) & 0xFF; out[2]= (v10>>16) & 0xFF; out[3]= (v10>>24) & 0xFF;
    sendFrame('R', c1, STATUS_OK, out);
  }
  // SF/SA/SH: 임계 설정 (req: int32, resp: STATUS만) (data:int32(LE)를 받아서 0.1 스케일을 **실수(℃)**로 바꾼 후 저장)
  else if(c0=='S' && (c1=='F' || c1=='A' || c1=='H')){
    float f = from_i32_10(i32);
    if(c1=='F') FAN_TEMP_HIGH = f;
    if(c1=='A') AC_TEMP_HIGH  = f;
    if(c1=='H') HEAT_TEMP_LOW = f;
    sendFrame('S', c1, STATUS_OK);
  }
  // SM: 모드 설정(0=MANUAL, 1=AUTO)
  else if(c0=='S' && c1=='M'){
    modeAuto = (i32 != 0);
    if(!modeAuto){
      //  수동 모드 진입 시 내부 상태 및 출력 OFF로 초기화
      manFan = manAC = manHeat = false;
      fanSet(false); acSet(false); heatSet(false);
    }
    sendFrame('S','M', STATUS_OK);
  }
  // SC: 수동 제어 bitmask (bit0=FAN, bit1=AC, bit2=HEAT)
  else if(c0=='S' && c1=='C'){
    uint8_t m = (uint8_t)(i32 & 0xFF);
    manFan  = (m & 0x01);
    manAC   = (m & 0x02);
    manHeat = (m & 0x04);
    // 수동 모드에서 즉시 반영 (자동 모드일 때는 무시되지만, 다음 sampleIfDue에서 자동 로직이 덮어씀)
    if(!modeAuto){
      fanSet(manFan); acSet(manAC); heatSet(manHeat);
    }
    sendFrame('S','C', STATUS_OK);
  }
  // 그 외: 무응답
}

void setup(){
  Serial.begin(9600);
  pinMode(PIN_FAN_A,OUTPUT); pinMode(PIN_FAN_B,OUTPUT);
  pinMode(PIN_AC,OUTPUT);    pinMode(PIN_HEAT,OUTPUT);
  fanSet(false); acSet(false); heatSet(false);

  dht.begin();
  sensor_t s; dht.temperature().getSensor(&s);
  minDelayMS = s.min_delay/1000;  // us→ms (DHT11 ≈ 1000~2000ms)

  // DHT 안정화 후 실행
  delay(1500);
  lastSample = 0;
  sampleIfDue();
}

void loop(){
  sampleIfDue();

  static uint8_t rx[16];
  if(Serial.available() > 0){
    int n = Serial.readBytesUntil('\n', (char*)rx, sizeof(rx));
    if(n > 0) handleRequest(rx, n);
  }
}
