#include <ArduinoBLE.h>
#include <Wire.h>
#include <Adafruit_RGBLCDShield.h>
#include <utility/Adafruit_MCP23017.h>

// Initialisation de l'écran LCD
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();

// Définition des codes couleur pour le rétroéclairage LCD
#define RED 0x1      // Rouge - utilisé pour les alertes
#define YELLOW 0x3   // Jaune - utilisé pour les avertissements
#define GREEN 0x2    // Vert - utilisé pour les statuts positifs
#define TEAL 0x6     // Bleu-vert
#define BLUE 0x4     // Bleu - utilisé pour les informations
#define VIOLET 0x5   // Violet
#define WHITE 0x7    // Blanc - couleur par défaut
// Note: 0x0 correspond à pas de rétroéclairage (éteint)

// Création du service BLE
BLEService newService("180A"); 

// Caractéristiques BLE
BLEUnsignedCharCharacteristic randomReading("2A58", BLERead | BLENotify); // Pour envoyer une valeur aléatoire
BLEStringCharacteristic lcdTextChar("2A3D", BLERead | BLEWrite, 32);      // Pour recevoir le texte à afficher (max 32 caractères)
BLEByteCharacteristic lcdColorChar("2A3E", BLERead | BLEWrite);           // Pour recevoir la couleur de l'écran LCD

// Variables globales
long previousMillis = 0;  // Pour le timing des mises à jour

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Initialisation de l'écran LCD
  lcd.begin(16, 2);       // Format 16 caractères sur 2 lignes
  lcd.setBacklight(WHITE); // Couleur de démarrage: blanc
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("BLE LCD Shield");
  lcd.setCursor(0, 1);
  lcd.print("En attente...");

  // LED intégrée pour indiquer l'état de connexion BLE
  pinMode(LED_BUILTIN, OUTPUT);

  // Initialisation du BLE
  if (!BLE.begin()) {
    Serial.println("L'initialisation du Bluetooth Low Energy a échoué!");
    lcd.clear();
    lcd.print("BLE error");
    while (1); // Arrêt du programme en cas d'échec
  }

  // Configuration du périphérique BLE
  BLE.setLocalName("LCD Shield BLE");
  BLE.setAdvertisedService(newService);

  // Ajout des caractéristiques au service
  newService.addCharacteristic(randomReading);
  newService.addCharacteristic(lcdTextChar);     // Pour le texte à afficher
  newService.addCharacteristic(lcdColorChar);    // Pour la couleur du LCD

  BLE.addService(newService);

  // Initialisation des valeurs des caractéristiques
  randomReading.writeValue(0);
  lcdTextChar.writeValue("Bonjour!");
  lcdColorChar.writeValue(WHITE);   // Couleur initiale: blanc

  // Démarrage de la publicité BLE
  BLE.advertise();
  Serial.println("Périphérique Bluetooth actif, en attente de connexions...");
}

void loop() {
  // Attendre une connexion centrale BLE
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connecté à : ");
    Serial.println(central.address());
    
    digitalWrite(LED_BUILTIN, HIGH);  // Allumer la LED intégrée pour indiquer la connexion
    
    // Afficher l'adresse de l'appareil connecté
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Connecte a:");
    lcd.setCursor(0, 1);
    lcd.print(central.address());
    
    // Boucle principale pendant la connexion
    while (central.connected()) {
      long currentMillis = millis();
      
      // Mise à jour toutes les 200ms
      if (currentMillis - previousMillis >= 200) {
        previousMillis = currentMillis;
        
        // Lecture et envoi d'une valeur analogique aléatoire
        int randomValue = analogRead(A1);
        randomReading.writeValue(randomValue);
        
        // Gestion du texte pour l'écran LCD
        if (lcdTextChar.written()) {
          String text = lcdTextChar.value();
          Serial.print("Nouveau texte reçu: ");
          Serial.println(text);
          
          lcd.clear();
          
          // Répartition du texte sur les deux lignes si nécessaire
          if (text.length() <= 16) {
            // Texte court: une seule ligne
            lcd.setCursor(0, 0);
            lcd.print(text);
          } else {
            // Texte long: deux lignes
            lcd.setCursor(0, 0);
            lcd.print(text.substring(0, 16));  // Premiers 16 caractères
            lcd.setCursor(0, 1);
            lcd.print(text.substring(16, min(32, text.length()))); // Caractères restants
          }
        }
        
        // Gestion de la couleur du rétroéclairage LCD
        if (lcdColorChar.written()) {
          byte color = lcdColorChar.value();
          color = color % 8;  // Assure une valeur entre 0 et 7
          lcd.setBacklight(color);
          
          // Affichage dans le moniteur série de la couleur sélectionnée
          Serial.print("Couleur de fond: ");
          switch(color) {
            case 0: Serial.println("Éteint"); break;
            case RED: Serial.println("Rouge"); break;
            case YELLOW: Serial.println("Jaune"); break;
            case GREEN: Serial.println("Vert"); break;
            case TEAL: Serial.println("Bleu-vert"); break;
            case BLUE: Serial.println("Bleu"); break;
            case VIOLET: Serial.println("Violet"); break;
            case WHITE: Serial.println("Blanc"); break;
            default: Serial.println("Inconnu"); break;
          }
        }
      }
    }
    
    digitalWrite(LED_BUILTIN, LOW);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("BLE LCD Shield");
    lcd.setCursor(0, 1);
    lcd.print("En attente...");
    
    Serial.print("Déconnecté de : ");
    Serial.println(central.address());
  }
}