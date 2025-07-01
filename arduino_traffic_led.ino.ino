// Define LED pins
const int redLED = 2;
const int yellowLED = 3;
const int greenLED = 4;

void setup() {
  Serial.begin(9600);
  pinMode(redLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  
  // Turn all LEDs off at start
  digitalWrite(redLED, LOW);
  digitalWrite(yellowLED, LOW);
  digitalWrite(greenLED, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    // Debug print
    Serial.print("Received: ");
    Serial.println(command);

    switch (command) {
      case 'R':
        digitalWrite(redLED, HIGH);
        digitalWrite(yellowLED, LOW);
        digitalWrite(greenLED, LOW);
        break;
      case 'Y':
        digitalWrite(redLED, LOW);
        digitalWrite(yellowLED, HIGH);
        digitalWrite(greenLED, LOW);
        break;
      case 'G':
        digitalWrite(redLED, LOW);
        digitalWrite(yellowLED, LOW);
        digitalWrite(greenLED, HIGH);
        break;
      case '0':
        digitalWrite(redLED, LOW);
        digitalWrite(yellowLED, LOW);
        digitalWrite(greenLED, LOW);
        break;
      default:
        // Unknown command
        break;
    }
  }
}
