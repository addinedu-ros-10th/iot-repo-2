// #include <SPI.h>
// #include <MFRC522.h>

// #define RST_PIN         9          // Configurable, see typical pin layout above
// #define SS_PIN          10         // Configurable, see typical pin layout above

// MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

// const int allowedUidNums = 2;  // 허용 가능 uid 갯수

// // LED pin 관련 변수
// const int RED_LED = 7;
// const int YLW_LED = 5;
// const int GRN_LED = 3;

// // card check 상태 관련 변수
// bool isWaiting = false;
// bool isChecking = false;
// bool isUsed = false;
// enum State { WAIT, CHECK, USE };

// String canAccessUID[allowedUidNums] = {}; 

// // 새로 추가한 변수
// State beforeState = WAIT;
// State currentState = WAIT;

// // 시간 관련 변수
// unsigned long lastCardCheckTime = 0;
// unsigned long lastStateChangeTime = 0;
// const int cardCheckingInterval = 500;
// const int nextCardCheckInterval = 1000;

// String getUID()
// {
// 	String tempUID = "";

// 	for (byte i = 0; i < mfrc522.uid.size; i++)
// 		{
// 			if (mfrc522.uid.uidByte[i] < 0x10) tempUID += "0";
// 			tempUID += String(mfrc522.uid.uidByte[i], HEX);
// 		}
	
// 	return tempUID;
// }

// void changeState(State state)
// {
// 	switch (state)
// 	{
// 		case WAIT:
// 			isWaiting = true;
// 			isChecking = false;
// 			isUsed = false;
// 			return;
// 		case CHECK:
// 			isWaiting = false;
// 			isChecking = true;
// 			isUsed = false;
// 			return;
// 		case USE:
// 			isWaiting = false;
// 			isChecking = false;
// 			isUsed = true;
// 			return;
// 		default:
// 			isWaiting = true;
// 			isChecking = false;
// 			isUsed = false;
// 			return;
// 	}
// }

// void cardCheck()
// {
// 	// SPI.begin();			// Init SPI bus
// 	// mfrc522.PCD_Init();		// Init MFRC522

// 		bool newCard = mfrc522.PICC_IsNewCardPresent();
// 		bool readCard = mfrc522.PICC_ReadCardSerial();
// 	if (!newCard || !readCard) return;
// 	// nextCardCheckInterval 동안 추가 스캔 차단
// 	// if (millis() - lastCardCheckTime < nextCardCheckInterval)
// 	// {
// 	// 	return;
// 	// }
// 	Serial.print("newCard : ");
// 	Serial.println(newCard);
// 	Serial.print("readCard : ");
// 	Serial.println(readCard);

// 	// Serial.print("beforeState == WAIT && millis() - lastStateChangeTime >= cardCheckingInterval.       :       ");
// 	// Serial.println(beforeState == WAIT && millis() - lastStateChangeTime >= cardCheckingInterval);
	
// 	switch (currentState)
// 	{
// 		// 현재 상태가 대기 중인 경우
// 		case WAIT:

// 			// if (!newCard || !readCard) return;
// 			// if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) return;

// 			// uid 인식
// 			String uid = getUID();

// 			// 상태 변경
// 			if (uid != "")
// 			{
// 				Serial.println("카드 인식 성공");
// 				Serial.print("card UID : ");
// 				Serial.println(uid);
				
// 				canAccessUID[0] = uid;

// 				lastCardCheckTime = millis();

// 				beforeState = currentState;
// 				currentState = CHECK;
// 				changeState(CHECK);
// 				lastStateChangeTime = millis();
// 			}

// 			// mfrc522.PICC_HaltA();
// 			// mfrc522.PCD_StopCrypto1();

// 			break;

// 		case CHECK:
// 			// 체크 시간이 지났으면 자동으로 상태 변경
// 			if (beforeState == WAIT && millis() - lastStateChangeTime >= cardCheckingInterval)
// 			{
// 				Serial.println("사용 중으로 전환합니다.");
// 				beforeState = currentState;
// 				currentState = USE;
// 				// changeState(USE);
// 				lastStateChangeTime = millis();
// 			}
// 			if (beforeState == USE && millis() - lastStateChangeTime >= cardCheckingInterval)
// 			{
// 				Serial.println("퇴실합니다.");
// 				beforeState = currentState;
// 				currentState = WAIT;
// 				// changeState(WAIT);
// 				lastStateChangeTime = millis();
// 			}
// 			break;
// 		case USE:
// 			break;
// 		default:
// 			Serial.println("here");
// 			return;
// 	}
// 	Serial.println("hi");

