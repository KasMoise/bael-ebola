# early_warning_system.py

import smtplib
import requests
from twilio.rest import Client

class EarlyWarningSystem:
    def __init__(self):
        self.thresholds = {
            "critical": 50, # Cas quotidiens > 50
            "high": 25,
            "moderate": 10
        }
        self.alert_channels = {
            "sms": self.send_sms_alert,
            "email": self.send_email_alert,
            "radio": self.broadcast_radio_alert,
            "whatsapp": self.send_whatsapp_alert
        }
    
    def check_and_alert(self, zone_data):
        """Vérifie les données et envoie des alertes si nécessaire"""
        for zone, data in zone_data.items():
            risk_level = self.assess_risk(data)
            
            if risk_level in ["critical", "high"]:
                alert = self.generate_alert(zone, data, risk_level)
                self.send_alerts(alert)
                self.log_alert(alert)
    
    def generate_alert(self, zone, data, risk_level):
        return {
            "zone": zone,
            "level": risk_level,
            "cases": data["new_cases"],
            "growth_rate": data["growth_rate"],
            "message": self.get_alert_message(risk_level),
            "recommendations": self.get_recommendations(risk_level),
            "timestamp": datetime.now().isoformat()
        }
    
    def send_alerts(self, alert):
        """Envoie les alertes via tous les canaux disponibles"""
        channels = self.get_channels_for_zone(alert["zone"])
        
        for channel in channels:
            if channel in self.alert_channels:
                self.alert_channels[channel](alert)