// KodyPad — remote DIY KodyKick. ESP32-C3 Super Mini, ESP-NOW broadcast saat PAIR lalu unicast ke robot.
// Pin C3 Super Mini: joystick X=GPIO0 (ADC), Y=GPIO1 (ADC), tekan joystick (PAIR)=GPIO2;
//                    TENDANG=GPIO3, TURBO=GPIO4, KLAKSON=GPIO5 (semua ke GND, INPUT_PULLUP); LED onboard=GPIO8 (aktif LOW).
// Catu: 3xAAA 4,5 V -> pin 5V (LDO 3,3 V on-board). Kirim 50 paket/detik.
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>

const int JX = 0, JY = 1, JSW = 2, BKICK = 3, BTURBO = 4, BHORN = 5, LED = 8;
const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

struct __attribute__((packed)) PadPacket { uint8_t magic; int8_t x; int8_t y; uint8_t btn; };

uint8_t robotMac[6];
bool paired = false;
int cx = 2048, cy = 2048;  // kalibrasi tengah saat nyala

int8_t axis(int raw, int center) {
  int v = map(raw, 0, 4095, -100, 100) - map(center, 0, 4095, -100, 100);
  if (abs(v) < 8) v = 0;          // deadzone
  return constrain(v, -100, 100);
}

void addPeer(const uint8_t *mac) {
  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, mac, 6);
  peer.channel = 0;
  peer.encrypt = false;
  if (!esp_now_is_peer_exist(mac)) esp_now_add_peer(&peer);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  for (int p : {JSW, BKICK, BTURBO, BHORN}) pinMode(p, INPUT_PULLUP);
  analogReadResolution(12);
  delay(200);
  cx = analogRead(JX); cy = analogRead(JY);
  WiFi.mode(WIFI_STA);
  esp_now_init();
  addPeer(BROADCAST);
  Serial.printf("KodyPad MAC %s\n", WiFi.macAddress().c_str());
}

void loop() {
  PadPacket p{0x4B, axis(analogRead(JX), cx), (int8_t)-axis(analogRead(JY), cy), 0};
  if (!digitalRead(BKICK)) p.btn |= 0x01;
  if (!digitalRead(BTURBO)) p.btn |= 0x02;
  if (!digitalRead(BHORN)) p.btn |= 0x04;
  bool pairBtn = !digitalRead(JSW);
  if (pairBtn) { p.btn |= 0x08; paired = false; }   // tekan joystick = cari robot baru (broadcast)

  // Robot yang menerima paket PAIR akan mengunci MAC pad; pad mengirim broadcast sampai tombol PAIR dilepas,
  // lalu terus broadcast (robot lain mengabaikan karena sudah terkunci ke pad masing-masing).
  esp_now_send(BROADCAST, (uint8_t *)&p, sizeof(p));
  digitalWrite(LED, pairBtn ? (millis() / 100) % 2 : LOW);  // LED nyala (aktif LOW) saat kirim, kedip saat PAIR
  delay(20);
}