// 	// if (currentState == WAIT)
// 	// {
// 	// 	// uid 인식
// 	// 	uid = getUID();

// 	// 	// 상태 변경
// 	// 	if (uid != "")
// 	// 	{
// 	// 		Serial.println("카드 인식 성공");
// 	// 		Serial.print("card UID : ");
// 	// 		Serial.println(uid);
			
// 	// 		canAccessUID[0] = uid;

// 	// 		lastCardCheckTime = millis();

// 	// 		currentState = CHECK;
// 	// 		changeState(CHECK);
// 	// 		lastStateChangeTime = millis();
// 	// 	}
// 	// }
// 	// // CHECK 상태에서 1초 경과 시 상태 전환
// 	// else if (currentState == CHECK && millis() - lastCardCheckTime >= cardCheckingInterval)
// 	// {
// 	// 	if (uid != "")
// 	// 	{
// 	// 		currentState = USE;
// 	// 		changeState(USE);
// 	// 		lastStateChangeTime = millis();
// 	// 		Serial.println("ENTER: " + uid);
// 	// 	}
// 	// }
// 	// else if (currentState == USE)
// 	// {

// 	// }

// 	// // UID 읽기
// 	// for (byte i = 0; i < mfrc522.uid.size; i++)
// 	// {
// 	// 	if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
// 	// 	uid += String(mfrc522.uid.uidByte[i], HEX);
// 	// }

// 	// // 상태 결정
// 	// if (isUsed && uid == uid)
// 	// {
// 	// 	// 동일 UID : 퇴장 준비
// 	// 	isUsed = false;
// 	// }
// 	// else
// 	// {
// 	// 	// 신규 UID : 입장 준비
// 	// 	isUsed = true;
// 	// }

// 	// // CHECK 상태로 전환
// 	// lastCardCheckTime = millis();
// 	// changeState(CHECK);
// 	// mfrc522.PICC_HaltA();
// 	// mfrc522.PCD_StopCrypto1();
// }

// void updateLEDs()
// {
// 	// Serial.print("isWaiting : ");
// 	// Serial.println(isWaiting);
// 	// Serial.print("isChecking : ");
// 	// Serial.println(isChecking);
// 	// Serial.print("isUsed : ");
// 	// Serial.println(isUsed);
// 	// if (isWaiting)
// 	// {
// 	// 	digitalWrite(RED_LED, LOW);
// 	// 	digitalWrite(YLW_LED, HIGH);
// 	// 	digitalWrite(GRN_LED, LOW);
// 	// }

// 	// if (isChecking)
// 	// {
// 	// 	digitalWrite(RED_LED, LOW);
// 	// 	digitalWrite(YLW_LED, LOW);
// 	// 	digitalWrite(GRN_LED, HIGH);
// 	// }

// 	// if (isUsed)
// 	// {
// 	// 	digitalWrite(RED_LED, HIGH);
// 	// 	digitalWrite(YLW_LED, LOW);
// 	// 	digitalWrite(GRN_LED, LOW);
// 	// }
// 	switch(currentState)
// 	{
// 		case WAIT:
// 			digitalWrite(RED_LED, LOW);
// 			digitalWrite(YLW_LED, HIGH);
// 			digitalWrite(GRN_LED, LOW);
// 			return;
// 		case CHECK:
// 			digitalWrite(RED_LED, LOW);
// 			digitalWrite(YLW_LED, LOW);
// 			digitalWrite(GRN_LED, HIGH);
// 			return;
// 		case USE:
// 			digitalWrite(RED_LED, HIGH);
// 			digitalWrite(YLW_LED, LOW);
// 			digitalWrite(GRN_LED, LOW);
// 			return;
// 	}
// }

// void setup() {
// 	Serial.begin(9600);		// Initialize serial communications with the PC
// 	while (!Serial);		// Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
// 	SPI.begin();			// Init SPI bus
// 	mfrc522.PCD_Init();		// Init MFRC522
// 	// delay(4);				// Optional delay. Some board do need more time after init to be ready, see Readme
// 	mfrc522.PCD_DumpVersionToSerial();	// Show details of PCD - MFRC522 Card Reader details
// 	Serial.println(F("Scan PICC to see UID, SAK, type, and data blocks..."));

