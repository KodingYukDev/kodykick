// KodyKick robot — ESP32 DevKit V1 (WROOM-32). Arduino-ESP32 core 3.x.
// Kendali: (1) KodyPad via ESP-NOW (default), (2) stik PS3/PS4/8BitDo via Bluepad32 (#define USE_BLUEPAD32,
// pilih board "ESP32 Dev Module" dari paket Bluepad32: https://bluepad32.readthedocs.io/en/latest/plat_arduino/),
// (3) fallback web joystick di AP "KodyKick-xx" (belum diimplementasi, lihat docs/RISET-REMOTE.md opsi D).
//
// Pin: DRV8833 AIN1=25 AIN2=26 (motor kiri), BIN1=27 BIN2=14 (motor kanan); servo kicker=13; buzzer=15;
//      LED mata=4 (2 LED paralel + 220R); LED onboard=2. Catu: 4xAA 6 V -> VIN ESP32 + VM DRV8833 + servo.
#include <Arduino.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <esp_now.h>

#define USE_BLUEPAD32   // default: stik PS3/PS4 (keputusan Owner 9 Nov 2026). ESP-NOW tetap ada untuk pad lama.
#ifdef USE_BLUEPAD32
#include <Bluepad32.h>
#endif

const int AIN1 = 25, AIN2 = 26, BIN1 = 27, BIN2 = 14, SERVO = 13, BUZZ = 15, EYES = 4, LED = 2;
const int KICK_REST = 20, KICK_HIT = 95;  // derajat servo
const uint32_t FAILSAFE_MS = 400;          // tanpa paket -> berhenti

struct __attribute__((packed)) PadPacket {
  uint8_t magic;   // 0xK1 = 0x4B
  int8_t x;        // -100..100 (kiri/kanan)
  int8_t y;        // -100..100 (maju/mundur)
  uint8_t btn;     // bit0 TENDANG, bit1 TURBO, bit2 KLAKSON, bit3 PAIR
};

Servo kicker;
volatile PadPacket last{};
volatile uint32_t lastMs = 0;
uint8_t padMac[6] = {0};
bool paired = false;

void drive(int left, int right) {  // -255..255
  auto ch = [](int v, int p1, int p2) {
    v = constrain(v, -255, 255);
    analogWrite(p1, v > 0 ? v : 0);
    analogWrite(p2, v < 0 ? -v : 0);
  };
  ch(left, AIN1, AIN2);
  ch(right, BIN1, BIN2);
}

void kick() {
  kicker.write(KICK_HIT);
  tone(BUZZ, 1200, 80);
  delay(140);
  kicker.write(KICK_REST);
}

void applyPacket(const PadPacket &p) {
  int maxPwm = (p.btn & 0x02) ? 255 : 180;                 // TURBO
  int fwd = map(p.y, -100, 100, -maxPwm, maxPwm);
  int turn = map(p.x, -100, 100, -maxPwm, maxPwm) * 0.8;   // arcade drive
  drive(fwd + turn, fwd - turn);
  static bool kickLatch = false;
  if ((p.btn & 0x01) && !kickLatch) kick();
  kickLatch = p.btn & 0x01;
  if (p.btn & 0x04) tone(BUZZ, 900, 60);
}

void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != sizeof(PadPacket) || data[0] != 0x4B) return;
  PadPacket p;
  memcpy(&p, data, sizeof(p));
  if (!paired) {                       // PAIR: paket pertama dengan bit PAIR mengunci MAC pad ini
    if (!(p.btn & 0x08)) return;
    memcpy(padMac, info->src_addr, 6);
    paired = true;
    tone(BUZZ, 1500, 100);
    digitalWrite(LED, HIGH);
  } else if (memcmp(padMac, info->src_addr, 6) != 0) {
    return;                            // paket dari pad lain diabaikan (multi-robot di satu arena)
  }
  memcpy((void *)&last, &p, sizeof(p));
  lastMs = millis();
}

#ifdef USE_BLUEPAD32
ControllerPtr pads[BP32_MAX_GAMEPADS];
void onConnected(ControllerPtr c) { for (auto &s : pads) if (!s) { s = c; tone(BUZZ, 1500, 100); break; } }
void onDisconnected(ControllerPtr c) { for (auto &s : pads) if (s == c) s = nullptr; drive(0, 0); }
void pollBluepad() {
  if (!BP32.update()) return;
  for (auto c : pads) {
    if (!c || !c->isConnected() || !c->isGamepad()) continue;
    PadPacket p{0x4B, (int8_t)map(c->axisX(), -512, 511, -100, 100), (int8_t)map(-c->axisY(), -512, 511, -100, 100), 0};
    if (c->a() || c->r1()) p.btn |= 0x01;   // X/A = tendang
    if (c->r2() > 100) p.btn |= 0x02;      // R2 = turbo
    if (c->b()) p.btn |= 0x04;             // O/B = klakson
    applyPacket(p);
    lastMs = millis();
  }
}
#endif

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT); pinMode(EYES, OUTPUT); pinMode(BUZZ, OUTPUT);
  for (int p : {AIN1, AIN2, BIN1, BIN2}) pinMode(p, OUTPUT);
  analogWriteFrequency(20000);  // PWM 20 kHz, tidak berdengung
  kicker.attach(SERVO, 500, 2400);
  kicker.write(KICK_REST);
  digitalWrite(EYES, HIGH);

  WiFi.mode(WIFI_STA);
  Serial.printf("KodyKick MAC %s\n", WiFi.macAddress().c_str());
  if (esp_now_init() == ESP_OK) esp_now_register_recv_cb(onRecv);
#ifdef USE_BLUEPAD32
  BP32.setup(&onConnected, &onDisconnected);
  BP32.forgetBluetoothKeys();
#endif
  tone(BUZZ, 880, 80); delay(100); tone(BUZZ, 1320, 80);
}

void loop() {
#ifdef USE_BLUEPAD32
  pollBluepad();
#endif
  if (millis() - lastMs > FAILSAFE_MS) {
    drive(0, 0);
    digitalWrite(LED, (millis() / 300) % 2);  // kedip = menunggu pad
  } else {
    PadPacket p;
    memcpy(&p, (const void *)&last, sizeof(p));
    applyPacket(p);
  }
  delay(10);
}
