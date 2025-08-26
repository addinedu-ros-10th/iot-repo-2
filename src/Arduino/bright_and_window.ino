#include <Servo.h>

Servo servo_1;
Servo servo_2;

const int LED_R = 3;
const int LED_G = 5;
const int LED_B = 6;
const int SERVO_PIN_1 = 14;
const int SERVO_PIN_2 = 15;

const int LIGHT_SENSOR = 16;

int light_control_period_count = 50;
int servo_control_period_count = 10;

int led_light_previous = 0;
int led_light_desired = 0;
int led_light_desired_mapped;
int led_light_actual = 0;

const int window_conditioning_time_default = 2000;
int window_conditioning_time = window_conditioning_time_default;

int window_conditioning_angle = 0;
int window_conditioning_open_angle = 40;
int window_conditioning_close_angle = 0;

bool is_window_conditioning_mode = false;
bool is_window_conditioning_open = false;

void serialLoop()
{
  while (Serial.available() > 0)
  {
    Serial.setTimeout(10);
    String string_recv = Serial.readStringUntil("\n");

    int length = string_recv.length();

    switch(string_recv[0])
    {
      case 'w':
      {
        int length = string_recv.length();

        if (string_recv[1] == 'a')
        {
          String servo_order = string_recv.substring(2, length);
        
          int blind_angle_desired = servo_order.toInt();
          controlBlind(blind_angle_desired);
        }
        else if (string_recv[1] == 'b')
        {
          if (is_window_conditioning_mode == true)
          {
            is_window_conditioning_mode = false;
            is_window_conditioning_open = false;
            window_conditioning_time = window_conditioning_time_default;
          }

          String servo_order = string_recv.substring(2, length);
      
          int window_angle_desired = servo_order.toInt();
          controlWindow(window_angle_desired);
        }
        else if (string_recv[1] == 'c')
        {
          is_window_conditioning_mode = true;
        }
        break;
      }
      case 'l':
      {
        int length = string_recv.length();

        if (string_recv[1] == 'a')
        {
          String led_order = string_recv.substring(2, length);

          led_light_desired = led_order.toInt();
          led_light_desired_mapped = map(led_light_desired, 0, 100, 0, 255);
        }
        break;
      }
      default:
      {
        break;
      }
    }

    delay(20);
  }
}

void controlLED1()
{
  int led_light;

  if (led_light_desired_mapped > led_light_actual)
  {
    led_light = led_light_actual + 1;
  }
  else if (led_light_desired_mapped < led_light_actual)
  {
    led_light = led_light_actual - 1;
  }

  analogWrite(LED_R, led_light);
  analogWrite(LED_G, led_light);
  analogWrite(LED_B, led_light);

  led_light_actual = led_light;
}

void controlBlind(int angle)
{
  if (angle > 90) {}
  else
  {
    servo_1.write(angle);
  }
}

void controlWindow(int angle)
{
  if (angle > 90) {}
  else
  {
    if (is_window_conditioning_mode == true)
    {
      if (is_window_conditioning_open == false)
      {
        if (window_conditioning_angle < angle)
        {
          window_conditioning_angle++;
          servo_2.write(window_conditioning_angle);
        }
        else if (window_conditioning_angle > angle)
        {
          window_conditioning_angle--;
          servo_2.write(window_conditioning_angle);
        }
        else
        {
          is_window_conditioning_open = true;
          window_conditioning_time = 0;
        }
      }
      else
      {
        if (window_conditioning_angle > angle)
        {
          window_conditioning_angle--;
          servo_2.write(window_conditioning_angle);
        }
        else
        {
          is_window_conditioning_open = false;
          window_conditioning_time = 0;
        }
      }
    }
    else
    {
      servo_2.write(angle);
      window_conditioning_angle = angle;
    }
  }
}

void controlWindowConditioning()
{
  if (is_window_conditioning_open == false)
  {
    if (window_conditioning_time > 2000)
    {
      controlWindow(window_conditioning_open_angle);
    }
    else
    {
      window_conditioning_time++;
    }
  }
  else
  {
    if (window_conditioning_time > 500)
    {
      controlWindow(window_conditioning_close_angle);
    }
    else
    {
      window_conditioning_time++;
    }
  }
  /*if (is_window_conditioning_open == false)
  {
    if (window_conditioning_time > 2000)
    {
      controlWindow(window_conditioning_open_angle);
    }
    else
    {
      window_conditioning_time++;
    }
  }
  else
  {
    if (window_conditioning_time > 500)
    {
      controlWindow(window_conditioning_close_angle);
    }
    else
    {
      window_conditioning_time++;
    }
  }*/
  
}

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  servo_1.attach(SERVO_PIN_1);
  servo_2.attach(SERVO_PIN_2);

  servo_1.write(0);
  servo_2.write(0);

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LIGHT_SENSOR, INPUT);

  analogWrite(LED_R, led_light_actual);
  analogWrite(LED_G, led_light_actual);
  analogWrite(LED_B, led_light_actual);
}

void loop() {
  // put your main code here, to run repeatedly:

  serialLoop();

  if (light_control_period_count > 1)
  {
    light_control_period_count--;
  }
  else
  {
    controlLED1();
  }

  if (is_window_conditioning_mode == true)
    {
      controlWindowConditioning();
    }

  delay(10);
}