// 	pinMode(RED_LED, OUTPUT);
// 	pinMode(YLW_LED, OUTPUT);
// 	pinMode(GRN_LED, OUTPUT);

// 	changeState(WAIT);
// 	Serial.println("READY");
// }

// void loop() {
// 	cardCheck();
// 	updateLEDs();
// }

//-------------------------------------------------------------------------------------------------------------------------------------------------------

// #include <SPI.h>
// #include <MFRC522.h>

// #define RST_PIN         9          // Configurable, see typical pin layout above
// #define SS_PIN          10         // Configurable, see typical pin layout above

// MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

// // LED 핀 번호 정의
// const int RED_LED = 7;
// const int YLW_LED = 5;
// const int GRN_LED = 3;

// // 개인이 소지 가능한 카드 갯수
// const int allowedUidNums = 2;

// // 현재 접근 가능한 UID 목록
// String canAccessUID[allowedUidNums] = {}; 

// // 시스템 상태를 나타내는 열거형(enum)
// enum State { WAIT, CHECK, USE };
// State beforeState = WAIT;
// State currentState = WAIT; // 현재 시스템 상태를 저장하는 변수

// // 시간 제어를 위한 변수
// unsigned long lastStateChangeTime = 0;
// const int greenLedDuration = 500; // 초록불이 켜져 있는 시간 (0.5초)

// /**
//  * @brief MFRC522에서 읽은 UID를 문자열로 변환합니다.
//  * @return 변환된 UID 문자열
//  */
// String getUID() {
//   String tempUID = "";
//   for (byte i = 0; i < mfrc522.uid.size; i++) {
//     // UID의 각 바이트가 16보다 작으면(한 자리 수이면) 앞에 '0'을 붙여줍니다.
//     if (mfrc522.uid.uidByte[i] < 0x10) {
//       tempUID += "0";
//     }
//     tempUID += String(mfrc522.uid.uidByte[i], HEX);
//   }
//   tempUID.toUpperCase(); // 가독성을 위해 대문자로 변경
//   return tempUID;
// }

// /**
//  * @brief 현재 상태(currentState)에 따라 LED를 제어합니다.
//  */
// void updateLEDs() {
//   switch (currentState) {
//     case WAIT: // 대기 상태: 노란불
//       digitalWrite(RED_LED, LOW);
//       digitalWrite(YLW_LED, HIGH);
//       digitalWrite(GRN_LED, LOW);
//       break;
//     case CHECK: // 확인 중 상태: 초록불
//       digitalWrite(RED_LED, LOW);
//       digitalWrite(YLW_LED, LOW);
//       digitalWrite(GRN_LED, HIGH);
//       break;
//     case USE: // 사용 중 상태: 빨간불
//       digitalWrite(RED_LED, HIGH);
//       digitalWrite(YLW_LED, LOW);
//       digitalWrite(GRN_LED, LOW);
//       break;
//   }
// }

// /**
//  * @brief RFID 카드를 확인하고 그에 따라 시스템 상태를 변경합니다.
//  */
// void cardCheck() {
//   switch (currentState) {
//     case WAIT:
//       // 새 카드가 있는지, 카드 정보를 읽을 수 있는지 확인
//       if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
//         String uid = getUID();
//         // Serial.println("카드 인식 성공!");
//         // Serial.print("Card UID: ");
//         // Serial.println(uid);

// 				canAccessUID[0] = uid;

// 				char cmd[2] = "EE";
// 				char send_buffer[16];
// 				memset(send_buffer, 0x00, sizeof(send_buffer));
// 				memcpy(send_buffer, cmd, 2);
// 				memset(send_buffer + 2, MFRC522::STATUS_OK, 1);
// 				memcpy(send_buffer + 3, mfrc522.uid.uidByte, 4);
// 				Serial.write(send_buffer, 7);

//         // 상태를 CHECK로 변경하고, 상태 변경 시간을 기록
// 				beforeState = currentState;
//         currentState = CHECK;
//         lastStateChangeTime = millis();
        
//         // 카드 읽기 중단을 위해 PICC를 정지시킵니다.
//         mfrc522.PICC_HaltA(); 
//         mfrc522.PCD_StopCrypto1();
//       }
//       break;

//     case CHECK:
//       // 초록불이 켜진 후 설정된 시간이 지나면 USE 상태로 변경
//       if (beforeState == WAIT && millis() - lastStateChangeTime >= greenLedDuration) {
//         // Serial.println("사용 중 상태로 전환합니다.");
//         currentState = USE;
//         lastStateChangeTime = millis();
//       }
// 			if (beforeState == USE && millis() - lastStateChangeTime >= greenLedDuration) {
//         // Serial.println("대기 중 상태로 전환합니다.");
//         currentState = WAIT;
//         lastStateChangeTime = millis();
//       }
//       break;

//     case USE:
//       // 사용 중(빨간불) 상태에서 다시 카드를 태그하면 대기 상태(노란불)로 돌아갑니다.
//       // 이렇게 하면 입실/퇴실 토글 기능이 완성됩니다.
//       if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
//         String uid = getUID();

// 				for (String tempUid : canAccessUID)
// 				{
// 					if (tempUid == uid)
// 					{
// 						// Serial.println("퇴실 처리. 대기 상태로 돌아갑니다.");
// 						// Serial.print("Card UID: ");
// 						// Serial.println(uid);

// 						canAccessUID[0] = "";
						
// 						// 상태를 WAIT로 변경하고, 상태 변경 시간을 기록
// 						beforeState = currentState;
// 						currentState = CHECK;
// 						lastStateChangeTime = millis();
// 						break;
// 					}
// 				}

// 				// Serial.println("다른 사용자가 사용중 입니다.");
//         // // 상태를 WAIT로 변경하고, 상태 변경 시간을 기록
// 				// beforeState = currentState;
//         // currentState = CHECK;
//         // lastStateChangeTime = millis();
        
//         // 카드 읽기 중단을 위해 PICC를 정지시킵니다.
//         mfrc522.PICC_HaltA(); 
//         mfrc522.PCD_StopCrypto1();
//       }
//       break;
//   }
// }

// void setup() {
//   Serial.begin(9600);   // PC와 시리얼 통신 시작 (보드레이트: 9600)
//   while (!Serial);      // 시리얼 포트가 열릴 때까지 대기

//   // *** 중요 ***
//   // SPI 버스와 MFRC522 모듈 초기화는 setup()에서 한 번만 실행해야 합니다.
//   SPI.begin();          // SPI 버스 초기화
//   mfrc522.PCD_Init();   // MFRC522 모듈 초기화

//   // LED 핀을 출력 모드로 설정
//   pinMode(RED_LED, OUTPUT);
//   pinMode(YLW_LED, OUTPUT);
//   pinMode(GRN_LED, OUTPUT);

//   Serial.println("시스템 준비 완료. 대기 상태입니다.");
// }

// void loop() {
//   cardCheck();
//   updateLEDs();
// }
//-------------------------------------------------------------------------------------------------------------------------------------------------------

#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN         9          // Configurable, see typical pin layout above
#define SS_PIN          10         // Configurable, see typical pin layout above

MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

/*
아두이노(컴파일러)는 메모리 효율을 위해 구조체 멤버 사이에 보이지 않는 빈 공간(패딩, padding)을 추가할 수 있습니다. 이 경우 구조체의 전체 크기가 우리가 의도한 12바이트가 아니라 13, 14바이트 등으로 늘어날 수 있어 통신 오류의 원인이 됩니다.
#pragma pack(1)는 컴파일러에게 "패딩을 추가하지 말고 1바이트 단위로 데이터를 꽉 채워서 구조체를 만들어라"라고 지시하는 명령어입니다. 통신용 구조체를 정의할 때는 거의 항상 사용한다고 보시면 됩니다.
*/
// 패킷 구조 정의
#pragma pack(push, 1)
struct DataPacket
{
  char header[2];
  byte status;
  byte data[8];
  char terminator;
};
#pragma pack(pop)

DataPacket rx_packet;  // 수신용
DataPacket tx_packet;  // 송신용
bool newDataAvailable = false;

// LED 핀 번호 정의
const int RED_LED = 7;
const int YLW_LED = 5;
const int GRN_LED = 3;

// 개인이 소지 가능한 카드 갯수
const int allowedUidNums = 2;

// 현재 접근 가능한 UID 목록
long authorizedUIDs[allowedUidNums] = {0,0}; 

// 시스템 상태를 나타내는 열거형(enum)
enum State { WAIT, CHECK, USE, REGISTER, OUT};
State beforeState = WAIT;
State currentState = WAIT; // 현재 시스템 상태를 저장하는 변수

// 시간 제어를 위한 변수
unsigned long lastStateChangeTime = 0;
const int greenLedDuration = 500; // 초록불이 켜져 있는 시간 (0.5초)

// LED 깜빡임을 위한 변수
unsigned long lastBlinkTime = 0;
bool yellowLedState = false;
bool redLedState = false;

bool canCheck = true;

/**
 * @brief MFRC522에서 읽은 UID를 문자열로 변환합니다.
 * @return 변환된 UID 문자열
 */
String getUID() {
  String tempUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    // UID의 각 바이트가 16보다 작으면(한 자리 수이면) 앞에 '0'을 붙여줍니다.
    if (mfrc522.uid.uidByte[i] < 0x10) {
      tempUID += "0";
    }
    tempUID += String(mfrc522.uid.uidByte[i], HEX);
  }
  tempUID.toUpperCase(); // 가독성을 위해 대문자로 변경
  return tempUID;
}

/**
 * @brief 지정된 내용으로 데이터 패킷을 구성하여 PC로 전송합니다.
 * @param header 패킷 헤더 (2글자 문자열 포인터. 예: "IA")
 * @param status 상태 코드 (1바이트)
 * @param data 전송할 데이터 (long 타입, 4바이트).
               UID 같이 바이트 배열인 경우 long으로 변환 후 전달해야 합니다.
 */
void sendPacket(const char* header, byte status, long long data)
{
  // 1. tx_packet (송신용 패킷) 내용 채우기
  strncpy(tx_packet.header, header, 2);
  tx_packet.status = status;

  // 2. 데이터 필드(8바이트)를 0으로 초기화
  memset(tx_packet.data, 0, sizeof(tx_packet.data));

  // 3. 4바이트 long 데이터를 데이터 필드 앞부분에 복사
  memcpy(tx_packet.data, &data, sizeof(data));

  // 4. 종료 문자 설정
  tx_packet.terminator = '\n';

  // 5. 시리얼 포트로 12바이트 패킷 전송
  Serial.write((byte*)&tx_packet, sizeof(tx_packet));
}

/**
 * @brief 현재 상태(currentState)에 따라 LED를 제어합니다.
 */
void updateLEDs() {
  switch (currentState) {
    case WAIT: // 대기 상태: 노란불
      digitalWrite(RED_LED, LOW);
      digitalWrite(YLW_LED, HIGH);
      digitalWrite(GRN_LED, LOW);
      break;
    case CHECK: // 확인 중 상태: 초록불
      digitalWrite(RED_LED, LOW);
      digitalWrite(YLW_LED, LOW);
      digitalWrite(GRN_LED, HIGH);
      break;
    case USE: // 사용 중 상태: 빨간불
      digitalWrite(RED_LED, HIGH);
      digitalWrite(YLW_LED, LOW);
      digitalWrite(GRN_LED, LOW);
      break;
    case REGISTER:
      digitalWrite(RED_LED, LOW);
      if (millis() - lastBlinkTime > 500)
      {
        lastBlinkTime = millis();
        yellowLedState = !yellowLedState;
        digitalWrite(YLW_LED, yellowLedState);
      }
      digitalWrite(GRN_LED, LOW);
    case OUT:
      if(millis() - lastBlinkTime > 500)
      {
        lastBlinkTime = millis();
        redLedState = !redLedState;
        digitalWrite(RED_LED, redLedState);
      }
      digitalWrite(YLW_LED, LOW);
      digitalWrite(GRN_LED, LOW);
  }
}

/**
 * @brief RFID 카드를 확인하고 그에 따라 시스템 상태를 변경합니다.
 */
void checkCard() {

  // 현재 카드인식 가능상태 확인
  if (!cardCheck) return;

  // 새 카드가 있는지 먼저 확인
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) return;

  long uidToSend = 0;
  memcpy(&uidToSend, mfrc522.uid.uidByte, 4);

  switch (currentState) 
  {
    case REGISTER:
      sendPacket("IR", 0x00, uidToSend);
      break;
    case WAIT:
      sendPacket("IA", 0x00, uidToSend);

      // 상태를 CHECK로 변경하고, 상태 변경 시간을 기록
      beforeState = currentState;
      currentState = CHECK;
      lastStateChangeTime = millis();
      break;

    case CHECK:
      break;

    case USE:      
      break;

    case OUT:
      String uid = getUID();
      bool isSame = false;

      // long값을 byte로 변환
      String hexString = "";

      // long 타입 변수를 1바이트씩 접근하기 위한 byte 포인터
      byte* ptr = (byte*)&authorizedUIDs[0];

      // 4바이트를 순회하며 문자열로 변환 (리틀 엔디안 순서 그대로)
      for (int i = 0; i < sizeof(authorizedUIDs[0]); i++) {
        byte currentByte = ptr[i];

        // 현재 바이트가 16(0x10)보다 작으면 앞에 "0"을 붙여 두 자리로 만듭니다.
        if (currentByte < 0x10) {
          hexString += "0";
        }
        
        // 현재 바이트를 16진수 문자열로 변환하여 뒤에 이어 붙입니다.
        hexString += String(currentByte, HEX);
      }

      long long sendData = 0;
      memcpy((byte*)&sendData, mfrc522.uid.uidByte, 4);
      memcpy((byte*)&sendData + 4, ptr, 4);

      if (String(hexString).equalsIgnoreCase(uid))
      {
        isSame = true;
      }

      if (isSame)
      {
        sendPacket("IZ", 0x00, sendData);
      }
      else
      {

        sendPacket("IG", 0x00, sendData);
      }

      currentState = WAIT;
      break;
  }

  // 카드 읽기 중단을 위한 정지
  mfrc522.PICC_HaltA(); 
  mfrc522.PCD_StopCrypto1();
}

void checkSerial()
{
  // --- 1. 더 안정적인 수신 방식으로 변경 ---
  // 패킷 크기(12바이트)만큼 데이터가 들어왔는지 먼저 확인
  if (Serial.available() >= sizeof(DataPacket)) {
    // 한 번에 12바이트를 읽어옵니다.
    Serial.readBytes((char*)&rx_packet, sizeof(DataPacket));
    
    // 종료 문자가 맞는지 확인하여 패킷의 유효성을 검사
    if (rx_packet.terminator == '\n') {
      newDataAvailable = true;
    }
  }
}

void processCommand()
{
  if (!newDataAvailable) return;

  // command가 IA일 경우
  if (strncmp(rx_packet.header, "IB", 2) == 0)
  {
    if(currentState == CHECK)
    {
      if(rx_packet.status == 0x00)
      {
        memcpy(&authorizedUIDs[0], rx_packet.data, 4);
        memcpy(&authorizedUIDs[1], rx_packet.data + 4, 4);

        currentState = USE;
        lastStateChangeTime = millis();
      }
      else if (rx_packet.status == 0xA1)
      {
        currentState = WAIT;
        lastStateChangeTime = millis();
      }
    }
  }
  else if (strncmp(rx_packet.header, "IS", 2) == 0)
  {
    currentState = REGISTER;
  }
  else if (strncmp(rx_packet.header, "IE", 2) == 0)
  {
    // currentState = WAIT;
    // sendPacket("IE", 0x00, 0);
    // currentState = ACK_SENT;
    lastStateChangeTime = millis(); // 상태 변경 시간 기록
    sendPacket("IE", 0x00, 0);
  }
  else if (strncmp(rx_packet.header, "IY", 2) == 0)
  {
    currentState = OUT;
  }

  newDataAvailable = false;
}

void setup() {
  Serial.begin(9600);   // PC와 시리얼 통신 시작 (보드레이트: 9600)
  // while (!Serial);      // 시리얼 포트가 열릴 때까지 대기

  // *** 중요 ***
  // SPI 버스와 MFRC522 모듈 초기화는 setup()에서 한 번만 실행해야 합니다.
  SPI.begin();          // SPI 버스 초기화
  mfrc522.PCD_Init();   // MFRC522 모듈 초기화

  // // LED 핀을 출력 모드로 설정
  pinMode(RED_LED, OUTPUT);
  pinMode(YLW_LED, OUTPUT);
  pinMode(GRN_LED, OUTPUT);

  Serial.println("시스템 준비 완료. 대기 상태입니다.");
}

void loop() {
  checkSerial();
  processCommand();
  checkCard();
  updateLEDs();
}
